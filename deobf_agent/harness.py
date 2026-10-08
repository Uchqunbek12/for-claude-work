"""Differensial test: ikki funksiya bir xil ishlaydimi?

G'oya: original (obfuskatsiyalangan) funksiya va LLM yaratgan soddalashtirilgan
funksiyani BIR XIL tasodifiy kirish qiymatlari bilan minglab marta chaqiramiz va
natijalarni solishtiramiz. Agar hech bir holatda farq chiqmasa — funksiyalar
amalda ekvivalent deb hisoblaymiz (bu matematik isbot emas, lekin kuchli dalil).

Cheklov: faqat parametrlari va qaytish qiymati butun son (int, unsigned, _DWORD,
undefined4 ...) bo'lgan funksiyalarni avtomatik sinash mumkin. Ko'rsatkichli
(pointer) funksiyalar uchun test "o'tkazib yuborildi" deb belgilanadi.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from . import compiler

# Butun son turlarini tashkil qiluvchi so'zlar (C, IDA, Ghidra uslublari).
INTEGER_WORDS = {
    "char", "short", "int", "long", "signed", "unsigned", "const", "volatile",
    "__int8", "__int16", "__int32", "__int64",
    "_BYTE", "_WORD", "_DWORD", "_QWORD", "_BOOL1", "_BOOL2", "_BOOL4", "_BOOL8",
    "int8_t", "int16_t", "int32_t", "int64_t", "uint8_t", "uint16_t", "uint32_t", "uint64_t",
    "size_t", "ssize_t", "uintptr_t", "intptr_t",
    "undefined", "undefined1", "undefined2", "undefined4", "undefined8",
    "byte", "word", "dword", "qword", "uchar", "ushort", "uint", "ulong",
    "longlong", "ulonglong", "bool", "_Bool", "BOOL", "DWORD", "WORD", "BYTE",
}

SYMBOL_A = "deobf_fn_original"
SYMBOL_B = "deobf_fn_candidate"


@dataclass
class DiffResult:
    status: str          # "equivalent" | "mismatch" | "inconclusive" | "skipped"
    tests: int = 0
    mismatches: int = 0
    details: str = ""

    @property
    def label_uz(self) -> str:
        return {
            "equivalent": "Ekvivalent (barcha testlar mos keldi)",
            "mismatch": "Farq topildi",
            "inconclusive": "Aniqlab bo'lmadi",
            "skipped": "O'tkazib yuborildi",
        }.get(self.status, self.status)


def is_integer_type(type_str: str) -> bool:
    """'unsigned int', '__int64', 'undefined4' kabi turlar butun sonmi?"""
    if "*" in type_str or "[" in type_str:
        return False
    words = [w for w in re.split(r"\s+", type_str.strip()) if w]
    return bool(words) and all(w in INTEGER_WORDS for w in words)


def build_harness_source(ret_type: str, param_types: list[str], n_tests: int, seed: int = 12345) -> str:
    """Ikki funksiyani taqqoslovchi main() funksiyali C dasturini yaratadi."""
    params_decl = ", ".join(param_types) if param_types else "void"
    arg_names = [f"p{i}" for i in range(len(param_types))]
    lines = [
        "#include <stdio.h>",
        "#include <stdint.h>",
        f"{ret_type} {SYMBOL_A}({params_decl});",
        f"{ret_type} {SYMBOL_B}({params_decl});",
        "",
        f"static uint64_t rng_state = {seed}ull ^ 0x9E3779B97F4A7C15ull;",
        "static uint64_t rnd64(void) {",
        "    rng_state ^= rng_state << 13; rng_state ^= rng_state >> 7; rng_state ^= rng_state << 17;",
        "    return rng_state;",
        "}",
        "/* Chegaraviy qiymatlar xatolarni ko'proq ochadi, shuning uchun ularni ham sinaymiz. */",
        "static const uint64_t EDGES[] = {0, 1, 2, 3, 7, 8, 15, 16, 31, 32, 0x7F, 0x80, 0xFF, 0x100,",
        "    0x7FFF, 0x8000, 0xFFFF, 0x7FFFFFFF, 0x80000000ull, 0xFFFFFFFFull, 0xFFFFFFFEull,",
        "    0xFFFFFFFFFFFFFFFFull, 0x8000000000000000ull};",
        "static uint64_t pick(void) {",
        "    uint64_t r = rnd64();",
        "    switch (r % 4) {",
        "    case 0: return EDGES[(r >> 8) % (sizeof(EDGES) / sizeof(EDGES[0]))];",
        "    case 1: return (r >> 8) % 64;          /* kichik sonlar */",
        "    default: return rnd64();               /* ixtiyoriy katta sonlar */",
        "    }",
        "}",
        "",
        "int main(void) {",
        "    int mismatches = 0;",
        f"    for (int t = 0; t < {n_tests}; t++) {{",
    ]
    for name, ptype in zip(arg_names, param_types):
        lines.append(f"        {ptype} {name} = ({ptype})pick();")
    call_args = ", ".join(arg_names)
    lines += [
        f"        unsigned long long ra = (unsigned long long)({ret_type}){SYMBOL_A}({call_args});",
        f"        unsigned long long rb = (unsigned long long)({ret_type}){SYMBOL_B}({call_args});",
        "        if (ra != rb) {",
        "            if (mismatches < 5) {",
        '                printf("MISMATCH args=(");',
    ]
    for i, name in enumerate(arg_names):
        sep = ", " if i else ""
        lines.append(f'                printf("{sep}0x%llx", (unsigned long long){name});')
    lines += [
        '                printf(") original=0x%llx candidate=0x%llx\\n", ra, rb);',
        "            }",
        "            mismatches++;",
        "        }",
        "        fflush(stdout);",
        "    }",
        f'    printf("RESULT tests=%d mismatches=%d\\n", {n_tests}, mismatches);',
        "    return 0;",
        "}",
    ]
    return "\n".join(lines) + "\n"


def differential_test(code_a: str, func_a: str, code_b: str, func_b: str,
                      ret_type: str, param_types: list[str],
                      n_tests: int = 2000, timeout: float = 10.0,
                      workdir: Path | None = None) -> DiffResult:
    """code_a ichidagi func_a va code_b ichidagi func_b ni solishtiradi."""
    if not is_integer_type(ret_type):
        return DiffResult("skipped", details=f"Qaytish turi butun son emas: '{ret_type}'")
    bad = [p for p in param_types if not is_integer_type(p)]
    if bad:
        return DiffResult("skipped", details=f"Butun son bo'lmagan parametr(lar): {', '.join(bad)}")
    if compiler.find_compiler() is None:
        return DiffResult("skipped", details="C kompilyatori topilmadi")

    tmp_ctx = tempfile.TemporaryDirectory(prefix="deobf_diff_") if workdir is None else None
    wd = Path(tmp_ctx.name) if tmp_ctx else workdir
    try:
        # -D makrosi yordamida ikkala funksiyaga turli nom beramiz, shunda ular bitta
        # dasturda birga yashay oladi (aks holda nomlar to'qnashadi).
        res_a, obj_a = compiler.compile_object(code_a, wd, "original", {func_a: SYMBOL_A})
        if not res_a.ok:
            return DiffResult("inconclusive", details="Original kod kompilyatsiya bo'lmadi:\n" + res_a.errors)
        res_b, obj_b = compiler.compile_object(code_b, wd, "candidate", {func_b: SYMBOL_B})
        if not res_b.ok:
            return DiffResult("inconclusive", details="Yangi kod kompilyatsiya bo'lmadi:\n" + res_b.errors)
        harness = build_harness_source(ret_type, param_types, n_tests)
        res_h, obj_h = compiler.compile_object(harness, wd, "harness")
        if not res_h.ok:
            return DiffResult("inconclusive", details="Test dasturi kompilyatsiya bo'lmadi:\n" + res_h.errors)
        exe = wd / "difftest.exe"
        res_l = compiler.link([obj_a, obj_b, obj_h], exe)
        if not res_l.ok:
            return DiffResult("inconclusive",
                              details="Bog'lash (link) bo'lmadi — ehtimol tashqi funksiya yoki global "
                                      "o'zgaruvchi aniqlanmagan:\n" + res_l.errors)
        try:
            proc = subprocess.run([str(exe)], capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return DiffResult("inconclusive", details=f"Test {timeout} soniyada tugamadi (cheksiz tsikl?)")
        out = proc.stdout
        m = re.search(r"RESULT tests=(\d+) mismatches=(\d+)", out)
        if proc.returncode != 0 or not m:
            return DiffResult("inconclusive",
                              details=f"Test dasturi favqulodda to'xtadi (kod {proc.returncode}), "
                                      f"masalan nolga bo'lish. Chiqish:\n{out[-800:]}")
        tests, mism = int(m.group(1)), int(m.group(2))
        examples = "\n".join(l for l in out.splitlines() if l.startswith("MISMATCH"))
        if mism == 0:
            return DiffResult("equivalent", tests, 0, f"{tests} ta tasodifiy test — barchasi mos keldi")
        return DiffResult("mismatch", tests, mism, f"{mism}/{tests} testda farq:\n{examples}")
    finally:
        if tmp_ctx:
            tmp_ctx.cleanup()
