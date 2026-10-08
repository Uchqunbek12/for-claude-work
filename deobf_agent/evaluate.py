"""Baholash: agentni test namunalarida ishga tushirib, natijani raqamlar bilan o'lchash.

Har bir namuna uchun:
  * psevdokodga ekvivalentmi      — verifier natijasi (agent ham shuni ko'radi);
  * HAQIQIY asl kodga ekvivalentmi — natija samples/src/clean dagi toza kod bilan solishtiriladi.
    Bu "oltin standart": agent toza kodni ko'rmaydi, biz esa uni bilamiz;
  * usullarni aniqlash (recall)   — psevdokodda bor usullarning necha foizi topildi;
  * murakkablik                   — qatorlar va tsiklomatik murakkablik: psevdokod -> natija -> toza kod;
  * narx, vaqt, urinishlar soni.

Ishga tushirish:  deobf eval --offline          (bepul)
                  deobf eval --model haiku      (Claude bilan; API kalit kerak)
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from . import harness, metrics
from .agent import AgentConfig, deobfuscate_text

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"
TRUTH_UZ = {"equivalent": "✅", "mismatch": "❌", "inconclusive": "?", "skipped": "—"}


def evaluate_sample(s: dict, cfg: AgentConfig, source: str = "angr") -> dict | None:
    path = SAMPLES / "decompiled" / f"{s['id']}.{source}.c"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    clean = (SAMPLES / "src" / "clean" / f"{s['id']}.c").read_text(encoding="utf-8")
    parsed, reports = deobfuscate_text(text, cfg, function=s["function"])
    rep = reports[0]
    truth = harness.differential_test(clean, s["function"], rep.result.c_code, s["function"],
                                      s["ret"], s["params"], n_tests=5000, data_blobs=parsed.data_blobs)
    expected = set(s.get("pseudocode_techniques", s["techniques"]))
    found = set(rep.analysis.techniques()) | set(rep.result.techniques)
    recall = len(expected & found) / len(expected) if expected else 1.0
    return {
        "id": s["id"], "engine": rep.engine, "verification": rep.verification.status,
        "truth": truth.status, "truth_details": truth.details.splitlines()[0] if truth.details else "",
        "recall": recall, "missed": sorted(expected - found),
        "before": rep.metrics_before.to_dict(), "after": rep.metrics_after.to_dict(),
        "clean": metrics.measure(clean).to_dict(),
        "attempts": len(rep.attempts), "cost": rep.usage.cost_usd, "tokens_in": rep.usage.input_tokens,
        "tokens_out": rep.usage.output_tokens, "time": rep.elapsed_sec, "error": rep.error,
        "suggested_name": rep.result.suggested_name,
    }


def to_markdown(rows: list[dict], title: str, source: str = "angr") -> str:
    out = [f"# Baholash natijalari — {title}", "", f"Sana: {date.today().isoformat()}  ",
           f"Kirish: `samples/decompiled/*.{source}.c` ({source} dekompilyatori natijasi).", "",
           "| Namuna | Psevdokodga ekvivalent | Asl kodga ekvivalent | Usullar topildi | Qatorlar (psevdo → natija → toza) "
           "| CC (psevdo → natija → toza) | Urinish | Narx | Vaqt |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(
            f"| {r['id']} | {r['verification']} | {TRUTH_UZ.get(r['truth'], r['truth'])} | {r['recall']:.0%}"
            + (f" (topilmadi: {', '.join(r['missed'])})" if r["missed"] else "")
            + f" | {r['before']['lines']} → {r['after']['lines']} → {r['clean']['lines']}"
            f" | {r['before']['cyclomatic']} → {r['after']['cyclomatic']} → {r['clean']['cyclomatic']}"
            f" | {r['attempts']} | ${r['cost']:.5f} | {r['time']} s |")
    n = len(rows)
    ver = sum(r["verification"] == "verified" for r in rows)
    tru = sum(r["truth"] == "equivalent" for r in rows)
    cc_b = sum(r["before"]["cyclomatic"] for r in rows)
    cc_a = sum(r["after"]["cyclomatic"] for r in rows)
    ln_b = sum(r["before"]["lines"] for r in rows)
    ln_a = sum(r["after"]["lines"] for r in rows)
    out += ["", "**Jami:**", "",
            f"- Psevdokodga ekvivalentligi isbotlangan: **{ver}/{n}**",
            f"- Haqiqiy asl kodga ekvivalent: **{tru}/{n}**",
            f"- Usullarni aniqlash (o'rtacha recall): **{sum(r['recall'] for r in rows) / n:.0%}**",
            f"- Tsiklomatik murakkablik: **{cc_b} → {cc_a}** ({(cc_b - cc_a) / cc_b:.0%} kamaydi)",
            f"- Qatorlar: **{ln_b} → {ln_a}** ({(ln_b - ln_a) / ln_b:.0%} kamaydi)",
            f"- Umumiy narx: **${sum(r['cost'] for r in rows):.5f}**", ""]
    errors = [r for r in rows if r["error"]]
    if errors:
        out += ["**LLM xatolari:**", ""] + [f"- {r['id']}: {r['error']}" for r in errors] + [""]
    out += ["Izoh: `s2_opaque` uchun angr dekompilyatori shartni xato soddalashtirgan (jurnal, 1.6-bo'lim). "
            "Agent psevdokodni etalon deb oladi, shuning uchun natija psevdokodga ekvivalent bo'lsa ham, "
            "asl kodga ekvivalent bo'lmasligi mumkin — bu dekompilyator xatosi, agentniki emas.", ""]
    return "\n".join(out)


def run_evaluation(model: str | None = None, offline: bool = False, effort: str = "medium",
                   output: str | None = None, quiet: bool = False, source: str = "angr") -> int:
    manifest = json.loads((SAMPLES / "manifest.json").read_text(encoding="utf-8"))
    cfg = AgentConfig(model=model, offline=offline, effort=effort)
    rows = []
    for s in manifest["samples"]:
        if not quiet:
            print(f"  · {s['id']} ...", file=sys.stderr, flush=True)
        row = evaluate_sample(s, cfg, source)
        if row is None:
            print(f"  · {s['id']}: samples/decompiled/{s['id']}.{source}.c topilmadi — o'tkazib yuborildi",
                  file=sys.stderr)
            continue
        rows.append(row)
    if not rows:
        print("Baholash uchun fayl topilmadi.", file=sys.stderr)
        return 1
    title = "offline (LLM'siz)" if offline else f"model: {rows[0]['engine'] if rows else model}"
    md = to_markdown(rows, title, source)
    print(md)
    if output:
        Path(output).write_text(md, encoding="utf-8")
        Path(output).with_suffix(".json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saqlandi: {output}", file=sys.stderr)
    return 0
