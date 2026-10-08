"""C kompilyatori (gcc/clang) bilan ishlash uchun yordamchi funksiyalar.

Nima uchun kerak: LLM yozgan C kodni "ko'r-ko'rona" qabul qilmaymiz. Avval uni
kompilyatordan o'tkazamiz: sintaksis xatosi bo'lsa, xato matnini LLM'ga qaytarib,
tuzatishni so'raymiz. Kompilyator topilmasa, tekshiruv o'tkazib yuboriladi
(dastur baribir ishlaydi, faqat natija "tekshirilmagan" deb belgilanadi).
"""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from . import sandbox

# re_types.h — IDA/Ghidra turlarini e'lon qiluvchi sarlavha fayli.
TYPES_HEADER = Path(__file__).parent / "data" / "re_types.h"

# Psevdokod ko'pincha "qattiq" C standartiga to'liq mos kelmaydi (masalan, e'lon
# qilinmagan funksiyalarni chaqiradi). Shuning uchun bu holatlarni xato emas,
# ogohlantirish deb hisoblaymiz. -fwrapv: ishorali sonlar to'lib ketganda
# mashinadagi kabi "aylanib" ketishini kafolatlaydi (psevdokod shunga tayanadi).
LENIENT_FLAGS = [
    "-std=gnu11",
    "-w",
    "-fwrapv",
    "-Wno-error=implicit-function-declaration",
    "-Wno-error=implicit-int",
    "-Wno-error=int-conversion",
    "-Wno-error=incompatible-pointer-types",
]


@dataclass
class CompileResult:
    ok: bool
    errors: str = ""


NO_COMPILER = "C kompilyatori topilmadi (gcc yoki clang o'rnating)"


def find_compiler() -> str | None:
    """Tizimdagi C kompilyatorini topadi (DEOBF_CC muhit o'zgaruvchisi ustun)."""
    env = os.environ.get("DEOBF_CC")
    if env:
        return env
    for name in ("gcc", "clang", "cc"):
        path = shutil.which(name)
        if path:
            return path
    return None


_STD_WIDTHS = {"8", "16", "32", "64"}


def prepare_source(code: str) -> str:
    """Psevdokodni kompilyatsiyaga tayyorlaydi (dekompilyatorga xos yozuvlarni standart C ga aylantiradi).

    * IDA: `0x10i64`, `1ui64` kabi son qo'shimchalari -> `0x10LL`, `1ULL`;
      `int a1@<eax>` kabi registr izohlari olib tashlanadi;
    * Ghidra: `auVar1._8_8_` (o'zgaruvchining 8-baytidan boshlab 8 bayt) -> xotiraga ko'rsatkich orqali murojaat;
    * angr: `uint224_t` kabi nostandart kenglikdagi turlar uchun struktura e'lon qilinadi.
    """
    code = re.sub(r"\b(0[xX][0-9A-Fa-f]+|\d+)(u?)i(8|16|32|64)\b",
                  lambda m: m.group(1) + m.group(2).upper() + ("LL" if m.group(3) == "64" else ""), code)
    code = re.sub(r"@<\w+(?::\w+)?>", "", code)
    # Ghidra: *(long *)(in_FS_OFFSET + 0x28) — stack canary o'qish -> IDA'dagi kabi __readfsqword(0x28)
    code = re.sub(r"\*\s*\(\s*[\w\s]+\*\s*\)\s*\(\s*in_FS_OFFSET\s*\+\s*(0[xX][0-9A-Fa-f]+|\d+)\s*\)",
                  r"__readfsqword(\1)", code)
    code = re.sub(r"\b([A-Za-z_]\w*)\._(\d+)_(1|2|4|8)_\b",
                  lambda m: f"(*(uint{int(m.group(3)) * 8}_t *)((unsigned char *)&{m.group(1)} + {m.group(2)}))", code)
    extra = []
    for sign, width in sorted(set(re.findall(r"\b(u?)int(\d+)_t\b", code))):
        if width in _STD_WIDTHS:
            continue
        name = f"{sign}int{width}_t"
        nbytes = max(1, int(width) // 8)
        if width == "128":
            extra.append(f"typedef {'unsigned ' if sign else ''}__int128 {name};")
        else:
            extra.append(f"typedef struct {{ unsigned char b[{nbytes}]; }} {name};")
    if not extra:
        return code
    return "/* deobf: nostandart turlar */\n" + "\n".join(extra) + "\n" + code


def _compile(code: str, workdir: Path, name: str, flags: list[str],
             defines: dict[str, str] | None = None) -> CompileResult:
    cc = find_compiler()
    if cc is None:
        return CompileResult(ok=False, errors=NO_COMPILER)
    workdir.mkdir(parents=True, exist_ok=True)
    src = workdir / f"{name}.c"
    src.write_text(prepare_source(code), encoding="utf-8")
    cmd = [cc, *LENIENT_FLAGS, *flags, "-include", str(TYPES_HEADER)]
    cmd += [f"-D{k}={v}" for k, v in (defines or {}).items()]
    proc = sandbox.run(cmd + [str(src)], timeout=60, cpu_sec=30, mem_mb=1024)
    if proc.timed_out:
        return CompileResult(ok=False, errors="Kompilyatsiya juda uzoq davom etdi (60 s)")
    return CompileResult(ok=proc.returncode == 0, errors=_clean(proc.stderr, workdir))


def syntax_check(code: str, workdir: Path) -> CompileResult:
    """Kodni faqat sintaksis va turlar bo'yicha tekshiradi (binar fayl yaratmaydi)."""
    return _compile(code, workdir, "candidate", ["-fsyntax-only"])


def compile_object(code: str, workdir: Path, name: str,
                   defines: dict[str, str] | None = None) -> tuple[CompileResult, Path]:
    """Kodni obyekt faylga (.o) kompilyatsiya qiladi. defines — -D makroslar (nomni almashtirish uchun)."""
    obj = workdir / f"{name}.o"
    return _compile(code, workdir, name, ["-O0", "-c", "-o", str(obj)], defines), obj


def link(objects: list[Path], output: Path) -> CompileResult:
    cc = find_compiler()
    if cc is None:
        return CompileResult(ok=False, errors=NO_COMPILER)
    proc = sandbox.run([cc, *map(str, objects), "-o", str(output)], timeout=60, cpu_sec=30, mem_mb=1024)
    return CompileResult(ok=proc.returncode == 0, errors=_clean(proc.stderr, output.parent))


def _clean(stderr: str, workdir: Path) -> str:
    """Xato matnidan vaqtinchalik papka yo'llarini olib tashlaydi (LLM uchun qisqaroq bo'lsin)."""
    lines = stderr.replace(str(workdir) + os.sep, "").strip().splitlines()
    if len(lines) > 40:  # juda uzun xato ro'yxatini qisqartiramiz — tokenlarni tejash uchun
        lines = lines[:40] + [f"... (yana {len(lines) - 40} qator)"]
    return "\n".join(lines)
