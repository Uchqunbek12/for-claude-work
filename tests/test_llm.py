"""Claude moduli testlari (soxta mijoz bilan — haqiqiy API chaqirilmaydi)."""

import pytest

from deobf_agent import llm
from tests.fakes import FakeClient, FakeResponse, FakeUsage, make_result


def test_model_aliases(monkeypatch):
    monkeypatch.delenv("DEOBF_MODEL", raising=False)
    assert llm.resolve_model(None) == "claude-sonnet-5-5"         # default — Sonnet 5.5
    assert llm.resolve_model("haiku") == "claude-haiku-5-5"
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
    assert call["output_config"]["effort"] == "low"
    assert call["output_config"]["format"]["type"] == "json_schema"      # javob sxema bo'yicha
    assert call["cache_control"] == {"type": "ephemeral"}
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
    with pytest.raises(llm.LLMError, match="xavfsizlik qoidalari"):
        s.ask("x")
    s = llm.ClaudeSession(model="claude-haiku-5-5", client=FakeClient([FakeResponse(None, stop_reason="max_tokens")]))
    with pytest.raises(llm.LLMError, match="token limitiga"):
        s.ask("x")


def test_truncated_or_invalid_json_is_llmerror_and_cost_counted():
    # kesilgan JSON (stop_reason end_turn, lekin yaroqsiz) -> xom ValidationError emas, LLMError; narx hisobga olinadi
    s = llm.ClaudeSession(model="claude-sonnet-5-5", client=FakeClient([FakeResponse(None, raw_text='{"function_name": "f", "su')]))
    with pytest.raises(llm.LLMError, match="sxema"):
        s.ask("x")
    assert s.usage.requests == 1 and s.usage.cost_usd > 0
    assert s.messages == []                                       # savol tarixda "osilib" qolmadi
    r = llm.ClaudeSession(model="claude-sonnet-5-5", client=FakeClient([FakeResponse(None, stop_reason="refusal")]))
    with pytest.raises(llm.LLMError):
        r.ask("x")
    assert r.usage.requests == 1                                  # rad etilgan javob ham pul turadi


def test_forget_removes_cached_answers(tmp_path):
    cache = llm.DiskCache(tmp_path)
    s = llm.ClaudeSession(model="claude-sonnet-5-5", client=FakeClient([FakeResponse(make_result("x"))]), cache=cache)
    s.ask("q")
    assert list(tmp_path.glob("*.json"))
    s.forget()
    assert not list(tmp_path.glob("*.json"))


def test_public_mode_never_uses_server_key(monkeypatch):
    from deobf_agent import sandbox

    monkeypatch.setattr(sandbox, "PUBLIC", True)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-SERVERKEYSERVERKEY1234")
    ok, msg = llm.check_api_key("sonnet")
    assert not ok and "o'z API kalitingizni" in msg and "SERVERKEY" not in msg
    with pytest.raises(llm.LLMError):
        llm.make_client(None)
    with pytest.raises(llm.LLMError, match="format"):
        llm.make_client("not-a-key")


def test_api_key_hidden_from_repr():
    s = llm.ClaudeSession(model="claude-sonnet-5-5", api_key="sk-ant-api03-SECRETSECRETSECRET1234")
    assert "SECRET" not in repr(s)
