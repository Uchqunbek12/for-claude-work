"""Offline rejim uchun bloklar va xulosa: har bir blok nima qilishini odam tilida aytadi.

Bloklar ikki turdan iborat:
  * "mantiq" bloklari — tozalangan funksiyaning qadamlari bajarilish tartibida (narrate.py): nima hisoblanadi,
    qaysi shart tekshiriladi, qaysi tsikl nechta narsani aylanib chiqadi. Imkon bo'lsa, ular asl koddagi qatorlarga
    bog'lanadi va qaysi chalkash ifoda qanday soddalashtirilgani shu blokning o'zida aytiladi;
  * "tozalash" bloklari — olib tashlangan narsalar: keraksiz qatorlar, hech qachon bajarilmaydigan tarmoqlar,
    tekislangan boshqaruv oqimi, ochilgan yashirin matn.
Har bir blokda ikki xil matn bor: mutaxassis uchun (`explanation`) va oddiy tilda (`simple`).
"""

from __future__ import annotations

import re

from . import narrate
from . import parser as P
from .detectors import AnalysisResult
from .explain import SIMPLE_SHORT, SIMPLE_TITLES, TECH_NAMES_UZ
from .models import FunctionInfo
from .schema import Block


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def _clip(s: str, n: int = 140) -> str:
    s = re.sub(r"\s+", " ", s.strip())
    return s if len(s) <= n else s[:n - 1] + "…"


def _lines_label(lines: list[int]) -> str:
    lo, hi = min(lines), max(lines)
    return str(lo) if lo == hi else f"{lo}-{hi}"


def _dispatcher_region(func_text: str) -> tuple[int, int] | None:
    """Tekislash (flattening) dispatcheri: `while (1) { switch ... }` tanasining qatorlar oralig'i."""
    m = P.mask_code(func_text)
    hit = re.search(r"\b(?:while\s*\(\s*(?:1|true|-1)\s*\)|for\s*\(\s*;\s*;\s*\))\s*\{", m)
    if not hit:
        return None
    close = P.find_close(m, hit.end() - 1, "{}")
    if close < 0:
        return None
    return m.count("\n", 0, hit.start()) + 1, m.count("\n", 0, close) + 1


def build(func: FunctionInfo, analysis: AnalysisResult, changes: list[tuple[int, str, str]], final_func_text: str,
          unflattened: bool) -> list[Block]:
    orig = func.text.splitlines()
    index: dict[str, list[int]] = {}
    for i, ln in enumerate(orig, 1):
        if _norm(ln) not in ("", "{", "}"):
            index.setdefault(_norm(ln), []).append(i)
    changed = {} if unflattened else {_norm(new): (line, old, new) for line, old, new in changes}   # qatorlar asl koordinatada
    region = _dispatcher_region(func.text) if unflattened else None
    blocks: list[tuple[tuple[int, int], Block]] = []       # (tartib kaliti, blok)

    # ---------------------------------------------------------------- mantiq bloklari
    for st in narrate.walkthrough(final_func_text):
        hits: list[int] = []
        sentences_x: list[str] = []
        used_changes = []
        for ln in (x.strip() for x in st.code.splitlines()):
            n = _norm(ln)
            if n in ("", "{", "}"):
                continue
            if n in changed:
                line, old, new = changed[n]
                hits.append(line)
                used_changes.append((line, old, new))
            elif n in index:
                free = [x for x in index[n] if x >= (hits[-1] if hits else 0)] or index[n]
                hits.append(free[0])
        if hits and region and any(region[0] <= h <= region[1] for h in hits):
            hits = []                    # tekislangan hududdagi qatorlar yangi tartibga mos kelmaydi: butun hudud ko'rsatiladi
        if hits:
            label = _lines_label(hits)
            original_code = "\n".join(orig[min(hits) - 1:max(hits)][:12])
            key = (min(hits), 1)
        elif region:
            label = f"{region[0]}-{region[1]}"
            original_code = ""           # "oldin" kodi bu qadamga xos emas: butun dispatcher yuqoridagi blokda ko'rsatilgan
            key = (region[0], 1)
        else:
            label, original_code, key = "", "", (10 ** 6, 1)
        text, simple = st.text, st.simple
        for line, old, new in used_changes:
            sentences_x.append(f"Chalkash yozuv `{_clip(old)}` unga teng `{_clip(new)}` bilan almashtirildi.")
        if used_changes:
            text += "\n" + " ".join(sentences_x)
            simple += "\n" + SIMPLE_SHORT["mba"]
        notes = narrate.known_notes(st.code)
        if notes:
            text += "\nMashhur konstanta: " + "; ".join(notes) + "."
            simple += "\n" + SIMPLE_SHORT["known_constants"]
        blocks.append((key, Block(title=st.title, original_lines=label, original_code=original_code,
                                  simplified_code=st.code.strip(), explanation=text, simple=simple)))

    # ---------------------------------------------------------------- tozalash bloklari
    dead = [f for f in analysis.findings if f.technique == "dead_code"]
    if dead:
        lines = sorted({f.line for f in dead})
        n = len(dead)
        blocks.append(((lines[0], 0), Block(
            title="Keraksiz qatorlar olib tashlandi", original_lines=_lines_label(lines),
            original_code="\n".join(_clip(f.snippet, 100) for f in dead[:6]), simplified_code="/* olib tashlandi */",
            explanation=(f"{n} ta qatorda qiymat yoziladi, lekin u hech qayerda o'qilmaydi yoki natijaga ta'sir qilmaydi: "
                         "ularni olib tashlash funksiyaning javobini o'zgartirmaydi."),
            simple=SIMPLE_SHORT["dead_code"] + f" Bu yerda shunday {n} ta qator topildi.")))
    for f in analysis.findings:
        if f.technique == "opaque_predicate":
            blocks.append(((f.line, 0), Block(
                title="Hech qachon bajarilmaydigan tarmoq olib tashlandi", original_lines=str(f.line),
                original_code=_clip(orig[f.line - 1] if 0 < f.line <= len(orig) else f.snippet, 200),
                simplified_code="/* olib tashlandi */",
                explanation=f.message.split("\n")[0], simple=SIMPLE_SHORT["opaque_predicate"])))
    if unflattened and analysis.state_machines:
        sm = analysis.state_machines[0]
        start = region[0] if region else 1
        blocks.append(((start, 0), Block(
            title="Aralashtirilgan bosqichlar tartibga keltirildi",
            original_lines=f"{region[0]}-{region[1]}" if region else str(start),
            original_code="\n".join(orig[start - 1:start + 3]) + "\n...", simplified_code="/* quyidagi qadamlarga qarang */",
            explanation=(f"Kod {len(sm.transitions)} ta bosqichga bo'lingan edi; qaysi bosqich qachon bajarilishini "
                         f"`{sm.state_var}` o'zgaruvchisi belgilardi. Bosqichlar o'rtasidagi o'tishlar tahlil qilindi: boshiga "
                         "qaytadigan yo'l tsikl (while), ikkiga ajraladigan joy shart (if/else) bo'ldi, `switch` va holat "
                         "o'zgaruvchisi esa olib tashlandi."),
            simple=SIMPLE_SHORT["control_flow_flattening"])))
    elif analysis.state_machines:
        blocks.append(((1, 0), Block(
            title="Aralashtirilgan bosqichlar topildi", original_lines="1", original_code=_clip(orig[0] if orig else ""),
            simplified_code="", explanation="Boshqaruv oqimi tekislangan (flattening), lekin uni avtomatik yechib bo'lmadi: "
                                            "holatlar xaritasi Statik tahlil bo'limida.",
            simple=SIMPLE_SHORT["control_flow_flattening"] + " Bu safar kartochkalarni to'liq tartibga sololmadik.")))
    for name, text in analysis.decoded_strings.items():
        line = next((f.line for f in analysis.findings if f.technique == "encoded_strings"), 1)
        blocks.append(((line, 0), Block(
            title="Yashirin matn ochildi", original_lines=str(line),
            original_code=_clip(orig[line - 1] if 0 < line <= len(orig) else name, 200),
            simplified_code=f'/* {name} = "{_clip(text, 80)}" */',
            explanation=f"`{name}` baytlari kalit bilan (XOR) yashirilgan edi; ochilgach matn «{_clip(text, 80)}» chiqdi.",
            simple=SIMPLE_SHORT["encoded_strings"] + f" Ochilgan yozuv: «{_clip(text, 60)}».")))

    blocks.sort(key=lambda kb: kb[0])
    return [b for _, b in blocks]


def summaries(func: FunctionInfo, analysis: AnalysisResult, final_func_text: str, changes: list, unflattened: bool
              ) -> tuple[str, str]:
    """Butun funksiya uchun: (mutaxassis xulosasi, oddiy tildagi xulosa) — avvalo funksiya NIMA qilishi, so'ng nima tozalangani."""
    parsed = P.parse(final_func_text).get(func.name)
    params = [(p.type, p.name) for p in (parsed or func).params]
    meaning, meaning_simple = narrate.meaning(func.name, params, final_func_text, analysis.decoded_strings)
    techniques = [t for t in analysis.techniques() if t != "known_constants"]
    done: list[str] = []
    if changes and not unflattened:
        done.append(f"{len(changes)} ta chalkash ifoda soddalashtirildi")
    elif changes:
        done.append("chalkash ifodalar soddalashtirildi")
    n_op = sum(f.technique == "opaque_predicate" for f in analysis.findings)
    if n_op:
        done.append(f"hech qachon bajarilmaydigan {n_op} ta tarmoq olib tashlandi")
    if unflattened:
        done.append("tekislangan boshqaruv oqimi tiklandi")
    n_dead = sum(f.technique == "dead_code" for f in analysis.findings)
    if n_dead:
        done.append(f"{n_dead} ta keraksiz qator olib tashlandi")
    if analysis.decoded_strings:
        done.append("yashirin matn ochildi")
    known = narrate.known_notes(final_func_text)

    head = meaning if meaning.startswith(f"`{func.name}`") else f"`{func.name}` — {meaning}"
    summary = head[0].upper() + head[1:]
    if techniques:
        summary += (f" Chalkashtirish usullari: {', '.join(TECH_NAMES_UZ.get(t, t) for t in techniques)}."
                    + (f" Tozalash: {'; '.join(done)}." if done else ""))
    else:
        summary += " Chalkashtirish belgilari topilmadi — kod shundoq ham oddiy ko'rinadi."
    if known:
        summary += " Mashhur algoritm belgilari: " + "; ".join(known) + "."

    if techniques:
        titles = ", ".join(f"«{SIMPLE_TITLES.get(t, t)}»" for t in techniques)
        simple = (f"{meaning_simple} Kod ataylab chalkash yozilgan edi ({titles}). Vosita uni tartibga keltirdi: "
                  "ma'nosi o'zgarmadi, faqat o'qish osonlashdi.")
    else:
        simple = f"{meaning_simple} Bu kodda ataylab chalkashtirish belgilari topilmadi."
    return summary, simple
