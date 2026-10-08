"""Web UI (Flask): brauzerda ishlaydigan oddiy interfeys.

Ishga tushirish:  deobf web        ->  http://127.0.0.1:5000 manzilini brauzerda oching.

Ikki rejim:
  * shaxsiy (standart) — faqat shu kompyuterdan (127.0.0.1) ochiladi, sizning .env dagi
    kalitingiz bilan ishlaydi. Kesh yoqilgan, cheklovlar yumshoq.
  * public (DEOBF_PUBLIC=1) — internetga chiqariladigan demo uchun. Server kalit saqlamaydi:
    Claude kerak bo'lsa, tashrif buyuruvchi O'Z kalitini kiritadi va u hech qayerda saqlanmaydi.
    Standart dvigatel — offline (bepul). Kirish hajmi, so'rovlar tezligi cheklanadi, disk kesh
    o'chiriladi, xavfsizlik sarlavhalari qo'shiladi. Batafsil: docs/04_internetga_chiqarish.md.
"""

from __future__ import annotations

import os
import time
import uuid
from collections import OrderedDict, defaultdict
from pathlib import Path

from flask import Flask, Response, abort, jsonify, render_template, request

from .. import llm, report, sandbox
from ..agent import AgentConfig, deobfuscate_text
from ..explain import TECH_NAMES_UZ

ROOT = Path(__file__).resolve().parents[2]
ENGINES = [
    ("offline", "Offline — bepul, LLM'siz (statik tahlil)"),
    ("haiku", "Claude Haiku 5.5 — arzon (~$0.001 / funksiya)"),
    ("sonnet", "Claude Sonnet 5.5 — o'rtacha (~$0.03 / funksiya)"),
    ("opus", "Claude Opus 5.5 — eng kuchli (~$0.05 / funksiya)"),
    ("custom", "Boshqa model (nomini o'zingiz yozasiz)"),
]
# Hisobot formatlari: nomi -> (chiqaruvchi funksiya, MIME turi)
FORMATS = {
    "md": (report.to_markdown, "text/markdown"),
    "html": (report.to_html, "text/html"),
    "json": (report.to_json, "application/json"),
}
# Shaxsiy va public rejim cheklovlari (public — begona odamlar uchun, shuning uchun qattiqroq)
LIMITS = {
    False: dict(max_chars=200_000, max_body=2 * 1024 * 1024, n_tests=2000, rate=None),
    True: dict(max_chars=20_000, max_body=256 * 1024, n_tests=600, rate=(15, 600)),  # 10 daqiqada 15 so'rov
}


def _load_samples() -> dict[str, str]:
    folder = ROOT / "samples" / "decompiled"
    if not folder.exists():
        return {}
    return {p.name.split(".")[0]: p.read_text(encoding="utf-8") for p in sorted(folder.glob("*.c"))}


class RateLimiter:
    """Oddiy, jarayon ichidagi IP bo'yicha tezlik cheklovchi (tashqi xizmatsiz)."""

    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self.hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str, now: float) -> bool:
        times = [t for t in self.hits[key] if now - t < self.window]
        times.append(now)
        self.hits[key] = times
        if len(self.hits) > 4096:                      # xotira o'smasligi uchun eski yozuvlarni tozalaymiz
            self.hits = {k: v for k, v in self.hits.items() if v and now - v[-1] < self.window}
        return len(times) <= self.limit


def create_app(test_config: dict | None = None) -> Flask:
    public = sandbox.PUBLIC
    limits = LIMITS[public]
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=limits["max_body"], PUBLIC=public,
                      CACHE_DIR=None if public else ".deobf_cache", CLIENT=None)
    if test_config:
        app.config.update(test_config)
    app.jinja_env.globals.update(report.TEMPLATE_GLOBALS)
    results: OrderedDict[str, tuple] = OrderedDict()     # oxirgi natijalar (yuklab olish uchun)
    samples = _load_samples()
    limiter = RateLimiter(*limits["rate"]) if limits["rate"] else None

    @app.after_request
    def security_headers(resp: Response) -> Response:
        if app.config["PUBLIC"]:
            resp.headers["X-Content-Type-Options"] = "nosniff"
            resp.headers["X-Frame-Options"] = "DENY"
            resp.headers["Referrer-Policy"] = "no-referrer"
            resp.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; "
                "base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
        return resp

    def page(**kw):
        defaults = dict(form={"code": "", "function": "", "engine": "offline" if public else "haiku",
                              "effort": "medium", "lang": "uz", "custom_model": ""},
                        engines=ENGINES, samples=samples, data=None, error=None, rid=None, public=public,
                        has_key=bool(os.environ.get("ANTHROPIC_API_KEY")))
        defaults.update(kw)
        return render_template("index.html", **defaults)

    @app.get("/")
    def index():
        return page()

    @app.post("/analyze")
    def analyze():
        if limiter is not None and not limiter.allow(request.remote_addr or "?", time.time()):
            return page(error="So'rovlar juda tez-tez yuborilyapti. Bir necha daqiqadan so'ng urinib ko'ring."), 429
        form = {k: request.form.get(k, "") for k in
                ("code", "function", "engine", "effort", "lang", "custom_model", "api_key")}
        upload = request.files.get("file")
        if upload and upload.filename:
            form["code"] = upload.read().decode("utf-8", errors="replace")
        if not form["code"].strip():
            return page(form=form, error="Psevdokod kiritilmadi.")
        if len(form["code"]) > limits["max_chars"]:
            return page(form=form, error=f"Matn juda uzun (maks. {limits['max_chars']:,} belgi) — "
                        "bitta yoki bir nechta funksiyani kiriting.")
        if public and _has_include(form["code"]):
            return page(form=form, error="Public demoda `#include` qatorlari qo'llab-quvvatlanmaydi — "
                        "faqat funksiyaning o'zini joylang (turlar avtomatik qo'shiladi).")
        engine = form["engine"] or ("offline" if public else "haiku")
        if engine == "custom":
            engine = form["custom_model"].strip()
            if not engine:
                return page(form=form, error="'Boshqa model' tanlangan, lekin model nomi yozilmagan "
                                             "(masalan: claude-sonnet-5-5).")
        offline = engine == "offline"
        api_key = form["api_key"].strip() or None
        if public and not offline and not api_key:
            return page(form=form, error="Claude modeli uchun o'z API kalitingizni kiriting "
                        "(sk-ant-...). Kalit saqlanmaydi. Yoki bepul Offline rejimni tanlang.")
        cfg = AgentConfig(model=None if offline else engine, offline=offline,
                          effort=form["effort"] or "medium", language=form["lang"] or "uz",
                          n_tests=limits["n_tests"], cache_dir=app.config["CACHE_DIR"],
                          api_key=api_key, client=app.config["CLIENT"])
        try:
            parsed, reps = deobfuscate_text(form["code"], cfg, function=form["function"].strip() or None)
        except ValueError as exc:
            return page(form=form, error=str(exc))
        rid = uuid.uuid4().hex[:12]
        results[rid] = (parsed, reps)
        while len(results) > 20:
            results.popitem(last=False)
        return page(form=form, data=report.to_data(parsed, reps), rid=rid)

    @app.post("/api/check-key")
    def check_key():
        """Kalit va tanlangan model ishlayotganini tekshiradi (Models API — bepul)."""
        model = (request.form.get("model") or "offline").strip()
        if model == "offline":
            return jsonify(ok=True, message="Offline rejim API kalitsiz ishlaydi.")
        api_key = (request.form.get("api_key") or "").strip() or None
        ok, message = llm.check_api_key(model, client=app.config["CLIENT"], api_key=api_key)
        return jsonify(ok=ok, message=message)

    @app.get("/download/<rid>.<fmt>")
    def download(rid: str, fmt: str):
        if rid not in results or fmt not in FORMATS:
            abort(404)
        render, mime = FORMATS[fmt]
        parsed, reps = results[rid]
        return Response(render(parsed, reps), mimetype=mime,
                        headers={"Content-Disposition": f"attachment; filename=deobf_{rid}.{fmt}"})

    return app


def _has_include(code: str) -> bool:
    return any(ln.lstrip().startswith(("#include", "#import")) for ln in code.splitlines())
