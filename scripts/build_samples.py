"""Test namunalarini tayyorlash skripti.

Bajaradigan ishlari:
  1. Har bir namunaning toza va obfuskatsiyalangan versiyasini differensial test
     bilan solishtiradi — obfuskatsiya dastur ishini o'zgartirmaganini isbotlash uchun.
  2. Obfuskatsiyalangan versiyani binar faylga (ELF) kompilyatsiya qiladi —
     keyin uni IDA Free / Ghidra / angr da ochib, psevdokod olamiz.

Ishga tushirish:  python scripts/build_samples.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deobf_agent import compiler, harness  # noqa: E402

SAMPLES = ROOT / "samples"


def main() -> int:
    manifest = json.loads((SAMPLES / "manifest.json").read_text(encoding="utf-8"))
    cc = compiler.find_compiler()
    if cc is None:
        print("XATO: gcc/clang topilmadi")
        return 1
    (SAMPLES / "bin").mkdir(exist_ok=True)
    all_ok = True
    for s in manifest["samples"]:
        sid, fn = s["id"], s["function"]
        clean = (SAMPLES / "src" / "clean" / f"{sid}.c").read_text(encoding="utf-8")
        obf = (SAMPLES / "src" / "obf" / f"{sid}.c").read_text(encoding="utf-8")

        diff = harness.differential_test(clean, fn, obf, fn, s["ret"], s["params"], n_tests=20000)
        print(f"[{sid}] toza vs obfuskatsiyalangan: {diff.status} — {diff.details.splitlines()[0]}")
        all_ok &= diff.status == "equivalent"

        # Binar fayl: -O0 (optimizatsiyasiz), shunda obfuskatsiya kompilyator tomonidan
        # "tozalab" yuborilmaydi va dekompilyatorda ko'rinadi. Belgilar (simvollar)
        # saqlanadi, shunda funksiyani nomi bo'yicha topish oson.
        out = SAMPLES / "bin" / f"{sid}.elf"
        src = SAMPLES / "src" / "obf" / f"{sid}.c"
        args = ", ".join("0" if "*" in t else "1" for t in s["params"])
        call = f"{fn}({args});" if s["ret"] == "void" else f"return (int){fn}({args}) & 1;"
        main_stub = f"int main(void) {{ {call} return 0; }}\n"
        stub_path = SAMPLES / "bin" / f"_{sid}_main.c"
        stub_path.write_text(f"{s['ret']} {fn}({', '.join(s['params'])});\n" + main_stub, encoding="utf-8")
        proc = subprocess.run([cc, "-O0", "-fno-inline", "-o", str(out), str(src), str(stub_path)],
                              capture_output=True, text=True)
        stub_path.unlink()
        if proc.returncode != 0:
            print(f"[{sid}] kompilyatsiya xatosi:\n{proc.stderr}")
            all_ok = False
        else:
            print(f"[{sid}] binar fayl: {out.relative_to(ROOT)}")
    print("NATIJA:", "hammasi muvaffaqiyatli" if all_ok else "xatolar bor")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
