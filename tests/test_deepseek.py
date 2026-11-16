"""DeepSeek provayderi: model nomlari, so'rov shakli, narx, xatolar, haqiqiy HTTP (mahalliy server), agent sikli, CLI."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from deobf_agent import llm
from deobf_agent.agent import AgentConfig, deobfuscate_text
from deobf_agent.deepseek import DeepSeekClient, DeepSeekError
from tests.fakes import FakeDeepSeek, deepseek_reply, make_result

KEY = "sk-" + "a1b2c3d4" * 4
S1 = "unsigned int mix(unsigned int a0, unsigned int a1)\n{\n    return ((a0 + a1) ^ (a0 - a1)) | (a0 & 0xff);\n}"
GOOD = make_result("unsigned int mix(unsigned int a0, unsigned int a1)\n{ return ((a0 + a1) ^ (a0 - a1)) | (a0 & 0xFFu); }", "mix")
WRONG = make_result("unsigned int mix(unsigned int a0, unsigned int a1)\n{ return (a0 + a1) | (a0 & 0xFFu); }", "mix")


def session(fake, **kw):
    return llm.LLMSession(model="deepseek-flash", client=fake, **kw)


# ------------------------------------------------------------------ model nomlari va kalitlar
def test_aliases_providers_and_default_model(monkeypatch):
    assert llm.resolve_model("deepseek") == "deepseek-flash" and llm.resolve_model("deepseek-pro") == "deepseek-v4-pro"
    assert llm.provider_of("deepseek-v4-pro") == "deepseek" and llm.provider_of("claude-sonnet-5-5") == "anthropic"
    assert llm.resolve_model(None) == "claude-sonnet-5-5"                      # kalitsiz — avvalgidek Claude
    monkeypatch.setenv("DEEPSEEK_API_KEY", KEY)
    assert llm.resolve_model(None) == "deepseek-flash"                         # DeepSeek kaliti bor — DeepSeek
    monkeypatch.setenv("DEOBF_MODEL", "haiku")
    assert llm.resolve_model(None) == "claude-haiku-5-5"                       # aniq tanlov hammasidan ustun


def test_key_is_cleaned_and_format_checked(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", f' "{KEY}"\n')
    assert llm.server_api_key("deepseek") == KEY
    with pytest.raises(llm.LLMError, match="format"):
        llm.make_client("sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUV", "deepseek")      # Claude kaliti DeepSeek'ga mos emas
    assert isinstance(llm.make_client(KEY, "deepseek"), DeepSeekClient) and KEY not in repr(llm.make_client(KEY, "deepseek"))


# ------------------------------------------------------------------ so'rov shakli, javob, narx
def test_request_uses_json_mode_schema_in_prompt_and_cheap_non_thinking_defaults():
    fake = FakeDeepSeek([deepseek_reply(GOOD, hit=400, miss=600, out=500)])
    s = session(fake)
    assert s.ask("Function: mix").function_name == "mix"
    p = fake.payloads[0]
    assert p["response_format"] == {"type": "json_object"} and p["thinking"] == {"type": "disabled"}
    assert p["temperature"] == 0 and "reasoning_effort" not in p and p["max_tokens"] == 16000 and p["stream"] is False
    system = p["messages"][0]
    assert system["role"] == "system" and "json" in system["content"].lower() and '"c_code"' in system["content"]   # hujjat: "json" so'zi + sxema
    assert p["messages"][1] == {"role": "user", "content": "Function: mix"}
    # narx: miss 600 * 0.30 + out 500 * 1.20 + hit 400 * 0.006 (so'mga emas, dollar / 1M token)
    assert s.usage.cost_usd == pytest.approx((600 * 0.30 + 500 * 1.20 + 400 * 0.006) / 1e6)
    assert (s.usage.input_tokens, s.usage.output_tokens, s.usage.cache_read_tokens) == (600, 500, 400)


def test_medium_effort_escalates_to_thinking_only_when_a_fix_is_requested_and_low_never_does():
    fake = FakeDeepSeek([deepseek_reply(WRONG), deepseek_reply(GOOD)])
    s = session(fake)                                       # effort = medium (standart)
    s.ask("first")
    s.ask("fix it")
    assert fake.payloads[0]["thinking"] == {"type": "disabled"}                      # 1-urinish: tez va arzon
    assert fake.payloads[1]["thinking"] == {"type": "enabled"} and fake.payloads[1]["max_tokens"] >= 32000   # tuzatish: o'ylash
    fake = FakeDeepSeek([deepseek_reply(WRONG), deepseek_reply(GOOD)])
    s = session(fake, effort="low")
    s.ask("first")
    s.ask("fix it")
    assert [p["thinking"]["type"] for p in fake.payloads] == ["disabled", "disabled"]


def test_request_timeout_is_configurable_and_defaults_below_the_web_limit(monkeypatch):
    assert llm.make_client(KEY, "deepseek").timeout == 90
    monkeypatch.setenv("DEOBF_LLM_TIMEOUT", "200")
    assert llm.make_client(KEY, "deepseek").timeout == 200
    monkeypatch.setenv("DEOBF_LLM_TIMEOUT", "abc")
    assert llm.make_client(KEY, "deepseek").timeout == 90


def test_high_effort_turns_thinking_on_and_leaves_room_for_it():
    fake = FakeDeepSeek([deepseek_reply(GOOD)])
    session(fake, effort="high").ask("x")
    p = fake.payloads[0]
    assert p["thinking"] == {"type": "enabled"} and p["reasoning_effort"] == "high" and "temperature" not in p
    assert p["max_tokens"] >= 32000


def test_followup_keeps_history_append_only_and_plain_text_replies():
    fake = FakeDeepSeek([deepseek_reply(WRONG), deepseek_reply(GOOD)])
    s = session(fake)
    s.ask("first")
    s.ask("fix it")
    msgs = fake.payloads[1]["messages"]
    assert [m["role"] for m in msgs] == ["system", "user", "assistant", "user"]
    assert isinstance(msgs[2]["content"], str) and msgs[2]["content"].startswith("{")     # oldingi javob matn sifatida qaytariladi
    assert fake.payloads[0]["messages"][0] == fake.payloads[1]["messages"][0]            # system bir xil: DeepSeek keshi ishlaydi


def test_blank_json_is_retried_once_with_a_repair_message_and_both_requests_are_billed():
    fake = FakeDeepSeek([deepseek_reply("   "), deepseek_reply(GOOD)])
    s = session(fake)
    assert s.ask("x").function_name == "mix"
    assert len(fake.payloads) == 2 and s.usage.requests == 2
    repair = fake.payloads[1]["messages"][-1]["content"]
    assert "empty" in repair and "JSON" in repair
    assert [m["role"] for m in s.messages] == ["user", "assistant"]                          # tuzatish xabarlari tarixga kirmaydi


def test_schema_mismatch_names_the_problem_and_gives_up_after_one_retry():
    bad = json.dumps({"function_name": "mix"})
    fake = FakeDeepSeek([deepseek_reply(bad), deepseek_reply(bad)])
    with pytest.raises(llm.LLMError, match="sxema"):
        session(fake).ask("x")
    assert "did not match" in fake.payloads[1]["messages"][-1]["content"] and len(fake.payloads) == 2


@pytest.mark.parametrize("finish,needle", [("length", "token limit"), ("content_filter", "filtr"), ("aborted", "resurs")])
def test_finish_reasons_become_clear_errors(finish, needle):
    with pytest.raises(llm.LLMError, match=needle):
        session(FakeDeepSeek([deepseek_reply("{}", finish=finish)])).ask("x")


@pytest.mark.parametrize("status,needle", [(401, "noto'g'ri yoki bekor"), (402, "mablag'"), (429, "limit"), (503, "band"),
                                           (400, "rad etildi"), (404, "topilmadi")])
def test_http_errors_are_explained_and_never_leak_the_key(status, needle):
    fake = FakeDeepSeek(error=DeepSeekError(status, "boom"))
    with pytest.raises(llm.LLMError, match=needle) as e:
        llm.LLMSession(model="deepseek-flash", client=fake, api_key=KEY).ask("x")
    assert KEY not in str(e.value)
    assert "vaqt" in llm._deepseek_error_text(DeepSeekError(0, "t", timeout=True), "m")
    assert "ulanib" in llm._deepseek_error_text(DeepSeekError(0, "t"), "m")


def test_check_api_key_for_deepseek():
    ok, msg = llm.check_api_key("deepseek", client=FakeDeepSeek())
    assert ok and "deepseek-flash" in msg
    ok, msg = llm.check_api_key("deepseek", client=FakeDeepSeek(models=["other"]))
    assert not ok and "ro'yxatda yo'q" in msg
    ok, msg = llm.check_api_key("deepseek", client=FakeDeepSeek(error=DeepSeekError(401, "bad")))
    assert not ok and "bekor qilingan" in msg
    ok, msg = llm.check_api_key("deepseek")                                                  # kalit umuman yo'q
    assert not ok and "DEEPSEEK_API_KEY topilmadi" in msg


# ------------------------------------------------------------------ haqiqiy HTTP (mahalliy server)
class _Handler(BaseHTTPRequestHandler):
    log = []
    script = []                              # navbatdagi javoblar: (status, tana)

    def _reply(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n)) if n else None
        type(self).log.append((self.command, self.path, self.headers.get("Authorization"), body))
        status, payload = type(self).script.pop(0)
        raw = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    do_GET = do_POST = _reply

    def log_message(self, *a):
        pass


@pytest.fixture
def server(monkeypatch):
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    monkeypatch.setenv("no_proxy", "127.0.0.1")
    _Handler.log, _Handler.script = [], []
    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def test_client_sends_bearer_key_and_json_and_parses_the_reply(server):
    _Handler.script = [(200, {"ok": 1}), (200, {"data": [{"id": "deepseek-flash"}, {"id": "deepseek-v4-pro"}]})]
    c = DeepSeekClient(KEY, base_url=server)
    assert c.chat({"model": "m", "messages": []}) == {"ok": 1}
    assert c.models() == ["deepseek-flash", "deepseek-v4-pro"]
    (m1, p1, auth1, body1), (m2, p2, _, _) = _Handler.log
    assert (m1, p1, auth1, body1) == ("POST", "/chat/completions", f"Bearer {KEY}", {"model": "m", "messages": []})
    assert (m2, p2) == ("GET", "/models")


def test_client_retries_once_on_503_then_succeeds_and_reports_errors(server):
    _Handler.script = [(503, {"error": {"message": "busy"}}), (200, {"ok": 2})]
    assert DeepSeekClient(KEY, base_url=server, retry_delay=0).chat({}) == {"ok": 2}
    _Handler.script = [(401, {"error": {"message": "Authentication Fails"}})]
    with pytest.raises(DeepSeekError) as e:
        DeepSeekClient(KEY, base_url=server, retry_delay=0).chat({})
    assert e.value.status == 401 and "Authentication" in e.value.message and KEY not in str(e.value)
    _Handler.script = [(500, {}), (500, {"error": {"message": "down"}})]                 # ikkinchi marta ham xato: to'xtaydi
    with pytest.raises(DeepSeekError) as e:
        DeepSeekClient(KEY, base_url=server, retry_delay=0).chat({})
    assert e.value.status == 500 and len(_Handler.log) == 5


def test_client_connection_failure_is_a_clear_error():
    with pytest.raises(DeepSeekError) as e:
        DeepSeekClient(KEY, base_url="http://127.0.0.1:9", timeout=2).chat({})
    assert e.value.status == 0


# ------------------------------------------------------------------ agent sikli (DeepSeek bilan)
def test_agent_verifies_a_deepseek_answer_and_reports_cost():
    fake = FakeDeepSeek([deepseek_reply(GOOD)])
    _, reps = deobfuscate_text(S1, AgentConfig(model="deepseek", client=fake, cache_dir=None))
    r = reps[0]
    assert r.engine == "deepseek-flash" and r.verification.status == "verified" and len(r.attempts) == 1
    assert r.usage.cost_usd > 0 and not r.error


def test_agent_feeds_the_mismatch_back_to_deepseek_and_gets_a_fix():
    fake = FakeDeepSeek([deepseek_reply(WRONG), deepseek_reply(GOOD)])
    _, reps = deobfuscate_text(S1, AgentConfig(model="deepseek", client=fake, cache_dir=None))
    r = reps[0]
    assert [a.status for a in r.attempts] == ["mismatch", "verified"] and r.engine == "deepseek-flash"
    assert "Differential testing" in fake.payloads[1]["messages"][-1]["content"]


def test_agent_falls_back_to_offline_when_deepseek_is_down():
    fake = FakeDeepSeek(error=DeepSeekError(402, "no balance"))
    _, reps = deobfuscate_text(S1, AgentConfig(model="deepseek", client=fake, cache_dir=None))
    r = reps[0]
    assert r.engine == "offline" and r.verification.status == "verified" and "mablag'" in r.error


# ------------------------------------------------------------------ CLI
def test_check_command_lists_both_providers(monkeypatch, capsys):
    from deobf_agent.cli import main

    monkeypatch.setenv("DEEPSEEK_API_KEY", KEY)
    main(["check", "--no-network"])
    out = capsys.readouterr().out
    assert "DEEPSEEK_API_KEY" in out and "ANTHROPIC_API_KEY" in out and "Standart model: deepseek-flash" in out
    assert KEY not in out                                                                  # kalit to'liq ko'rsatilmaydi


def test_dotenv_file_provides_the_deepseek_key_and_makes_it_the_default(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text(f"DEEPSEEK_API_KEY={KEY}\n", encoding="utf-8")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    llm.load_dotenv(env)
    assert llm.server_api_key("deepseek") == KEY and llm.resolve_model(None) == "deepseek-flash"


def test_masked_key_hides_the_random_part_of_a_deepseek_key():
    assert llm.mask_key(KEY) == "sk-a1...c3d4" and KEY[5:-4] not in llm.mask_key(KEY)
    assert llm.mask_key("sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUV1234") == "sk-ant-api03...1234"       # Claude: avvalgidek
