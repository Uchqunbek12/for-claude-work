"""Natijalarni hisobotga aylantirish: Markdown, JSON va HTML.

* JSON     — boshqa dasturlar uchun (mashina o'qiydigan format);
* Markdown — GitHub'da yoki matn muharririda o'qish uchun;
* HTML     — brauzerda ochiladigan chiroyli hisobot (Web UI bilan bir xil shablon).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .agent import FunctionReport
from .explain import TECH_NAMES_UZ
from .models import ParsedInput
from .prompts import number_lines

STYLE_NAMES = {"ida": "IDA (Hex-Rays)", "ghidra": "Ghidra", "angr": "angr", "c": "oddiy C"}
CONFIDENCE_UZ = {"low": "past", "medium": "o'rta", "high": "yuqori"}
# HTML shablonlar (Web UI va saqlanadigan hisobot) uchun umumiy o'zgaruvchilar
TEMPLATE_GLOBALS = dict(tech_names=TECH_NAMES_UZ, style_names=STYLE_NAMES, confidence_uz=CONFIDENCE_UZ)


def display_code(rep: FunctionReport) -> str:
    """Ko'rsatish uchun: funksiya nomini taklif qilingan mazmunli nomga almashtiradi."""
    code = rep.result.c_code
    new = rep.result.suggested_name
    if new and new != rep.function.name and re.fullmatch(r"[A-Za-z_]\w*", new):
        code = re.sub(rf"\b{re.escape(rep.function.name)}\b", new, code)
    return code


def report_to_dict(rep: FunctionReport) -> dict:
    return {
        "function": rep.function.name,
        "suggested_name": rep.result.suggested_name,
        "style": rep.style,
        "engine": rep.engine,
        "verification": rep.verification.to_dict(),
        "attempts": [a.__dict__ for a in rep.attempts],
        "metrics_before": rep.metrics_before.to_dict() if rep.metrics_before else None,
        "metrics_after": rep.metrics_after.to_dict() if rep.metrics_after else None,
        "usage": rep.usage.to_dict(),
        "error": rep.error,
        "elapsed_sec": rep.elapsed_sec,
        "original_code": rep.function.text,
        "display_code": display_code(rep),
        "result": rep.result.model_dump(),
        "static_findings": [f.to_dict() for f in rep.analysis.findings],
        "state_machines": [sm.describe_uz() for sm in rep.analysis.state_machines],
        "decoded_strings": rep.analysis.decoded_strings,
    }


def to_data(parsed: ParsedInput, reports: list[FunctionReport]) -> dict:
    return {"style": parsed.style, "functions": [report_to_dict(r) for r in reports],
            "total_cost_usd": round(sum(r.usage.cost_usd for r in reports), 6)}


def to_json(parsed: ParsedInput, reports: list[FunctionReport]) -> str:
    return json.dumps(to_data(parsed, reports), ensure_ascii=False, indent=2)


def _md_escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def to_markdown(parsed: ParsedInput, reports: list[FunctionReport]) -> str:
    out = ["# Deobfuskatsiya hisoboti", "",
           f"- Kirish uslubi: **{STYLE_NAMES.get(parsed.style, parsed.style)}**",
           f"- Funksiyalar soni: **{len(reports)}**",
           f"- Umumiy narx: **${sum(r.usage.cost_usd for r in reports):.4f}**", ""]
    for rep in reports:
        res, mb, ma = rep.result, rep.metrics_before, rep.metrics_after
        out += [f"## `{rep.function.name}` → `{res.suggested_name}`", ""]
        if rep.error:
            out += [f"> ⚠️ LLM xatosi: {rep.error}. Natija offline tahlildan olindi.", ""]
        out += [
            "| Ko'rsatkich | Qiymat |", "|---|---|",
            f"| Dvigatel | {rep.engine} |",
            f"| Tekshiruv | {rep.verification.label_uz} |",
            f"| Ishonch (model bahosi) | {CONFIDENCE_UZ.get(res.confidence, res.confidence)} |",
            f"| Qatorlar | {mb.lines} → {ma.lines} |",
            f"| Tsiklomatik murakkablik | {mb.cyclomatic} → {ma.cyclomatic} |",
            f"| Urinishlar | {len(rep.attempts)} |",
            f"| Tokenlar (kirish / chiqish / keshdan o'qilgan) | {rep.usage.input_tokens} / "
            f"{rep.usage.output_tokens} / {rep.usage.cache_read_tokens} |",
            f"| Narx | ${rep.usage.cost_usd:.5f}" + (" (keshdan)" if rep.usage.cache_hits else "") + " |",
            f"| Vaqt | {rep.elapsed_sec} s |", "",
            "### Qisqacha", "", res.summary, "",
        ]
        if res.simple_summary:
            out += ["### Oddiy tilda (dehqoncha)", "", res.simple_summary, ""]
        if res.techniques:
            out += ["**Aniqlangan obfuskatsiya usullari:** "
                    + ", ".join(TECH_NAMES_UZ.get(t, t) for t in res.techniques), ""]
        out += ["### Soddalashtirilgan C kod", "", "```c", display_code(rep).rstrip(), "```", ""]
        if res.blocks:
            out += ["### Bloklar bo'yicha tushuntirish", ""]
            for i, b in enumerate(res.blocks, 1):
                out += [f"#### {i}. {b.title} (qatorlar {b.original_lines})", "",
                        "Asl psevdokod:", "```c", b.original_code.rstrip(), "```"]
                if b.simplified_code.strip():
                    out += ["Soddalashtirilgan:", "```c", b.simplified_code.rstrip(), "```"]
                out += ["", b.explanation, ""]
                if b.simple:
                    out += [f"*Oddiy tilda:* {b.simple}", ""]
        if res.renames:
            out += ["### Qayta nomlashlar", "", "| Eski | Yangi | Sabab |", "|---|---|---|"]
            out += [f"| `{r.old}` | `{r.new}` | {_md_escape_cell(r.reason)} |" for r in res.renames]
            out.append("")
        if rep.analysis.findings:
            out += ["### Statik tahlil topilmalari (LLM'siz)", ""]
            for f in rep.analysis.findings:
                mark = " (test bilan tasdiqlangan)" if f.verified else ""
                out.append(f"- **{TECH_NAMES_UZ.get(f.technique, f.technique)}**, {f.line}-qator{mark}: "
                           + f.message.split("\n")[0])
            out.append("")
        for sm in rep.analysis.state_machines:
            out += ["```text", sm.describe_uz(), "```", ""]
        out += ["### Tekshiruv tafsilotlari", ""]
        for a in rep.attempts:
            out.append(f"- {a.round}-urinish: **{a.status}** — {a.details.splitlines()[0] if a.details else ''}")
        out.append("")
        if res.notes:
            out += ["### Eslatmalar", "", res.notes, ""]
        out += ["<details><summary>Asl psevdokod</summary>", "", "```c", number_lines(rep.function.text), "```",
                "", "</details>", ""]
    return "\n".join(out)


def _jinja_env():
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "web" / "templates")),
                      autoescape=select_autoescape(["html"]))
    env.globals.update(TEMPLATE_GLOBALS)
    return env


def to_html(parsed: ParsedInput, reports: list[FunctionReport]) -> str:
    return _jinja_env().get_template("standalone.html").render(data=to_data(parsed, reports))
