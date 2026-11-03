"""Web UI (Flask): brauzerda ishlaydigan oddiy interfeys.

Ishga tushirish:  deobf web        ->  http://127.0.0.1:5000 manzilini brauzerda oching.

Ikki rejim:
  * shaxsiy (standart) — faqat shu kompyuterdan (127.0.0.1) ochiladi, sizning .env dagi kalitingiz bilan ishlaydi.
    Brauzerdagi boshqa saytlar (CSRF / DNS rebinding) uni chaqira olmasligi uchun Host va Origin tekshiriladi.
  * public (DEOBF_PUBLIC=1) — internetga chiqariladigan demo uchun. Server kalit saqlamaydi: Claude kerak bo'lsa,
    tashrif buyuruvchi O'Z kalitini kiritadi va u hech qayerda saqlanmaydi. Standart dvigatel — offline (bepul).
    Tashrif buyuruvchining kodi serverda kompilyatsiya qilinmaydi va ishga tushirilmaydi (sandbox.native_allowed).
    Kirish hajmi, funksiyalar soni, vaqt va so'rovlar tezligi cheklanadi, disk kesh o'chiriladi.
    Batafsil: docs/04_internetga_chiqarish.md.
"""

from __future__ import annotations

import os
import threading
import time
import uuid
from collections import OrderedDict
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, Response, abort, jsonify, render_template, request

from .. import llm, report, sandbox
from ..agent import AgentConfig, deobfuscate_text

ROOT = Path(__file__).resolve().parents[2]
ENGINES = [
    ("sonnet", "Claude Sonnet 5.5 (tavsiya) — taxminan $0.03–0.07 / funksiya"),
    ("haiku", "Claude Haiku 5.5 — arzonroq, taxminan $0.002–0.005"),
    ("opus", "Claude Opus 5.5 — eng kuchli, taxminan $0.06–0.15"),
    ("offline", "Offline — bepul, Claude'siz"),
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
    False: dict(max_chars=200_000, max_body=2 * 1024 * 1024, n_tests=2000, max_funcs=None, time_limit=None,
                analyze_rate=None, key_rate=None, slots=4),
    True: dict(max_chars=20_000, max_body=256 * 1024, n_tests=600, max_funcs=3, time_limit=90,
               analyze_rate=(15, 600), key_rate=(6, 600), slots=2),       # 10 daqiqada 15 tahlil / 6 kalit tekshiruvi
}
LOCAL_HOSTS = {"127.0.0.1", "localhost", "[::1]", "::1"}


def _load_samples() -> dict[str, str]:
    folder = ROOT / "samples" / "decompiled"
    if not folder.exists():
        return {}
    return {p.name.split(".")[0]: p.read_text(encoding="utf-8") for p in sorted(folder.glob("*.c"))}


class RateLimiter:
    """Oddiy, jarayon ichidagi tezlik cheklovchi (tashqi xizmatsiz). Rad etilgan urinish oynani uzaytirmaydi."""

    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self.hits: dict[str, list[float]] = {}
        self.lock = threading.Lock()

    def allow(self, key: str, now: float) -> bool:
        with self.lock:
            times = [t for t in self.hits.get(key, []) if now - t < self.window]
            ok = len(times) < self.limit
            if ok:
                times.append(now)
            self.hits[key] = times
            if len(self.hits) > 4096:                      # xotira o'smasligi uchun eskirgan yozuvlarni tozalaymiz
                self.hits = {k: v for k, v in self.hits.items() if v and now - v[-1] < self.window}
            return ok


def _has_include(code: str) -> bool:
    """`#include` (va `# include`, `%:include`) qatorlari bormi? Public demoda taqiqlanadi."""
    import re

    return bool(re.search(r"^\s*(?:#|%:)\s*(?:include|import|embed)\b", code, flags=re.M))


def create_app(test_config: dict | None = None) -> Flask:
    public = sandbox.PUBLIC
    limits = LIMITS[public]
    app = Flask(__name__)
    app.config.update(MAX_CONTENT_LENGTH=limits["max_body"], PUBLIC=public, LOCAL_ONLY=True,
                      CACHE_DIR=None if public else ".deobf_cache", CLIENT=None)
    if test_config:
        app.config.update(test_config)
    # Render kabi proksi orqasida haqiqiy mijoz IP'si kerak: ishonchli proksilar soni DEOBF_TRUSTED_PROXIES (standart 0)
    proxies = int(os.environ.get("DEOBF_TRUSTED_PROXIES", "0") or 0)
    if proxies > 0:
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxies, x_proto=1, x_host=0)
    app.jinja_env.globals.update(report.TEMPLATE_GLOBALS)
    app.jinja_env.filters["rich"] = report.rich
    results: OrderedDict[str, tuple] = OrderedDict()     # oxirgi natijalar (yuklab olish uchun)
    samples = _load_samples()
    analyze_limiter = RateLimiter(*limits["analyze_rate"]) if limits["analyze_rate"] else None
    key_limiter = RateLimiter(*limits["key_rate"]) if limits["key_rate"] else None
    slots = threading.BoundedSemaphore(limits["slots"])  # bir vaqtda ishlaydigan tahlillar soni

    @app.before_request
    def guard():
        """CSRF / DNS rebinding himoyasi: boshqa sayt bu serverga so'rov yubora olmaydi."""
        if request.method == "POST":
            origin = request.headers.get("Origin")
            if origin and urlparse(origin).netloc != request.host:        # "null" ham rad etiladi
                abort(403)
            if request.headers.get("Sec-Fetch-Site") == "cross-site":
                abort(403)
        if app.config["LOCAL_ONLY"] and not app.config["PUBLIC"] and request.host.rsplit(":", 1)[0] not in LOCAL_HOSTS \
                and request.host not in LOCAL_HOSTS:
            abort(403)

    @app.after_request
    def security_headers(resp: Response) -> Response:
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        # same-origin: boshqa saytga hech narsa yuborilmaydi, lekin o'z saytimizdagi formalar to'g'ri `Origin` yuboradi
        # (no-referrer bilan brauzer `Origin: null` yuboradi va Origin tekshiruvi oddiy so'rovlarni ham rad etar edi)
        resp.headers["Referrer-Policy"] = "same-origin"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
        if app.config["PUBLIC"] and request.is_secure:
            resp.headers["Strict-Transport-Security"] = "max-age=31536000"
        return resp

    def page(status: int = 200, **kw):
        defaults = dict(form={"code": "", "function": "", "engine": "offline" if public else "sonnet",
                              "effort": "medium", "lang": "uz", "custom_model": ""},
                        engines=ENGINES, samples=samples, data=None, error=None, rid=None, public=public,
                        native=sandbox.native_allowed(), has_key=bool(os.environ.get("ANTHROPIC_API_KEY")))
        defaults.update(kw)
        return render_template("index.html", **defaults), status

    @app.get("/")
    def index():
        return page()

    @app.post("/analyze")
    def analyze():
        form = {k: request.form.get(k, "") for k in
                ("code", "function", "engine", "effort", "lang", "custom_model", "api_key")}
        upload = request.files.get("file")
        if upload and upload.filename:
            form["code"] = upload.read().decode("utf-8", errors="replace")
        shown = {k: v for k, v in form.items() if k != "api_key"}          # kalit formaga qaytarilmaydi
        if not form["code"].strip():
            return page(form=shown, error="Psevdokod kiritilmadi.")
        if len(form["code"]) > limits["max_chars"]:
            return page(form=shown, error=f"Matn juda uzun (ko'pi bilan {limits['max_chars']:,} belgi) — "
                        "bitta yoki bir nechta funksiyani kiriting.")
        if public and _has_include(form["code"]):
            return page(form=shown, error="Public demoda `#include` qatorlari qo'llab-quvvatlanmaydi — "
                        "faqat funksiyaning o'zini joylang (turlar avtomatik qo'shiladi).")
        engine = form["engine"] or ("offline" if public else "sonnet")
        if engine == "custom":
            engine = form["custom_model"].strip()
            if not engine:
                return page(form=shown, error="'Boshqa model' tanlangan, lekin model nomi yozilmagan "
                                              "(masalan: claude-sonnet-5-5).")
        offline = engine == "offline"
        api_key = form["api_key"].strip() or None
        if public and not offline and not api_key:
            return page(form=shown, error="Claude modeli uchun o'z API kalitingizni kiriting "
                        "(sk-ant-...). Kalit saqlanmaydi. Yoki bepul Offline rejimni tanlang.")
        if analyze_limiter is not None and not analyze_limiter.allow(request.remote_addr or "?", time.time()):
            resp, _ = page(form=shown, error="So'rovlar juda tez-tez yuborilyapti. Bir necha daqiqadan so'ng urinib ko'ring.")
            return Response(resp, status=429, headers={"Retry-After": "120"})
        if not slots.acquire(blocking=False):
            return page(503, form=shown, error="Server hozir band (boshqa tahlillar ishlayapti). Birozdan so'ng qayta urinib ko'ring.")
        try:
            cfg = AgentConfig(model=None if offline else engine, offline=offline,
                              effort=form["effort"] or "medium", language=form["lang"] or "uz",
                              n_tests=limits["n_tests"], cache_dir=app.config["CACHE_DIR"],
                              api_key=api_key, client=app.config["CLIENT"],
                              max_functions=limits["max_funcs"], time_limit_sec=limits["time_limit"])
            try:
                parsed, reps = deobfuscate_text(form["code"], cfg, function=form["function"].strip() or None)
            except ValueError as exc:
                return page(form=shown, error=str(exc))
            except Exception:                                  # kutilmagan xato: izni logda, foydalanuvchiga — tushunarli matn
                app.logger.exception("tahlil muvaffaqiyatsiz")
                return page(500, form=shown, error="Bu kodni tahlil qilib bo'lmadi (kutilmagan xato). Kodni qisqartirib "
                            "yoki boshqa funksiyani tanlab ko'ring.")
        finally:
            slots.release()
        rid = uuid.uuid4().hex[:12]
        results[rid] = (parsed, reps)
        while len(results) > 20:
            results.popitem(last=False)
        return page(form=shown, data=report.to_data(parsed, reps), rid=rid)

    @app.post("/api/check-key")
    def check_key():
        """Kalit va tanlangan model ishlayotganini tekshiradi (Models API — bepul)."""
        model = (request.form.get("model") or "offline").strip()[:100]
        if model == "offline":
            return jsonify(ok=True, message="Offline rejim API kalitsiz ishlaydi.")
        if key_limiter is not None and not key_limiter.allow(request.remote_addr or "?", time.time()):
            return jsonify(ok=False, message="Juda ko'p tekshiruv. Bir necha daqiqadan so'ng urinib ko'ring."), 429
        api_key = (request.form.get("api_key") or "").strip()[:300] or None
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

    @app.errorhandler(413)
    def too_large(_):
        return page(413, error="Yuborilgan hajm juda katta. Bitta yoki bir nechta funksiyani kiriting.")

    @app.errorhandler(404)
    def not_found(_):
        return page(404, error="Sahifa yoki hisobot topilmadi (hisobotlar server qayta ishga tushganda o'chib ketadi).")

    @app.errorhandler(403)
    def forbidden(_):
        return Response("Taqiqlangan so'rov.", status=403, mimetype="text/plain")

    return app
