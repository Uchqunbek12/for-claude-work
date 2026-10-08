"""Buyruq qatori interfeysi (CLI).

Misollar:
  deobf analyze samples/decompiled/s3_flatten.angr.c              # Claude Haiku (standart)
  deobf analyze kod.c --model sonnet                              # kuchliroq model
  deobf analyze kod.c --offline                                   # bepul, LLM'siz
  deobf analyze kod.c -f sub_401136 --format html -o hisobot.html # bitta funksiya, HTML hisobot
  deobf functions kod.c                                           # fayldagi funksiyalar ro'yxati
  deobf web                                                       # brauzer interfeysi
  deobf eval --offline                                            # namunalar bo'yicha baholash
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, parser, report
from .agent import AgentConfig, deobfuscate_text
from .llm import DEFAULT_MODEL, MODEL_ALIASES, load_dotenv


def _read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8", errors="replace")


def _progress(quiet: bool):
    def fn(msg: str) -> None:
        if not quiet:
            print(f"  · {msg}", file=sys.stderr, flush=True)
    return fn


def cmd_analyze(args) -> int:
    text = _read_input(args.input)
    cfg = AgentConfig(model=args.model, offline=args.offline, effort=args.effort, language=args.lang,
                      max_rounds=args.max_rounds, n_tests=args.tests, max_tokens=args.max_tokens,
                      cache_dir=None if args.no_cache else args.cache_dir)
    try:
        parsed, reps = deobfuscate_text(text, cfg, function=args.function, progress=_progress(args.quiet))
    except ValueError as exc:
        print(f"XATO: {exc}", file=sys.stderr)
        return 2
    render = {"md": report.to_markdown, "json": report.to_json, "html": report.to_html}[args.format]
    output = render(parsed, reps)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Hisobot saqlandi: {args.output}", file=sys.stderr)
    else:
        print(output)
    total = sum(r.usage.cost_usd for r in reps)
    for r in reps:
        print(f"[{r.function.name}] {r.verification.label_uz} | dvigatel: {r.engine} | "
              f"CC {r.metrics_before.cyclomatic}->{r.metrics_after.cyclomatic} | ${r.usage.cost_usd:.5f}",
              file=sys.stderr)
    print(f"Umumiy narx: ${total:.5f}", file=sys.stderr)
    return 0 if all(r.verification.ok for r in reps) else 1


def cmd_functions(args) -> int:
    parsed = parser.parse(_read_input(args.input))
    print(f"Uslub: {parsed.style}")
    for f in parsed.functions:
        params = ", ".join(f"{p.type} {p.name}" for p in f.params) or "void"
        print(f"  {f.name}({params}) -> {f.ret_type}   [{f.start_line}-{f.end_line} qatorlar]")
    if parsed.data_blobs:
        print("Global ma'lumotlar: " + ", ".join(f"{k} ({len(v)} bayt)" for k, v in parsed.data_blobs.items()))
    return 0


def cmd_web(args) -> int:
    from .web.app import create_app

    app = create_app()
    print(f"Web UI: http://{args.host}:{args.port}  (to'xtatish: Ctrl+C)", file=sys.stderr)
    app.run(host=args.host, port=args.port, debug=False, threaded=True)
    return 0


def cmd_eval(args) -> int:
    from .evaluate import run_evaluation

    return run_evaluation(model=args.model, offline=args.offline, effort=args.effort,
                          output=args.output, quiet=args.quiet)


def build_parser() -> argparse.ArgumentParser:
    models = ", ".join(MODEL_ALIASES)
    p = argparse.ArgumentParser(prog="deobf", description="Obfuskatsiyalangan psevdokodni LLM yordamida "
                                "soddalashtiruvchi va tushuntiruvchi agent.")
    p.add_argument("--version", action="version", version=f"deobf-agent {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyze", help="psevdokodni tahlil qilish")
    a.add_argument("input", help="fayl yo'li yoki '-' (standart kirish)")
    a.add_argument("-f", "--function", help="faqat shu funksiyani tahlil qilish")
    a.add_argument("-m", "--model", help=f"model: {models} yoki to'liq model nomi (standart: {DEFAULT_MODEL})")
    a.add_argument("--offline", action="store_true", help="LLM'siz, faqat statik tahlil (bepul)")
    a.add_argument("--effort", default="medium", choices=["low", "medium", "high"], help="o'ylash chuqurligi")
    a.add_argument("--lang", default="uz", choices=["uz", "ru", "en"], help="tushuntirish tili")
    a.add_argument("--max-rounds", type=int, default=3, help="tuzatish urinishlari soni (standart: 3)")
    a.add_argument("--tests", type=int, default=2000, help="differensial testlar soni")
    a.add_argument("--max-tokens", type=int, default=16000, help="javob uchun maksimal tokenlar")
    a.add_argument("--cache-dir", default=".deobf_cache", help="disk kesh papkasi")
    a.add_argument("--no-cache", action="store_true", help="disk keshdan foydalanmaslik")
    a.add_argument("--format", default="md", choices=["md", "json", "html"], help="hisobot formati")
    a.add_argument("-o", "--output", help="hisobotni faylga saqlash")
    a.add_argument("-q", "--quiet", action="store_true", help="jarayon xabarlarini ko'rsatmaslik")
    a.set_defaults(func=cmd_analyze)

    f = sub.add_parser("functions", help="fayldagi funksiyalar ro'yxati")
    f.add_argument("input")
    f.set_defaults(func=cmd_functions)

    w = sub.add_parser("web", help="brauzer interfeysini ishga tushirish")
    w.add_argument("--host", default="127.0.0.1")
    w.add_argument("--port", type=int, default=5000)
    w.set_defaults(func=cmd_web)

    e = sub.add_parser("eval", help="test namunalari bo'yicha baholash")
    e.add_argument("-m", "--model", help=f"model: {models}")
    e.add_argument("--offline", action="store_true")
    e.add_argument("--effort", default="medium", choices=["low", "medium", "high"])
    e.add_argument("-o", "--output", default="docs/baholash_natijalari.md", help="natijalar jadvali fayli")
    e.add_argument("-q", "--quiet", action="store_true")
    e.set_defaults(func=cmd_eval)
    return p


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):          # Windows konsolida o'zbekcha harflar/emoji uchun
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    load_dotenv()
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
