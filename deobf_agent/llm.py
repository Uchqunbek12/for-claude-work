"""Claude API bilan ishlash: model tanlash, so'rov yuborish, narx hisoblash, kesh.

Asosiy tushunchalar:
  * token — model matnni o'qiydigan va yozadigan "bo'lak" (taxminan 3-4 harf).
    API narxi tokenlar soniga qarab hisoblanadi: kirish (input) va chiqish (output) alohida.
  * model — default "haiku" (Claude Haiku 5.5, eng arzon). --model sonnet / opus bilan
    kuchliroq modelga bir zumda o'tish mumkin.
  * effort — modelning "o'ylash" chuqurligi (low / medium / high). Pastroq = arzonroq va tezroq.
  * structured output — javob aniq sxema (schema.DeobfResult) bo'yicha keladi.
  * prompt caching — so'rovning o'zgarmas boshlang'ich qismi (ko'rsatmalar) API serverida
    keshlanadi; keyingi so'rovlarda u ~10 barobar arzon hisoblanadi.
  * disk kesh — bir xil kod uchun bir xil so'rovni qayta yubormaymiz: javob diskdan olinadi ($0).
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .prompts import SYSTEM_PROMPT
from .schema import DeobfResult

MODEL_ALIASES = {
    "haiku": "claude-haiku-5-5",
    "sonnet": "claude-sonnet-5-5",
    "opus": "claude-opus-5-5",
}
DEFAULT_MODEL = "haiku"

# Narxlar: AQSH dollari / 1 million token. (kirish, chiqish, kesh-yozish, kesh-o'qish)
# Taxminiy qiymatlar — aniq va eng so'nggi narxlar: https://www.anthropic.com/pricing
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50, 0.125, 0.01),
    "claude-sonnet-5-5": (2.00, 10.00, 2.50, 0.20),
    "claude-opus-5-5": (4.00, 20.00, 5.00, 0.20),
}

EFFORTS = ("low", "medium", "high")
LANGUAGES = ("uz", "ru", "en")


class LLMError(Exception):
    """LLM bilan bog'liq xato (foydalanuvchiga tushunarli matn bilan)."""


def resolve_model(name: str | None) -> str:
    """'haiku' -> 'claude-haiku-5-5'. To'liq model nomi berilsa, o'zgarishsiz qaytariladi."""
    name = (name or os.environ.get("DEOBF_MODEL") or DEFAULT_MODEL).strip()
    return MODEL_ALIASES.get(name.lower(), name)


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
    """Kalitni xavfsiz ko'rsatish: sk-ant-api03-...a1b2"""
    if not key:
        return "(yo'q)"
    return key[:12] + "..." + key[-4:] if len(key) > 20 else "***"


def _api_error_text(exc: Exception, model_id: str, key: str = "") -> str:
    """Claude API xatosini foydalanuvchiga tushunarli o'zbekcha matnga aylantiradi."""
    import anthropic

    if isinstance(exc, anthropic.AuthenticationError):
        return (f"Kalit noto'g'ri yoki bekor qilingan ({mask_key(key)}). "
                "console.anthropic.com da yangi kalit yarating.")
    if isinstance(exc, anthropic.PermissionDeniedError):
        return f"Kalitga ruxsat yo'q: {exc.message}"
    if isinstance(exc, anthropic.NotFoundError):
        return f"'{model_id}' modeli topilmadi yoki sizga mavjud emas. Boshqa modelni tanlang (haiku, sonnet, opus)."
    if isinstance(exc, anthropic.RateLimitError):
        return "So'rovlar limiti oshib ketdi (rate limit). Bir oz kutib, qayta urinib ko'ring."
    if isinstance(exc, anthropic.BadRequestError):
        return f"So'rov rad etildi (400): {exc.message}"
    if isinstance(exc, anthropic.APIStatusError):
        return f"Claude API xatosi ({exc.status_code}): {exc.message}"
    if isinstance(exc, anthropic.APIConnectionError):
        return "Claude serveriga ulanib bo'lmadi — internet aloqasini tekshiring."
    return f"Claude API xatosi: {exc}"


def make_client(api_key: str | None = None):
    """Claude mijozini yaratadi. api_key berilmasa — ANTHROPIC_API_KEY (yoki .env) dan olinadi."""
    import anthropic

    return anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()


def check_api_key(model: str | None = None, client=None, api_key: str | None = None) -> tuple[bool, str]:
    """Kalit va model ishlayotganini tekshiradi.

    Models API (`models.retrieve`) chaqiriladi — bu matn generatsiya qilmaydi va BEPUL.
    Natija: (muvaffaqiyat, o'zbekcha xabar).
    """
    import anthropic

    model_id = resolve_model(model)
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if client is None:
        if not key:
            return False, ("ANTHROPIC_API_KEY topilmadi. Loyiha papkasida .env fayli yarating va unga "
                           "ANTHROPIC_API_KEY=sk-ant-... qatorini yozing.")
        if not key.startswith("sk-ant-"):
            return False, f"Kalit 'sk-ant-' bilan boshlanmaydi ({mask_key(key)}) — to'liq nusxalanganini tekshiring."
    try:
        info = (client or make_client(api_key)).models.retrieve(model_id)
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

    def add_response(self, usage, model: str) -> None:
        p_in, p_out, p_cw, p_cr = PRICES.get(model, PRICES["claude-opus-5-5"])
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


@dataclass
class ClaudeSession:
    """Bitta funksiya bo'yicha Claude bilan suhbat: birinchi so'rov + tuzatish so'rovlari.

    Suhbat tarixi faqat oxiriga qo'shib boriladi (o'zgartirilmaydi) — bu prompt keshi
    ishlashi uchun muhim: oldingi qism bayt-ma-bayt bir xil qolsa, u keshdan o'qiladi.
    """

    model: str = field(default_factory=lambda: resolve_model(None))
    effort: str = "medium"
    max_tokens: int = 16000
    cache: DiskCache | None = None
    client: object = None
    api_key: str | None = None        # tashrif buyuruvchining o'z kaliti (public rejim); saqlanmaydi
    messages: list = field(default_factory=list)
    usage: UsageStats = field(default_factory=UsageStats)

    def _client(self):
        if self.client is None:
            import anthropic  # faqat kerak bo'lganda yuklanadi (offline rejimda shart emas)

            try:
                self.client = make_client(self.api_key)
            except anthropic.AnthropicError as exc:
                raise LLMError(f"Claude API mijozini yaratib bo'lmadi: {exc}. "
                               "ANTHROPIC_API_KEY ni .env fayliga yozing yoki --offline rejimidan foydalaning.")
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
        if hit:
            self.usage.cache_hits += 1
            content, result = hit["content"], DeobfResult.model_validate(hit["result"])
        else:
            content, result = self._call_api()
            if self.cache:
                self.cache.set(key, {"model": self.model, "content": content, "result": result.model_dump()})
        self.messages.append({"role": "assistant", "content": content})
        return result

    def _call_api(self) -> tuple[list, DeobfResult]:
        import anthropic

        client = self._client()
        try:
            response = client.messages.parse(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_PROMPT,
                messages=self.messages,
                output_format=DeobfResult,
                output_config={"effort": self.effort},
                # Avtomatik prompt keshi: so'rovning oxirgi blokigacha bo'lgan qism keshlanadi,
                # tuzatish so'rovlarida oldingi suhbat qayta to'liq narxda hisoblanmaydi.
                extra_body={"cache_control": {"type": "ephemeral"}},
            )
        except anthropic.AnthropicError as exc:
            raise LLMError(_api_error_text(exc, self.model, self.api_key or os.environ.get("ANTHROPIC_API_KEY", ""))) from exc

        self.usage.add_response(response.usage, self.model)
        if response.stop_reason == "refusal":
            detail = ""
            if response.stop_details is not None:
                detail = f" ({getattr(response.stop_details, 'category', '') or ''})"
            raise LLMError(f"Model so'rovni bajarishdan bosh tortdi{detail}. Boshqa model bilan urinib "
                           "ko'ring (--model sonnet) yoki offline rejimdan foydalaning.")
        if response.stop_reason == "max_tokens":
            raise LLMError("Javob token limitiga yetib kesildi. --max-tokens qiymatini oshiring yoki "
                           "funksiyani kichikroq qismlarga bo'ling.")
        result = response.parsed_output
        if result is None:
            raise LLMError("Model javobini sxema bo'yicha o'qib bo'lmadi.")
        # Javobni tarixga qo'shish uchun JSON ko'rinishiga o'tkazamiz (thinking bloklari ham saqlanadi —
        # keyingi tuzatish so'rovida ular o'zgarishsiz qaytarilishi kerak).
        content = [b.model_dump(mode="json", exclude_none=True) for b in response.content]
        return content, result
