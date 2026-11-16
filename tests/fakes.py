"""Testlar uchun soxta Claude mijozi: tarmoqqa chiqmaydi, oldindan berilgan javoblarni qaytaradi."""

from __future__ import annotations

from dataclasses import dataclass, field

from deobf_agent.schema import DeobfResult


@dataclass
class FakeUsage:
    input_tokens: int = 1000
    output_tokens: int = 500
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


@dataclass
class FakeBlock:
    type: str
    text: str = ""
    thinking: str = ""
    signature: str = ""

    def model_dump(self, mode="json", exclude_none=True):
        if self.type == "thinking":
            return {"type": "thinking", "thinking": self.thinking, "signature": self.signature}
        return {"type": "text", "text": self.text}


@dataclass
class FakeResponse:
    parsed_output: DeobfResult | None
    stop_reason: str = "end_turn"
    stop_details: object = None
    usage: FakeUsage = field(default_factory=FakeUsage)
    raw_text: str | None = None            # parsed_output o'rniga to'g'ridan-to'g'ri matn (kesilgan/yaroqsiz JSON uchun)

    @property
    def content(self):
        text = self.raw_text if self.raw_text is not None else (
            self.parsed_output.model_dump_json() if self.parsed_output else "")
        return [FakeBlock("thinking", signature="sig"), FakeBlock("text", text=text)]


class FakeMessages:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        # messages ro'yxatining nusxasini saqlaymiz (keyin u o'zgaradi)
        self.calls.append({**kwargs, "messages": [dict(m) for m in kwargs["messages"]]})
        return self.responses.pop(0)


class FakeModels:
    """client.models.retrieve() — kalitni tekshirish uchun."""

    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def retrieve(self, model_id):
        self.calls.append(model_id)
        if self.error is not None:
            raise self.error
        return type("ModelInfo", (), {"id": model_id, "display_name": model_id.replace("-", " ").title()})()


class FakeClient:
    def __init__(self, responses=(), model_error=None):
        self.messages = FakeMessages(responses)
        self.models = FakeModels(model_error)


def make_result(c_code: str, name: str = "f", **kw) -> DeobfResult:
    base = dict(function_name=name, suggested_name=name, summary="test", simple_summary="oddiy tilda test",
                techniques=["mba"], c_code=c_code, blocks=[], renames=[], confidence="high", notes="")
    base.update(kw)
    return DeobfResult(**base)


class FakeDeepSeek:
    """Soxta DeepSeek mijozi (`chat(payload)` va `models()`): tarmoqqa chiqmaydi, oldindan berilgan javoblarni qaytaradi."""

    def __init__(self, replies=(), error=None, models=("deepseek-flash", "deepseek-v4-pro")):
        self.replies = list(replies)
        self.error = error                  # DeepSeekError: har bir chaqiruvda ko'tariladi
        self.payloads = []                  # yuborilgan so'rovlar (messages nusxasi bilan)
        self.model_names = list(models)
        self.models_calls = 0

    def chat(self, payload):
        self.payloads.append({**payload, "messages": [dict(m) for m in payload["messages"]]})
        if self.error is not None:
            raise self.error
        return self.replies.pop(0)

    def models(self):
        self.models_calls += 1
        if self.error is not None:
            raise self.error
        return list(self.model_names)


def deepseek_reply(content, finish="stop", hit=0, miss=1000, out=500):
    """DeepSeek `/chat/completions` javobi shaklidagi lug'at. `content` — DeobfResult yoki xom matn."""
    text = content.model_dump_json() if isinstance(content, DeobfResult) else content
    return {"choices": [{"index": 0, "finish_reason": finish, "message": {"role": "assistant", "content": text}}],
            "usage": {"prompt_tokens": hit + miss, "completion_tokens": out, "prompt_cache_hit_tokens": hit,
                      "prompt_cache_miss_tokens": miss}}
