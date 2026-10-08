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

    @property
    def content(self):
        text = self.parsed_output.model_dump_json() if self.parsed_output else ""
        return [FakeBlock("thinking", signature="sig"), FakeBlock("text", text=text)]


class FakeMessages:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def parse(self, **kwargs):
        # messages ro'yxatining nusxasini saqlaymiz (keyin u o'zgaradi)
        self.calls.append({**kwargs, "messages": [dict(m) for m in kwargs["messages"]]})
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, responses):
        self.messages = FakeMessages(responses)


def make_result(c_code: str, name: str = "f", **kw) -> DeobfResult:
    base = dict(function_name=name, suggested_name=name, summary="test", techniques=["mba"],
                c_code=c_code, blocks=[], renames=[], confidence="high", notes="")
    base.update(kw)
    return DeobfResult(**base)
