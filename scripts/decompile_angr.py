"""Binar fayldagi funksiyani angr dekompilyatori yordamida psevdokodga aylantirish.

Nima uchun angr: bu bepul, Python'da yozilgan dekompilyator. Loyiha ishlab
chiqilgan bulutli serverda Ghidra'ni yuklab olish imkoni bo'lmadi, shuning uchun
test namunalari uchun HAQIQIY dekompilyatsiya natijasini angr bilan oldik.
O'z kompyuteringizda xuddi shu binar fayllarni IDA Free (F5) yoki Ghidra'da
ochib, ularning psevdokodini ham sinab ko'rishingiz mumkin.

O'rnatish:  pip install angr      (hajmi katta, ~500 MB)
Ishlatish:  python scripts/decompile_angr.py samples/bin/s1_mba.elf mix > mix.angr.c
            python scripts/decompile_angr.py --all      (barcha namunalar uchun)
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def decompile(binary: Path, func_name: str) -> str:
    import angr  # og'ir kutubxona — faqat kerak bo'lganda yuklaymiz

    logging.getLogger("angr").setLevel(logging.ERROR)
    logging.getLogger("cle").setLevel(logging.ERROR)
    proj = angr.Project(str(binary), auto_load_libs=False)
    cfg = proj.analyses.CFGFast(normalize=True, data_references=True)
    func = cfg.kb.functions.function(name=func_name)
    if func is None:
        raise SystemExit(f"Funksiya topilmadi: {func_name}")
    proj.analyses.CompleteCallingConventions(cfg=cfg.model, recover_variables=True)
    dec = proj.analyses.Decompiler(func, cfg=cfg.model)
    if dec.codegen is None:
        raise SystemExit("Dekompilyatsiya muvaffaqiyatsiz")
    text = dec.codegen.text
    return text + _global_data_comment(proj, text)


def _global_data_comment(proj, text: str) -> str:
    """Psevdokodda ishlatilgan global ma'lumotlarning baytlarini izoh sifatida qo'shadi.

    Dekompilyator faqat kodni ko'rsatadi, ma'lumot (masalan, shifrlangan satr baytlari)
    esa binar faylning alohida bo'limida turadi. IDA'da bu baytlarni "Shift+E" (Export
    data) bilan olish mumkin. Biz ularni avtomatik ravishda izohga qo'shamiz, shunda
    LLM ham, statik tahlil ham ularni ko'ra oladi.
    """
    import re

    lines = []
    for name in re.findall(r"^extern\s+[\w\s\*]+?\b(\w+);", text, flags=re.M):
        sym = proj.loader.find_symbol(name)
        if sym is None or not sym.size:
            continue
        data = proj.loader.memory.load(sym.rebased_addr, sym.size)
        hexes = " ".join(f"{b:02X}" for b in data)
        lines.append(f"// {name} @ 0x{sym.rebased_addr:X} ({sym.size} bayt): {hexes}")
    if not lines:
        return ""
    return "\n// --- Global ma'lumotlar (binar fayldan olingan) ---\n" + "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--all":
        manifest = json.loads((ROOT / "samples" / "manifest.json").read_text(encoding="utf-8"))
        out_dir = ROOT / "samples" / "decompiled"
        out_dir.mkdir(exist_ok=True)
        for s in manifest["samples"]:
            text = decompile(ROOT / "samples" / "bin" / f"{s['id']}.elf", s["function"])
            header = (f"// Manba: samples/bin/{s['id']}.elf, funksiya: {s['function']}\n"
                      f"// Dekompilyator: angr (avtomatik yaratilgan psevdokod)\n")
            (out_dir / f"{s['id']}.angr.c").write_text(header + text + "\n", encoding="utf-8")
            print(f"{s['id']}: tayyor")
        return 0
    if len(argv) != 2:
        print(__doc__)
        return 2
    print(decompile(Path(argv[0]), argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
