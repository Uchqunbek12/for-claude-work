"""DeepSeek API mijozi (OpenAI formatidagi `/chat/completions`) — faqat standart kutubxona bilan.

Nima uchun tayyor kutubxona (openai, httpx) emas:
  * yangi paket o'rnatish shart emas (Dockerfile va o'rnatish yo'riqnomasi o'zgarmaydi);
  * kalit faqat bitta joyda (Authorization sarlavhasida) ishlatiladi va hech qachon xato matniga tushmaydi;
  * bizga faqat ikkita chaqiruv kerak: `chat` (javob olish) va `models` (kalitni bepul tekshirish).

Rasmiy hujjat: https://api-docs.deepseek.com/ (base_url: https://api.deepseek.com).
Testlarda shu mijozning o'rniga `chat(payload)` va `models()` metodlari bor soxta obyekt beriladi.
"""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request

BASE_URL = "https://api.deepseek.com"
MAX_BODY = 16 * 1024 * 1024          # serverdan bundan katta javobni o'qimaymiz
RETRY_STATUSES = (429, 500, 503)     # bir marta qayta uriniladi (hujjat: "biroz kutib, qayta urining")


class DeepSeekError(Exception):
    """DeepSeek bilan aloqa xatosi. `status` — HTTP kodi (tarmoq xatosida 0), `timeout` — vaqt tugadimi."""

    def __init__(self, status: int, message: str, timeout: bool = False):
        super().__init__(message)
        self.status = status
        self.message = message
        self.timeout = timeout


def _error_message(raw: bytes) -> str:
    """Xato javobidan `{"error": {"message": ...}}` matnini oladi (bo'lmasa — qisqartirilgan xom matn)."""
    text = raw.decode("utf-8", errors="replace").strip()
    try:
        body = json.loads(text)
    except ValueError:
        return text[:300]
    err = body.get("error") if isinstance(body, dict) else None
    if isinstance(err, dict) and isinstance(err.get("message"), str):
        return err["message"][:300]
    return text[:300]


class DeepSeekClient:
    """Minimal mijoz. `api_key` repr'da ko'rinmaydi."""

    def __init__(self, api_key: str, base_url: str = BASE_URL, timeout: float = 90.0, retry_delay: float = 2.0):
        self._api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout          # veb-serverning umumiy chegarasidan (gunicorn: 120 s) past bo'lsin
        self.retry_delay = retry_delay

    def __repr__(self) -> str:
        return f"DeepSeekClient(base_url={self.base_url!r})"

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(
            self.base_url + path, data=data, method=method,
            headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json",
                     "Accept": "application/json", "User-Agent": "deobf-agent"})
        for attempt in (1, 2):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read(MAX_BODY + 1)
                if len(raw) > MAX_BODY:
                    raise DeepSeekError(0, "Server juda katta javob yubordi.")
                try:
                    body = json.loads(raw)
                except ValueError:
                    raise DeepSeekError(0, "Server noto'g'ri formatdagi javob yubordi.") from None
                if not isinstance(body, dict):
                    raise DeepSeekError(0, "Server kutilmagan formatdagi javob yubordi.")
                return body
            except urllib.error.HTTPError as exc:
                error = DeepSeekError(exc.code, _error_message(exc.read(65536)))
            except (socket.timeout, TimeoutError):
                error = DeepSeekError(0, "Vaqt tugadi.", timeout=True)
            except urllib.error.URLError as exc:
                error = DeepSeekError(0, "Ulanib bo'lmadi.", timeout=isinstance(exc.reason, (socket.timeout, TimeoutError)))
            if attempt == 1 and error.status in RETRY_STATUSES:
                time.sleep(self.retry_delay)
                continue
            raise error
        raise AssertionError("unreachable")

    def chat(self, payload: dict) -> dict:
        """POST /chat/completions — javob (JSON lug'at) qaytaradi."""
        return self._request("POST", "/chat/completions", payload)

    def models(self) -> list[str]:
        """GET /models — mavjud model nomlari. Matn yaratmaydi, shuning uchun BEPUL (kalitni tekshirish uchun)."""
        body = self._request("GET", "/models")
        return [m["id"] for m in body.get("data", []) if isinstance(m, dict) and isinstance(m.get("id"), str)]
