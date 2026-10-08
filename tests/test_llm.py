"""Claude moduli testlari (soxta mijoz bilan — haqiqiy API chaqirilmaydi)."""

import pytest

from deobf_agent import llm
from tests.fakes import FakeClient, FakeResponse, FakeUsage, make_result


def test_model_aliases(monkeypatch):
    monkeypatch.delenv("DEOBF_MODEL", raising=False)
    assert llm.resolve_model(None) == "claude-haiku-5-5"          # default — eng arzon
    assert llm.resolve_model("sonnet") == "claude-sonnet-5-5"
    assert llm.resolve_model("OPUS") == "claude-opus-5-5"
    assert llm.resolve_model("claude-some-model") == "claude-some-model"
    monkeypatch.setenv("DEOBF_MODEL", "opus")
    assert llm.resolve_model(None) == "claude-opus-5-5"


def test_request_shape_and_cost():
    client = FakeClient([FakeResponse(make_result("int f(int a){return a;}"),
                                      usage=FakeUsage(input_tokens=2000, output_tokens=1000))])
    s = llm.ClaudeSession(model="claude-haiku-5-5", effort="low", client=client)
    res = s.ask("salom")
    assert res.c_code.startswith("int f")
    call = client.messages.calls[0]
    assert call["model"] == "claude-haiku-5-5"
    assert call["output_config"] == {"effort": "low"}
    assert call["extra_body"] == {"cache_control": {"type": "ephemeral"}}
    assert call["messages"] == [{"role": "user", "content": "salom"}]
    # 2000 * 0.10 / 1e6 + 1000 * 0.50 / 1e6 = 0.0007 $
    assert s.usage.cost_usd == pytest.approx(0.0007)
    # javob tarixga to'liq (thinking bloki bilan) qo'shiladi
    assert s.messages[-1]["role"] == "assistant"
    assert s.messages[-1]["content"][0]["type"] == "thinking"


def test_followup_is_append_only():
    client = FakeClient([FakeResponse(make_result("x")), FakeResponse(make_result("y"))])
    s = llm.ClaudeSession(model="claude-haiku-5-5", client=client)
    s.ask("birinchi")
    s.ask("tuzat")
    first, second = client.messages.calls
    assert second["messages"][:1] == first["messages"]            # tarix o'zgarmagan, faqat qo'shilgan
    assert [m["role"] for m in second["messages"]] == ["user", "assistant", "user"]


def test_disk_cache(tmp_path):
    cache = llm.DiskCache(tmp_path)
    c1 = FakeClient([FakeResponse(make_result("int f(void){return 1;}"))])
    s1 = llm.ClaudeSession(model="claude-haiku-5-5", client=c1, cache=cache)
    s1.ask("bir xil so'rov")
    c2 = FakeClient([])                                           # javob yo'q — API chaqirilsa xato bo'ladi
    s2 = llm.ClaudeSession(model="claude-haiku-5-5", client=c2, cache=cache)
    res = s2.ask("bir xil so'rov")
    assert res.c_code == "int f(void){return 1;}"
    assert s2.usage.cache_hits == 1 and s2.usage.cost_usd == 0
    assert c2.messages.calls == []


def test_refusal_and_truncation():
    s = llm.ClaudeSession(model="claude-haiku-5-5", client=FakeClient([FakeResponse(None, stop_reason="refusal")]))
    with pytest.raises(llm.LLMError, match="bosh tortdi"):
        s.ask("x")
    s = llm.ClaudeSession(model="claude-haiku-5-5", client=FakeClient([FakeResponse(None, stop_reason="max_tokens")]))
    with pytest.raises(llm.LLMError, match="token limitiga"):
        s.ask("x")
