"""Buyruq qatori interfeysi (CLI).

Misollar:
  deobf analyze samples/decompiled/s3_flatten.angr.c              # Claude Haiku (standart)
  deobf analyze kod.c --model sonnet                              # kuchliroq model
  deobf analyze kod.c --offline                                   # bepul, LLM'siz
  deobf analyze kod.c -f sub_401136 --format html -o hisobot.html # bitta funksiya, HTML hisobot
  deobf functions kod.c                                           # fayldagi funksiyalar ro'yxati
  deobf web                                                       # brauzer interfeysi
  deobf check                                                     # diagnostika: kalit ishlayaptimi?
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


def cmd_check(args) -> int:
    """Diagnostika: o'rnatish to'g'rimi, .env topildimi, kalit ishlayaptimi, gcc bormi."""
    import os
    import platform

    from . import compiler, llm

    ok_all = True

    def line(ok: bool | None, title: str, detail: str = "") -> None:
        mark = {True: "✅", False: "❌", None: "⚠️ "}[ok]
        print(f"{mark} {title}" + (f": {detail}" if detail else ""))

    print("deobf-agent diagnostikasi\n" + "=" * 40)
    py_ok = sys.version_info >= (3, 10)
    line(py_ok, "Python", f"{platform.python_version()} ({sys.executable})")
    ok_all &= py_ok
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    line(True if in_venv else None, "Virtual muhit (.venv)",
         "faol" if in_venv else "faol emas — .venv ichidagi Python ishlatilmayapti, kutubxonalar topilmasligi mumkin")
    try:
        import anthropic
        import flask

        line(True, "Kutubxonalar", f"anthropic {anthropic.__version__}, flask o'rnatilgan")
    except ImportError as exc:
        line(False, "Kutubxonalar", f"{exc} — `pip install -e .` buyrug'ini bajaring")
        return 1

    env_path = llm.DOTENV_INFO.get("path")
    if env_path:
        hint = "" if env_path.name == ".env" else f" (fayl nomi '{env_path.name}' — ishlaydi, lekin '.env' deb nomlash tavsiya etiladi)"
        line(True, ".env fayli", f"{env_path}{hint}")
    else:
        line(None, ".env fayli", f"topilmadi (qidirilgan joylar: {os.getcwd()} va {llm.PROJECT_ROOT})")
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        src = ".env faylidan" if "ANTHROPIC_API_KEY" in llm.DOTENV_INFO.get("keys", []) else "tizim muhit o'zgaruvchisidan"
        line(True, "ANTHROPIC_API_KEY", f"{llm.mask_key(key)} ({src})")
    else:
        line(False, "ANTHROPIC_API_KEY", "topilmadi — faqat --offline rejim ishlaydi")
        ok_all = False

    if key and not args.no_network:
        print("\nKalitni Claude serverida tekshirish (bepul so'rov, matn yaratilmaydi)...")
        models = [args.model] if args.model else list(MODEL_ALIASES)
        for m in models:
            ok, msg = llm.check_api_key(m)
            line(ok, f"Model '{m}'", msg)
            ok_all &= ok or m != (args.model or DEFAULT_MODEL)

    cc = compiler.find_compiler()
    line(True if cc else None, "C kompilyatori (gcc/clang)",
         cc or "topilmadi — vosita ishlaydi, lekin natijalar tekshirilmaydi (⚪). docs/02_foydalanish.md, 1-bo'lim")
    print("\nStandart model:", llm.resolve_model(None), "(o'zgartirish: --model sonnet yoki .env da DEOBF_MODEL=sonnet)")
    print("\nNATIJA:", "hammasi tayyor ✅" if ok_all else "yuqoridagi ❌ belgili qatorlarni tuzating")
    return 0 if ok_all else 1


def cmd_web(args) -> int:
    import socket
    import threading
    import webbrowser

    from .web.app import create_app

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if sock.connect_ex((args.host, args.port)) == 0:
            print(f"XATO: {args.port}-port band (ehtimol Web UI allaqachon ishlab turibdi yoki boshqa dastur "
                  f"ishlatyapti). Brauzerda http://{args.host}:{args.port} ni ochib ko'ring yoki boshqa port "
                  f"tanlang: deobf web --port 5050", file=sys.stderr)
            return 1
    app = create_app()
    url = f"http://{args.host}:{args.port}"
    print("=" * 60, file=sys.stderr)
    print(f"  Web UI ishga tushdi:  {url}", file=sys.stderr)
    print("  Brauzerda shu manzilni oching (avtomatik ochilishi kerak).", file=sys.stderr)
    print("  DIQQAT: bu oynani YOPMANG — yopsangiz Web UI to'xtaydi.", file=sys.stderr)
    print("  To'xtatish: Ctrl+C", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    if not args.no_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    app.run(host=args.host, port=args.port, debug=False, threaded=True)
    return 0


def cmd_eval(args) -> int:
    from .evaluate import run_evaluation

    return run_evaluation(model=args.model, offline=args.offline, effort=args.effort,
                          output=args.output, quiet=args.quiet, source=args.source)


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
    w.add_argument("--no-browser", action="store_true", help="brauzerni avtomatik ochmaslik")
    w.set_defaults(func=cmd_web)

    c = sub.add_parser("check", help="diagnostika: o'rnatish, .env, API kalit, gcc")
    c.add_argument("-m", "--model", help="faqat shu modelni tekshirish (masalan, haiku)")
    c.add_argument("--no-network", action="store_true", help="Claude serveriga ulanmasdan tekshirish")
    c.set_defaults(func=cmd_check)

    e = sub.add_parser("eval", help="test namunalari bo'yicha baholash")
    e.add_argument("-m", "--model", help=f"model: {models}")
    e.add_argument("--offline", action="store_true")
    e.add_argument("--effort", default="medium", choices=["low", "medium", "high"])
    e.add_argument("--source", default="angr", help="psevdokod manbasi: samples/decompiled/<id>.<source>.c "
                   "(angr, ida, ghidra)")
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
