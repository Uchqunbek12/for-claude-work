"""Web UI (Flask): brauzerda ishlaydigan oddiy interfeys.

Ishga tushirish:  deobf web        ->  http://127.0.0.1:5000 manzilini brauzerda oching.

Xavfsizlik: server standart holatda faqat shu kompyuterdan (127.0.0.1) ochiladi,
chunki u sizning API kalitingiz bilan ishlaydi. Uni internetga ochmang.
"""

from __future__ import annotations

import json
import os
import uuid
from collections import OrderedDict
from pathlib import Path

from flask import Flask, Response, abort, jsonify, render_template, request

from .. import llm, report
from ..agent import AgentConfig, deobfuscate_text
from ..offline import TECH_NAMES_UZ

ROOT = Path(__file__).resolve().parents[2]
ENGINES = [
    ("haiku", "Claude Haiku 5.5 — arzon, standart (~$0.001 / funksiya)"),
    ("sonnet", "Claude Sonnet 5.5 — o'rtacha (~$0.03 / funksiya)"),
    ("opus", "Claude Opus 5.5 — eng kuchli (~$0.05 / funksiya)"),
    ("offline", "Offline — bepul, LLM'siz"),
    ("custom", "Boshqa model (nomini o'zingiz yozasiz)"),
]
MAX_INPUT_CHARS = 200_000


def _load_samples() -> dict[str, str]:
    folder = ROOT / "samples" / "decompiled"
    if not folder.exists():
        return {}
    return {p.name.split(".")[0]: p.read_text(encoding="utf-8") for p in sorted(folder.glob("*.c"))}


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=2 * 1024 * 1024, CACHE_DIR=".deobf_cache", CLIENT=None)
    if test_config:
        app.config.update(test_config)
    app.jinja_env.globals.update(tech_names=TECH_NAMES_UZ, style_names=report.STYLE_NAMES,
                                 confidence_uz=report.CONFIDENCE_UZ)
    results: OrderedDict[str, tuple] = OrderedDict()     # oxirgi natijalar (yuklab olish uchun)
    samples = _load_samples()

    def page(**kw):
        defaults = dict(form={"code": "", "function": "", "engine": "haiku", "effort": "medium", "lang": "uz",
                              "custom_model": ""},
                        engines=ENGINES, samples=samples, data=None, error=None, rid=None,
                        has_key=bool(os.environ.get("ANTHROPIC_API_KEY")))
        defaults.update(kw)
        return render_template("index.html", **defaults)

    @app.get("/")
    def index():
        return page()

    @app.post("/analyze")
    def analyze():
        form = {k: request.form.get(k, "") for k in ("code", "function", "engine", "effort", "lang", "custom_model")}
        upload = request.files.get("file")
        if upload and upload.filename:
            form["code"] = upload.read().decode("utf-8", errors="replace")
        if not form["code"].strip():
            return page(form=form, error="Psevdokod kiritilmadi.")
        if len(form["code"]) > MAX_INPUT_CHARS:
            return page(form=form, error="Matn juda uzun — bitta yoki bir nechta funksiyani kiriting.")
        engine = form["engine"] or "haiku"
        if engine == "custom":
            engine = form["custom_model"].strip()
            if not engine:
                return page(form=form, error="'Boshqa model' tanlangan, lekin model nomi yozilmagan "
                                             "(masalan: claude-sonnet-5-5).")
        cfg = AgentConfig(model=None if engine == "offline" else engine, offline=engine == "offline",
                          effort=form["effort"] or "medium", language=form["lang"] or "uz",
                          cache_dir=app.config["CACHE_DIR"], client=app.config["CLIENT"])
        try:
            parsed, reps = deobfuscate_text(form["code"], cfg, function=form["function"].strip() or None)
        except ValueError as exc:
            return page(form=form, error=str(exc))
        rid = uuid.uuid4().hex[:12]
        results[rid] = (parsed, reps)
        while len(results) > 20:
            results.popitem(last=False)
        data = json.loads(report.to_json(parsed, reps))
        return page(form=form, data=data, rid=rid)

    @app.post("/api/check-key")
    def check_key():
        """Kalit va tanlangan model ishlayotganini tekshiradi (Models API — bepul)."""
        model = (request.form.get("model") or "haiku").strip()
        if model == "offline":
            return jsonify(ok=True, message="Offline rejim API kalitsiz ishlaydi.")
        ok, message = llm.check_api_key(model, client=app.config["CLIENT"])
        return jsonify(ok=ok, message=message)

    @app.get("/download/<rid>.<fmt>")
    def download(rid: str, fmt: str):
        if rid not in results:
            abort(404)
        parsed, reps = results[rid]
        if fmt == "md":
            return Response(report.to_markdown(parsed, reps), mimetype="text/markdown",
                            headers={"Content-Disposition": f"attachment; filename=deobf_{rid}.md"})
        if fmt == "html":
            return Response(report.to_html(parsed, reps), mimetype="text/html",
                            headers={"Content-Disposition": f"attachment; filename=deobf_{rid}.html"})
        if fmt == "json":
            return Response(report.to_json(parsed, reps), mimetype="application/json",
                            headers={"Content-Disposition": f"attachment; filename=deobf_{rid}.json"})
        abort(404)

    return app
