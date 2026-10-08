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
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

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
    command: list[str] = field(default_factory=list)


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
    """Psevdokodni kompilyatsiyaga tayyorlaydi.

    angr kabi dekompilyatorlar katta buferlar uchun `uint224_t` kabi nostandart
    turlar yaratadi. Bunday turlar uchun kerakli o'lchamdagi struktura e'lon qilamiz.
    """
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


def _run(cmd: list[str], timeout: float) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def syntax_check(code: str, workdir: Path, name: str = "candidate", timeout: float = 30) -> CompileResult:
    """Kodni faqat sintaksis va turlar bo'yicha tekshiradi (binar fayl yaratmaydi)."""
    cc = find_compiler()
    if cc is None:
        return CompileResult(ok=False, errors="C kompilyatori topilmadi (gcc yoki clang o'rnating)")
    workdir.mkdir(parents=True, exist_ok=True)
    src = workdir / f"{name}.c"
    src.write_text(prepare_source(code), encoding="utf-8")
    cmd = [cc, *LENIENT_FLAGS, "-fsyntax-only", "-include", str(TYPES_HEADER), str(src)]
    proc = _run(cmd, timeout)
    return CompileResult(ok=proc.returncode == 0, errors=_clean(proc.stderr, workdir), command=cmd)


def compile_object(code: str, workdir: Path, name: str, defines: dict[str, str] | None = None,
                   timeout: float = 60) -> tuple[CompileResult, Path]:
    """Kodni obyekt faylga (.o) kompilyatsiya qiladi. defines — -D makroslar."""
    cc = find_compiler()
    obj = workdir / f"{name}.o"
    if cc is None:
        return CompileResult(ok=False, errors="C kompilyatori topilmadi"), obj
    workdir.mkdir(parents=True, exist_ok=True)
    src = workdir / f"{name}.c"
    src.write_text(prepare_source(code), encoding="utf-8")
    cmd = [cc, *LENIENT_FLAGS, "-O0", "-c", "-include", str(TYPES_HEADER)]
    for key, value in (defines or {}).items():
        cmd.append(f"-D{key}={value}")
    cmd += [str(src), "-o", str(obj)]
    proc = _run(cmd, timeout)
    return CompileResult(ok=proc.returncode == 0, errors=_clean(proc.stderr, workdir), command=cmd), obj


def link(objects: list[Path], output: Path, timeout: float = 60) -> CompileResult:
    cc = find_compiler()
    if cc is None:
        return CompileResult(ok=False, errors="C kompilyatori topilmadi")
    cmd = [cc, *map(str, objects), "-o", str(output)]
    proc = _run(cmd, timeout)
    return CompileResult(ok=proc.returncode == 0, errors=_clean(proc.stderr, output.parent), command=cmd)


def _clean(stderr: str, workdir: Path) -> str:
    """Xato matnidan vaqtinchalik papka yo'llarini olib tashlaydi (LLM uchun qisqaroq bo'lsin)."""
    text = stderr.replace(str(workdir) + os.sep, "")
    lines = text.strip().splitlines()
    if len(lines) > 40:  # juda uzun xato ro'yxatini qisqartiramiz — tokenlarni tejash uchun
        lines = lines[:40] + [f"... (yana {len(lines) - 40} qator)"]
    return "\n".join(lines)
