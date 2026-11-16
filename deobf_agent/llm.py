"""LLM bilan ishlash (Claude va DeepSeek): model tanlash, so'rov yuborish, narx hisoblash, kesh.

Ikki provayder bor: Anthropic (Claude: sonnet, haiku, opus) va DeepSeek (deepseek, deepseek-pro). Provayder model nomidan
aniqlanadi (`provider_of`): "deepseek" bilan boshlansa — DeepSeek, aks holda — Claude. Kalitlar: ANTHROPIC_API_KEY va
DEEPSEEK_API_KEY. Agent va tekshiruv provayderga bog'liq emas: ikkalasi ham bir xil `DeobfResult` qaytaradi.

Asosiy tushunchalar:
  * token — model matnni o'qiydigan va yozadigan "bo'lak" (taxminan 3-4 harf).
    API narxi tokenlar soniga qarab hisoblanadi: kirish (input) va chiqish (output) alohida.
  * model — default "sonnet" (Claude Sonnet 5.5: kuchli va o'rtacha narxda). --model haiku bilan arzonroq,
    --model opus bilan kuchliroq modelga bir zumda o'tish mumkin.
  * effort — modelning "o'ylash" chuqurligi (low / medium / high). Pastroq = arzonroq va tezroq.
  * structured output — javob aniq sxema (schema.DeobfResult) bo'yicha keladi (Claude: sxema majburiy; DeepSeek: JSON rejimi
    + sxema prompt ichida, javob pydantic bilan tekshiriladi).
  * prompt caching — bir suhbatning davomida (tuzatish urinishlarida) so'rovning boshlang'ich qismi
    API serverida keshlanadi va ~10 barobar arzon hisoblanadi.
  * disk kesh — bir xil kod uchun bir xil so'rovni qayta yubormaymiz: javob diskdan olinadi ($0).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import sandbox
from .deepseek import DeepSeekClient, DeepSeekError
from .prompts import SYSTEM_PROMPT
from .schema import DeobfResult

MODEL_ALIASES = {
    "haiku": "claude-haiku-5-5",
    "sonnet": "claude-sonnet-5-5",
    "opus": "claude-opus-5-5",
    "deepseek": "deepseek-flash",          # arzon va tez (rasmiy hujjatda tavsiya etilgan model nomi)
    "deepseek-pro": "deepseek-v4-pro",     # kuchliroq va qimmatroq
}
DEFAULT_MODEL = "sonnet"                   # hech qanday kalit topilmasa; DeepSeek kaliti bo'lsa — default_alias()

# Provayderlar va ularning kalit o'zgaruvchilari (muhitda yoki .env faylida).
KEY_ENV = {"anthropic": "ANTHROPIC_API_KEY", "deepseek": "DEEPSEEK_API_KEY"}
PROVIDERS = tuple(KEY_ENV)

# Narxlar: AQSH dollari / 1 million token. (kirish, chiqish, kesh-yozish, kesh-o'qish)
# Taxminiy qiymatlar — aniq va eng so'nggi narxlar: https://www.anthropic.com/pricing
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50, 0.125, 0.01),
    "claude-sonnet-5-5": (2.00, 10.00, 2.50, 0.20),
    "claude-opus-5-5": (4.00, 20.00, 5.00, 0.20),
    # DeepSeek (https://api-docs.deepseek.com/quick_start/pricing): kesh-yozish alohida haq olinmaydi (= kirish narxi).
    # Band soatlarda (UTC 01-04 va 06-10, du-ju) narx 2 barobar, boshqa vaqtda yarmi: bu yerda BAND narx (ehtiyot uchun).
    "deepseek-flash": (0.30, 1.20, 0.30, 0.006),
    "deepseek-v4-pro": (1.32, 3.96, 1.32, 0.044),
}

EFFORTS = ("low", "medium", "high")
LANGUAGES = ("uz", "ru", "en")


class LLMError(Exception):
    """LLM bilan bog'liq xato (foydalanuvchiga tushunarli matn bilan)."""


def provider_of(model_id: str) -> str:
    """Model nomidan provayderni aniqlaydi: 'deepseek...' — DeepSeek, qolgani — Anthropic (Claude)."""
    return "deepseek" if model_id.strip().lower().startswith("deepseek") else "anthropic"


def default_alias() -> str:
    """Standart model: muhitda DeepSeek kaliti bo'lsa — DeepSeek, bo'lmasa — Claude Sonnet."""
    return "deepseek" if server_api_key("deepseek") else DEFAULT_MODEL


def resolve_model(name: str | None) -> str:
    """'haiku' -> 'claude-haiku-5-5', 'deepseek' -> 'deepseek-flash'. To'liq model nomi berilsa, o'zgarishsiz qaytariladi.
    Nom berilmasa: DEOBF_MODEL, u ham yo'q bo'lsa — default_alias()."""
    name = (name or os.environ.get("DEOBF_MODEL") or default_alias()).strip()
    return MODEL_ALIASES.get(name.lower(), name)


def _price(model: str) -> tuple[float, float, float, float]:
    if model in PRICES:
        return PRICES[model]
    if provider_of(model) == "deepseek":              # noma'lum DeepSeek modeli: nomida "flash" bo'lsa arzon narx, aks holda ehtiyotkor (pro)
        return PRICES["deepseek-flash" if "flash" in model.lower() else "deepseek-v4-pro"]
    return PRICES["claude-opus-5-5"]


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOTENV_INFO: dict = {"path": None, "keys": []}     # qaysi .env fayli o'qilgani (diagnostika uchun)


def _decode_text_file(data: bytes) -> str:
    """Faylni kodlashidan qat'i nazar o'qiydi.

    Windows'da .env turli yo'llar bilan yaratiladi: PowerShell'dagi `echo ... > .env`
    UTF-16 kodlashda yozadi, Notepad esa ba'zan UTF-8 ni BOM belgisi bilan saqlaydi.
    Shuning uchun kodlashni faylning birinchi baytlariga qarab aniqlaymiz.
    """
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig")
    if b"\x00" in data:                         # BOM'siz UTF-16
        return data.decode("utf-16-le", errors="replace").replace("\x00", "")
    return data.decode("utf-8", errors="replace")


def find_dotenv() -> Path | None:
    """`.env` faylini qidiradi: joriy papka, so'ng loyiha papkasi.

    Notepad fayl nomiga ko'rinmas `.txt` qo'shib qo'yishi mumkin (`.env.txt`) —
    bunday faylni ham qabul qilamiz.
    """
    for folder in (Path.cwd(), PROJECT_ROOT):
        for name in (".env", ".env.txt", "env.txt"):
            p = folder / name
            if p.is_file():
                return p
    return None


def load_dotenv(path: Path | None = None) -> Path | None:
    """.env faylidan ANTHROPIC_API_KEY=... kabi qatorlarni o'qiydi (agar hali o'rnatilmagan bo'lsa).

    API kalitni kod ichida yozish xavfli (u GitHub'ga tushib qolishi mumkin), shuning
    uchun u .env faylida saqlanadi, .env esa .gitignore ro'yxatida.
    Hech qachon xato bilan to'xtamaydi — muammo bo'lsa `deobf check` buni ko'rsatadi.
    """
    path = path if path is not None else find_dotenv()
    if path is None or not path.is_file():
        return None
    try:
        text = _decode_text_file(path.read_bytes())
    except OSError:
        return None
    keys = []
    for line in text.splitlines():
        line = line.strip().lstrip("\ufeff")
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith(("export ", "set ")):          # "set X=Y" / "export X=Y"
            line = line.split(" ", 1)[1].strip()
        if "=" not in line:
            if line.startswith("sk-ant-"):                          # faqat kalitning o'zi yozilgan
                os.environ.setdefault("ANTHROPIC_API_KEY", line)
                keys.append("ANTHROPIC_API_KEY")
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'").strip()
        if key:
            os.environ.setdefault(key, value)
            keys.append(key)
    DOTENV_INFO.update(path=path, keys=keys)
    return path


def mask_key(key: str | None) -> str:
    """Kalitni xavfsiz ko'rsatish: sk-ant-api03...a1b2 (Claude: boshi doimiy prefiks) yoki sk-a1...b2c3 (DeepSeek: "sk-"dan
    keyingi belgilar tasodifiy, shuning uchun faqat 2 tasi ko'rsatiladi)."""
    if not key:
        return "(yo'q)"
    head = 12 if key.startswith("sk-ant-") else 5
    return key[:head] + "..." + key[-4:] if len(key) > 20 else "***"


_KEY_RES = {"anthropic": re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"), "deepseek": re.compile(r"sk-[A-Za-z0-9_\-]{20,}")}
_KEY_RE = _KEY_RES["anthropic"]          # eski nom (testlar va tashqi kod uchun)
_KEY_HELP = {"anthropic": "'sk-ant-...'", "deepseek": "'sk-...'"}


def _key_ok(provider: str, key: str) -> bool:
    """Kalit shakli to'g'rimi (faqat shakl: kalit ishlashini API tekshiradi). DeepSeek kaliti 'sk-ant-' bilan boshlanmaydi."""
    if provider == "deepseek" and key.startswith("sk-ant-"):
        return False
    return bool(_KEY_RES[provider].fullmatch(key))


def _server_key_allowed(api_key: str | None) -> bool:
    """Public rejimda server kalitiga (.env / muhit) tushib ketmaymiz — faqat tashrif buyuruvchining kaliti. Istisno:
    operator DEOBF_USE_SERVER_KEY=1 qo'ygan (u faqat kirish kodi bilan birga ishlaydi: app.create_app tekshiradi)."""
    return bool(api_key) or not sandbox.PUBLIC or sandbox.USE_SERVER_KEY


def _api_error_text(exc: Exception, model_id: str, key: str = "") -> str:
    """Claude API xatosini foydalanuvchiga tushunarli o'zbekcha matnga aylantiradi."""
    import anthropic

    if isinstance(exc, anthropic.AuthenticationError):
        return (f"Kalit noto'g'ri yoki bekor qilingan ({mask_key(key)}). "
                "console.anthropic.com da yangi kalit yarating.")
    if isinstance(exc, anthropic.PermissionDeniedError):
        return f"Kalitga ruxsat yo'q: {exc.message}"
    if isinstance(exc, anthropic.NotFoundError):
        return f"'{model_id}' modeli topilmadi yoki sizga mavjud emas. Boshqa modelni tanlang (sonnet, haiku, opus)."
    if isinstance(exc, anthropic.RateLimitError):
        return "So'rovlar limiti oshib ketdi (rate limit). Bir oz kutib, qayta urinib ko'ring."
    if isinstance(exc, anthropic.BadRequestError):
        return f"So'rov rad etildi (400): {exc.message}"
    if isinstance(exc, anthropic.APIStatusError):
        body = exc.body.get("error") if isinstance(getattr(exc, "body", None), dict) else None
        detail = (body or {}).get("message") if isinstance(body, dict) else None
        return f"Claude API xatosi ({exc.status_code}): {detail or exc.message}"
    if isinstance(exc, anthropic.APITimeoutError):
        return "Claude serveri javob bermadi (vaqt tugadi). Birozdan so'ng qayta urinib ko'ring."
    if isinstance(exc, anthropic.APIConnectionError):
        return "Claude serveriga ulanib bo'lmadi — internet aloqasini tekshiring."
    return f"Claude API xatosi: {exc}"


def _deepseek_error_text(exc: DeepSeekError, model_id: str, key: str = "") -> str:
    """DeepSeek xatosini (HTTP kodi bo'yicha, rasmiy xatolar jadvali) tushunarli o'zbekcha matnga aylantiradi."""
    if exc.timeout:
        return "DeepSeek serveri javob bermadi (vaqt tugadi). Birozdan so'ng qayta urinib ko'ring."
    if exc.status == 0:
        return "DeepSeek serveriga ulanib bo'lmadi — internet aloqasini tekshiring."
    if exc.status == 401:
        return f"Kalit noto'g'ri yoki bekor qilingan ({mask_key(key)}). platform.deepseek.com da yangi kalit yarating."
    if exc.status == 402:
        return "DeepSeek hisobida mablag' tugagan (402). platform.deepseek.com da hisobni to'ldiring."
    if exc.status in (400, 422):
        return f"So'rov rad etildi ({exc.status}): {exc.message}"
    if exc.status == 404:
        return f"'{model_id}' modeli topilmadi. Boshqa modelni tanlang (deepseek, deepseek-pro)."
    if exc.status == 429:
        return "So'rovlar limiti oshib ketdi (rate limit). Bir oz kutib, qayta urinib ko'ring."
    if exc.status in (500, 503):
        return f"DeepSeek serveri band yoki xato berdi ({exc.status}). Birozdan so'ng qayta urinib ko'ring."
    return f"DeepSeek API xatosi ({exc.status}): {exc.message}"


def key_provider(key: str) -> str | None:
    """Kalitning o'zidan provayderni aniqlaydi: Claude kaliti 'sk-ant-' bilan boshlanadi, DeepSeek kaliti — boshqa 'sk-...'."""
    if key.startswith("sk-ant-"):
        return "anthropic"
    return "deepseek" if key.startswith("sk-") else None


def _env_keys() -> dict[str, str]:
    """Muhitdagi kalitlar (provayder -> kalit). Nusxalashda qo'shilib qoladigan bo'shliq, yangi qator va tirnoqlar olib
    tashlanadi. Kalit NOTO'G'RI nomli o'zgaruvchiga yozilgan bo'lsa (masalan, DeepSeek kaliti ANTHROPIC_API_KEY ichida),
    u shakliga qarab to'g'ri provayderga o'tkaziladi: foydalanuvchi nom adashgani uchun ishsiz qolmasin."""
    raw = {p: os.environ.get(KEY_ENV[p], "").strip().strip("'\"").strip() for p in PROVIDERS}
    keys = dict(raw)
    for p, key in raw.items():
        right = key_provider(key) if key else None
        if right and right != p and not raw[right]:
            keys[right], keys[p] = key, ""
    return keys


def key_mixups() -> list[tuple[str, str]]:
    """[(o'zgaruvchi nomi, bo'lishi kerak bo'lgan nom)]: kalit noto'g'ri nomli o'zgaruvchida turgan holatlar (sahifada ogohlantirish uchun)."""
    keys = _env_keys()
    return [(KEY_ENV[p], KEY_ENV[q]) for p in PROVIDERS for q in PROVIDERS
            if p != q and os.environ.get(KEY_ENV[p], "").strip() and not keys[p] and keys[q]
            and not os.environ.get(KEY_ENV[q], "").strip()]


def server_api_key(provider: str = "anthropic") -> str:
    """Muhit o'zgaruvchisidagi (Render, .env) kalit: ANTHROPIC_API_KEY yoki DEEPSEEK_API_KEY (noto'g'ri nomda turgan kalit ham
    shakliga qarab topiladi: `_env_keys`)."""
    return _env_keys()[provider]


def any_server_key() -> bool:
    return any(server_api_key(p) for p in PROVIDERS)


def _llm_timeout() -> float:
    """DeepSeek bitta so'rovi uchun kutish chegarasi (soniya). Veb-sayt vaqt byudjetiga sig'ishi uchun standart 90; o'z
    kompyuteringizda sekin (o'ylash yoqilgan Pro) so'rovlar uchun DEOBF_LLM_TIMEOUT=200 kabi oshirish mumkin."""
    try:
        return max(10.0, float(os.environ.get("DEOBF_LLM_TIMEOUT", "90")))
    except ValueError:
        return 90.0


def make_client(api_key: str | None = None, provider: str = "anthropic"):
    """Provayder mijozini yaratadi. api_key berilmasa — ANTHROPIC_API_KEY / DEEPSEEK_API_KEY (yoki .env) dan olinadi
    (public rejimda esa kalit majburiy: server kaliti ishlatilmaydi)."""
    name = "DeepSeek" if provider == "deepseek" else "Claude"
    if not _server_key_allowed(api_key):
        raise LLMError(f"{name} uchun o'z API kalitingizni kiriting ({_KEY_HELP[provider][1:-1]}).")
    if api_key and not _key_ok(provider, api_key):
        raise LLMError(f"API kalit formati noto'g'ri — {_KEY_HELP[provider]} bilan boshlanadigan to'liq {name} kalitini kiriting.")
    key = api_key or server_api_key(provider)
    if provider == "deepseek":
        if not key:
            raise LLMError("DEEPSEEK_API_KEY topilmadi: uni .env fayliga yozing (Render'da — Environment) yoki --offline rejimidan foydalaning.")
        return DeepSeekClient(key, timeout=_llm_timeout())
    import anthropic

    return anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()


def check_api_key(model: str | None = None, client=None, api_key: str | None = None) -> tuple[bool, str]:
    """Kalit va model ishlayotganini tekshiradi.

    Models API (`models.retrieve`) chaqiriladi — bu matn generatsiya qilmaydi va BEPUL.
    Natija: (muvaffaqiyat, o'zbekcha xabar).
    """
    import anthropic

    model_id = resolve_model(model)
    provider = provider_of(model_id)
    if not _server_key_allowed(api_key):
        return False, f"Kalitni tekshirish uchun o'z API kalitingizni kiriting ({_KEY_HELP[provider][1:-1]})."
    key = api_key or server_api_key(provider)
    if client is None:
        if not key:
            return False, (f"{KEY_ENV[provider]} topilmadi. Loyiha papkasida .env fayli yarating va unga "
                           f"{KEY_ENV[provider]}={_KEY_HELP[provider][1:-1]} qatorini yozing.")
        if not _key_ok(provider, key):
            return False, (f"Kalit formati noto'g'ri ({mask_key(key)}): {_KEY_HELP[provider]} bilan boshlanib, to'liq "
                           "nusxalanganini tekshiring.")
    if provider == "deepseek":
        try:
            names = (client or make_client(api_key, provider)).models()
        except LLMError as exc:
            return False, str(exc)
        except DeepSeekError as exc:
            return False, _deepseek_error_text(exc, model_id, key)
        if model_id not in names:
            return False, f"Kalit ishlayapti, lekin '{model_id}' modeli ro'yxatda yo'q. Mavjud modellar: {', '.join(names) or '(bo`sh)'}."
        return True, f"Kalit ishlayapti — model mavjud: {model_id}"
    try:
        info = (client or make_client(api_key)).models.retrieve(model_id)
    except LLMError as exc:
        return False, str(exc)
    except anthropic.AnthropicError as exc:
        return False, _api_error_text(exc, model_id, key)
    name = getattr(info, "display_name", None) or model_id
    return True, f"Kalit ishlayapti — model mavjud: {name} ({model_id})"


@dataclass
class UsageStats:
    """Token sarfi va narx (bir nechta so'rov bo'yicha yig'indisi)."""

    requests: int = 0
    cache_hits: int = 0              # diskdagi keshdan olingan javoblar ($0)
    input_tokens: int = 0
    output_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    cost_usd: float = 0.0

    def add_deepseek(self, usage: dict, model: str) -> None:
        """DeepSeek `usage` lug'atidan: kesh-miss (to'liq narx), kesh-hit (juda arzon) va chiqish tokenlari."""
        def num(key):
            v = usage.get(key)
            return v if isinstance(v, int) and v > 0 else 0

        p_in, p_out, _, p_cr = _price(model)
        hit = num("prompt_cache_hit_tokens")
        miss = usage.get("prompt_cache_miss_tokens")
        miss = miss if isinstance(miss, int) and miss >= 0 else max(num("prompt_tokens") - hit, 0)
        out = num("completion_tokens")
        self.requests += 1
        self.input_tokens += miss
        self.output_tokens += out
        self.cache_read_tokens += hit
        self.cost_usd += (miss * p_in + out * p_out + hit * p_cr) / 1_000_000

    def add_response(self, usage, model: str) -> None:
        p_in, p_out, p_cw, p_cr = _price(model)
        cw = getattr(usage, "cache_creation_input_tokens", 0) or 0
        cr = getattr(usage, "cache_read_input_tokens", 0) or 0
        self.requests += 1
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens
        self.cache_write_tokens += cw
        self.cache_read_tokens += cr
        self.cost_usd += (usage.input_tokens * p_in + usage.output_tokens * p_out
                          + cw * p_cw + cr * p_cr) / 1_000_000

    def to_dict(self) -> dict:
        d = asdict(self)
        d["cost_usd"] = round(self.cost_usd, 6)
        return d


class DiskCache:
    """Oddiy fayl keshi: har bir javob alohida JSON faylda, nomi — so'rovning SHA-256 xeshi."""

    def __init__(self, directory: Path | str = ".deobf_cache"):
        self.dir = Path(directory)

    def _path(self, key: str) -> Path:
        return self.dir / f"{key}.json"

    def get(self, key: str) -> dict | None:
        p = self._path(key)
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return None
        return None

    def set(self, key: str, value: dict) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self._path(key).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


# DeepSeek JSON rejimi sxemani majburlay olmaydi: hujjat bo'yicha prompt'da "json" so'zi va javob shaklining namunasi bo'lishi
# kerak. Sxema (DeobfResult) shu yerga qo'shiladi, javob esa pydantic bilan tekshiriladi.
_JSON_EXAMPLE = ('{"function_name":"f","suggested_name":"f_clean","summary":"...","simple_summary":"...","techniques":["mba"],'
                 '"c_code":"unsigned f(unsigned a){return a;}","blocks":[{"title":"...","original_lines":"1-3","original_code":"...",'
                 '"simplified_code":"...","explanation":"...","simple":"..."}],"renames":[{"old":"v1","new":"sum","reason":"..."}],'
                 '"confidence":"high","notes":""}')


def _json_addendum() -> str:
    schema = json.dumps(DeobfResult.model_json_schema(), ensure_ascii=False, separators=(",", ":"))
    return ("\n\nOUTPUT FORMAT (json): reply with exactly ONE JSON object and nothing else: no Markdown code fences, no text before "
            "or after it. Every key is required. The object must validate against this JSON Schema:\n" + schema +
            "\nEXAMPLE JSON OUTPUT (shape only, the values are placeholders):\n" + _JSON_EXAMPLE)


@dataclass
class LLMSession:
    """Bitta funksiya bo'yicha LLM (Claude yoki DeepSeek) bilan suhbat: birinchi so'rov + tuzatish so'rovlari.

    Suhbat tarixi faqat oxiriga qo'shib boriladi (o'zgartirilmaydi) — bu prompt keshi
    ishlashi uchun muhim: oldingi qism bayt-ma-bayt bir xil qolsa, u keshdan o'qiladi.
    """

    model: str = field(default_factory=lambda: resolve_model(None))
    effort: str = "medium"
    max_tokens: int = 16000
    cache: DiskCache | None = None
    client: object = None
    api_key: str | None = field(default=None, repr=False)   # tashrif buyuruvchining o'z kaliti; saqlanmaydi
    messages: list = field(default_factory=list)
    usage: UsageStats = field(default_factory=UsageStats)
    _cache_keys: list = field(default_factory=list, repr=False)

    @property
    def provider(self) -> str:
        return provider_of(self.model)

    def _client(self):
        if self.client is None:
            if self.provider == "deepseek":
                self.client = make_client(self.api_key, "deepseek")          # LLMError o'zi tushunarli matn bilan chiqadi
                return self.client
            import anthropic  # faqat kerak bo'lganda yuklanadi (offline rejimda shart emas)

            try:
                self.client = make_client(self.api_key)
            except anthropic.AnthropicError as exc:
                raise LLMError("Claude API mijozini yaratib bo'lmadi: ANTHROPIC_API_KEY ni .env fayliga yozing "
                               "yoki --offline rejimidan foydalaning.") from None
        return self.client

    def _cache_key(self) -> str:
        # Sxema ham kalitga kiradi: javob tuzilmasi o'zgarsa, eski keshdagi javoblar ishlatilmaydi.
        payload = json.dumps({"schema": DeobfResult.model_json_schema(), "model": self.model, "effort": self.effort,
                              "system": SYSTEM_PROMPT, "messages": self.messages},
                             sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def ask(self, user_text: str) -> DeobfResult:
        self.messages.append({"role": "user", "content": user_text})
        key = self._cache_key()
        hit = self.cache.get(key) if self.cache else None
        try:
            if hit:
                self.usage.cache_hits += 1
                content, result = hit["content"], DeobfResult.model_validate(hit["result"])
            else:
                content, result = self._call_api()
                if self.cache:
                    self.cache.set(key, {"model": self.model, "content": content, "result": result.model_dump()})
        except Exception:
            self.messages.pop()                    # xatoda suhbat tarixida "osilib qolgan" savol qolmasin
            raise
        self._cache_keys.append(key)
        self.messages.append({"role": "assistant", "content": content})
        return result

    def forget(self) -> None:
        """Tekshiruvdan o'tmagan javoblarni keshdan o'chiradi: qayta urinishda xuddi shu xato javob
        $0 ga "qaytib kelmasligi", model qaytadan javob berishi uchun."""
        if self.cache:
            for key in self._cache_keys:
                self.cache.delete(key)
        self._cache_keys.clear()

    def _call_deepseek(self) -> tuple[str, DeobfResult]:
        """DeepSeek (OpenAI formati): JSON rejimi + sxema prompt ichida. Bo'sh yoki sxemaga mos kelmaydigan javobda
        (hujjat: noto'g'ri JSON bo'sh joylar bilan almashtiriladi) xatoni aytib, bir marta qayta so'raydi."""
        import pydantic

        client = self._client()
        # O'ylash (thinking) rejimi: past — doim o'chiq; o'rta — birinchi urinishda o'chiq (tez, arzon), tekshiruv xato topib
        # tuzatish so'ralganda YOQILADI (haqiqiy o'lchov: Flash o'ylashsiz 3 marta xato qilgan funksiyani o'ylash bilan 1-urinishda
        # to'g'ri yozdi); yuqori — doim yoqilgan (Pro bilan 2 daqiqagacha cho'zilishi mumkin).
        thinking = self.effort == "high" or (self.effort == "medium" and len(self.messages) > 1)
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT + _json_addendum()}] + self.messages,
            "response_format": {"type": "json_object"},
            "max_tokens": max(self.max_tokens, 32000) if thinking else self.max_tokens,   # o'ylash tokenlari ham shu chegaraga kiradi
            "thinking": {"type": "enabled" if thinking else "disabled"},
            "stream": False,
        }
        if thinking:
            payload["reasoning_effort"] = "high"
        else:
            payload["temperature"] = 0                                        # kod uchun aniqlik (o'ylash rejimida ta'sir qilmaydi)
        extra: list[dict] = []
        for attempt in (1, 2):
            try:
                body = client.chat({**payload, "messages": payload["messages"] + extra})
            except DeepSeekError as exc:
                raise LLMError(_deepseek_error_text(exc, self.model, self.api_key or server_api_key("deepseek"))) from None
            self.usage.add_deepseek(body.get("usage") or {}, self.model)     # avval narx: keyingi xatolarda ham hisobga olinadi
            choice = (body.get("choices") or [{}])[0]
            reason, message = choice.get("finish_reason"), choice.get("message") or {}
            if reason == "length":
                raise LLMError("Javob token limitiga yetib kesildi. Funksiyani kichikroq qismlarga bo'ling "
                               "yoki --effort low bilan urinib ko'ring.")
            if reason == "content_filter":
                raise LLMError("DeepSeek kontent filtri javobni to'xtatdi. Boshqa model bilan urinib ko'ring yoki offline rejimdan foydalaning.")
            if reason in ("insufficient_system_resource", "aborted"):
                raise LLMError("DeepSeek serveri resurs yetishmasligi tufayli javobni to'xtatdi. Birozdan so'ng qayta urinib ko'ring.")
            text = message.get("content") if isinstance(message.get("content"), str) else ""
            problem = "Your reply was empty (not valid JSON)."
            if text.strip():
                try:
                    return text, DeobfResult.model_validate_json(text)
                except pydantic.ValidationError as exc:
                    short = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors(include_input=False)[:4])
                    problem = f"Your reply did not match the JSON Schema ({short})."
            extra = [{"role": "assistant", "content": text.strip() or "{}"},
                     {"role": "user", "content": problem + " Reply again with ONE complete JSON object that validates against the schema."}]
        raise LLMError("DeepSeek javobini sxema bo'yicha o'qib bo'lmadi (qayta urinishdan keyin ham). Boshqa model yoki offline rejimni tanlang.")

    def _call_api(self) -> tuple[list | str, DeobfResult]:
        if self.provider == "deepseek":
            return self._call_deepseek()
        import anthropic
        import pydantic

        client = self._client()
        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_PROMPT,
                messages=self.messages,
                # Javob aynan DeobfResult sxemasi bo'yicha keladi (structured output). parse() o'rniga create()
                # ishlatamiz: javob kesilsa yoki rad etilsa ham sarflangan tokenlar hisobga olinadi va xato
                # tushunarli LLMError bo'lib chiqadi (aks holda xom ValidationError agentni to'xtatib qo'yardi).
                output_config={"effort": self.effort,
                               "format": {"type": "json_schema", "schema": anthropic.transform_schema(DeobfResult)}},
                # Avtomatik prompt keshi: tuzatish urinishlarida oldingi suhbat qayta to'liq narxda hisoblanmaydi.
                cache_control={"type": "ephemeral"},
            )
        except anthropic.AnthropicError as exc:
            raise LLMError(_api_error_text(exc, self.model, self.api_key or server_api_key())) from None
        except ValueError as exc:
            raise LLMError(f"So'rovni yuborib bo'lmadi: {exc}. --max-tokens qiymatini kamaytiring.") from None

        self.usage.add_response(response.usage, self.model)       # avval narx: keyingi xatolarda ham hisobga olinadi
        if response.stop_reason == "refusal":
            category = getattr(response.stop_details, "category", None) if response.stop_details is not None else None
            hint = (" Zararli dastur tahlilida bu tez-tez uchraydi." if category == "cyber" else "")
            raise LLMError(f"Model xavfsizlik qoidalari tufayli so'rovni bajarmadi{f' ({category})' if category else ''}."
                           f"{hint} Boshqa model (--model opus) bilan urinib ko'ring yoki offline rejimdan foydalaning.")
        if response.stop_reason == "max_tokens":
            raise LLMError("Javob token limitiga yetib kesildi. Funksiyani kichikroq qismlarga bo'ling "
                           "yoki --effort low bilan urinib ko'ring.")
        text = next((b.text for b in response.content if b.type == "text"), "")
        try:
            result = DeobfResult.model_validate_json(text)
        except pydantic.ValidationError:
            raise LLMError("Model javobini sxema bo'yicha o'qib bo'lmadi.") from None
        # Javobni tarixga qo'shish uchun JSON ko'rinishiga o'tkazamiz (thinking bloklari ham saqlanadi —
        # keyingi tuzatish so'rovida ular o'zgarishsiz qaytarilishi kerak).
        content = [b.model_dump(mode="json", exclude_none=True) for b in response.content]
        return content, result


ClaudeSession = LLMSession          # eski nom (testlar va tashqi kod uchun)
