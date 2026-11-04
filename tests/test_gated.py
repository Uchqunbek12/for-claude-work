"""Yopiq demo (kirish kodi), server kaliti, kunlik byudjet va foydalanuvchi ajratishi testlari."""

import os

import pytest

from deobf_agent import compiler, harness, sandbox
from deobf_agent.web.app import create_app
from tests.fakes import FakeClient, FakeResponse, make_result

CODE = "7391"
GOOD = make_result("unsigned int mix(unsigned int a, unsigned int b)\n{ return ((a + b) ^ (a - b)) | (a & 0xFFu); }", "mix")
S1 = "unsigned int mix(unsigned int a0, unsigned int a1)\n{\n    return ((a0 + a1) ^ (a0 - a1)) | (a0 & 0xff);\n}"


@pytest.fixture
def gated(monkeypatch):
    monkeypatch.setattr(sandbox, "PUBLIC", True)
    monkeypatch.setattr(sandbox, "NATIVE", False)
    monkeypatch.setattr(sandbox, "USE_SERVER_KEY", False)
    return lambda **cfg: create_app({"ACCESS_CODE": CODE, **cfg})


def login(client, code=CODE, ip="10.0.0.1"):
    return client.post("/login", data={"code": code}, environ_overrides={"REMOTE_ADDR": ip})


def test_everything_requires_the_code_except_login_health_and_static(gated):
    c = gated().test_client()
    assert c.get("/").status_code == 302 and "/login" in c.get("/").headers["Location"]
    assert c.post("/analyze", data={"code": S1, "engine": "offline"}).status_code == 302
    assert c.get("/download/abc.md").status_code == 302
    assert c.post("/api/check-key", data={"model": "sonnet"}).status_code == 401
    assert c.get("/healthz").get_data(as_text=True) == "ok"
    assert c.get("/login").status_code == 200 and c.get("/static/app.js").status_code == 200


def test_wrong_code_rejected_and_right_code_opens_the_site(gated):
    c = gated().test_client()
    r = login(c, "1234")
    assert r.status_code == 401 and "noto&#39;g&#39;ri" in r.get_data(as_text=True)
    assert c.get("/").status_code == 302                          # hali kirmagan
    assert login(c).status_code == 303
    page = c.get("/")
    assert page.status_code == 200 and "Yopiq demo" in page.get_data(as_text=True)
    assert "no-store" in page.headers["Cache-Control"]
    c.post("/logout")
    assert c.get("/").status_code == 302                          # chiqqach yana kod kerak


def test_session_cookie_is_http_only_and_not_readable_from_scripts(gated):
    c = gated().test_client()
    cookie = login(c).headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie and CODE not in cookie


def test_guessing_the_code_is_throttled_per_ip_and_globally(gated):
    app = gated()
    c = app.test_client()
    for _ in range(5):
        assert login(c, "0000", ip="9.9.9.9").status_code == 401
    r = login(c, CODE, ip="9.9.9.9")                              # 6-urinish: kod to'g'ri bo'lsa ham bloklangan
    assert r.status_code == 429 and r.headers["Retry-After"]
    # boshqa IP'lardan ko'p urinish: umumiy blok (4 xonali kodni taqsimlangan holda terish ham to'xtaydi)
    c2 = gated().test_client()
    for i in range(40):
        login(c2, "0000", ip=f"7.7.{i // 250}.{i % 250 + 1}")
    assert login(c2, CODE, ip="8.8.8.8").status_code == 429


def test_server_key_is_refused_without_access_code(monkeypatch):
    monkeypatch.setattr(sandbox, "PUBLIC", True)
    monkeypatch.setattr(sandbox, "USE_SERVER_KEY", True)
    with pytest.raises(RuntimeError, match="DEOBF_ACCESS_CODE"):
        create_app()


def test_logged_in_user_can_use_server_key_and_daily_budget_stops_it(gated, monkeypatch):
    monkeypatch.setattr(sandbox, "USE_SERVER_KEY", True)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-SERVERKEYSERVERKEY1234567890")
    fake = FakeClient([FakeResponse(GOOD), FakeResponse(GOOD)])
    c = gated(CLIENT=fake, DAILY_BUDGET_USD=0.001).test_client()
    login(c)
    html = c.get("/").get_data(as_text=True)
    assert "Server kaliti ulangan" in html and "SERVERKEY" not in html
    ok = c.post("/analyze", data={"code": S1, "engine": "sonnet"}).get_data(as_text=True)      # kalit kiritilmagan
    assert "claude-sonnet-5-5" in ok and "API kalitingizni kiriting" not in ok
    stop = c.post("/analyze", data={"code": S1, "engine": "sonnet"}).get_data(as_text=True)
    assert "byudjeti tugadi" in stop and len(fake.messages.calls) == 1                         # ikkinchi so'rov Claude'ga bormadi
    offline = c.post("/analyze", data={"code": S1, "engine": "offline"}).get_data(as_text=True)
    assert "byudjeti tugadi" not in offline                                                    # offline baribir ishlaydi


def test_without_server_key_flag_a_logged_in_user_still_needs_own_key(gated):
    c = gated().test_client()
    login(c)
    html = c.post("/analyze", data={"code": S1, "engine": "sonnet"}).get_data(as_text=True)
    assert "API kalitingizni kiriting" in html


def test_native_needs_access_code_and_isolation_when_server_key_is_used(monkeypatch):
    monkeypatch.setattr(sandbox, "PUBLIC", True)
    monkeypatch.setattr(sandbox, "NATIVE", True)
    monkeypatch.setattr(sandbox, "USE_SERVER_KEY", False)
    sandbox.configure(False, log=lambda *_: None)
    assert not sandbox.native_allowed()                           # kirish kodisiz begona kod ishga tushmaydi
    monkeypatch.setattr(sandbox, "NATIVE", True)
    monkeypatch.setattr(sandbox, "USE_SERVER_KEY", True)
    monkeypatch.setattr(sandbox, "SANDBOX_UID", 0)                # ajratish yo'q
    sandbox.configure(True, log=lambda *_: None)
    assert not sandbox.native_allowed()                           # server kaliti + ajratishsiz = kod ishga tushmaydi


root_only = pytest.mark.skipif(not hasattr(os, "geteuid") or os.geteuid() != 0, reason="root kerak")


@root_only
def test_executed_code_runs_as_another_user_and_cannot_read_server_secrets(monkeypatch):
    monkeypatch.setattr(sandbox, "SANDBOX_UID", 10002)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-SERVERKEYSERVERKEY1234567890")
    assert sandbox.selftest_isolation()
    assert sandbox.run(["id", "-u"], timeout=5).stdout.strip() == "10002"
    leak = sandbox.run(["sh", "-c", f"cat /proc/{os.getpid()}/environ"], timeout=5)
    assert "SERVERKEY" not in leak.stdout and leak.returncode != 0


@root_only
@pytest.mark.skipif(compiler.find_compiler() is None, reason="C kompilyatori yo'q")
def test_full_differential_test_works_when_code_runs_as_unprivileged_user(monkeypatch):
    monkeypatch.setattr(sandbox, "SANDBOX_UID", 10002)
    a = "int f(int x) { return x * 2; }"
    assert harness.differential_test(a, "f", "int f(int x) { return x + x; }", "f", "int", ["int"]).status == "equivalent"
    assert harness.differential_test(a, "f", "int f(int x) { return x + x + 1; }", "f", "int", ["int"]).status == "mismatch"


def test_model_picker_is_available_after_login(gated):
    c = gated().test_client()
    login(c)
    html = c.get("/").get_data(as_text=True)
    for value in ("sonnet", "haiku", "opus", "offline", "custom"):          # yopiq demoda "Boshqa model" ham bor
        assert f'<option value="{value}"' in html


def test_server_key_and_native_turn_on_automatically_when_access_code_is_set(monkeypatch):
    # Render'da faqat ikki maydon yaratish yetadi: DEOBF_ACCESS_CODE va ANTHROPIC_API_KEY
    monkeypatch.setattr(sandbox, "PUBLIC", True)
    monkeypatch.setattr(sandbox, "NATIVE", None)
    monkeypatch.setattr(sandbox, "USE_SERVER_KEY", None)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-SERVERKEYSERVERKEY1234567890")
    app = create_app({"ACCESS_CODE": CODE})
    assert sandbox.USE_SERVER_KEY is True
    c = app.test_client()
    login(c)
    assert "Server kaliti ulangan" in c.get("/").get_data(as_text=True)         # "kalitingizni kiriting" demaydi
    monkeypatch.setattr(sandbox, "NATIVE", None)
    monkeypatch.setattr(sandbox, "USE_SERVER_KEY", None)
    create_app()                                                                  # kirish kodisiz: hech narsa avtomatik yoqilmaydi
    assert sandbox.USE_SERVER_KEY is False and sandbox.NATIVE is False


def test_explicit_zero_turns_features_off_even_with_access_code(monkeypatch):
    monkeypatch.setattr(sandbox, "PUBLIC", True)
    monkeypatch.setenv("DEOBF_NATIVE", "0")
    monkeypatch.setenv("DEOBF_USE_SERVER_KEY", "0")
    monkeypatch.setattr(sandbox, "NATIVE", sandbox._tri("DEOBF_NATIVE"))
    monkeypatch.setattr(sandbox, "USE_SERVER_KEY", sandbox._tri("DEOBF_USE_SERVER_KEY"))
    create_app({"ACCESS_CODE": CODE})
    assert sandbox.USE_SERVER_KEY is False and sandbox.NATIVE is False


def test_missing_server_key_is_explained_on_the_page(gated, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    c = gated().test_client()
    login(c)
    assert "ANTHROPIC_API_KEY" in c.get("/").get_data(as_text=True)               # sababi aniq aytiladi


def test_site_name_is_configurable(gated, monkeypatch):
    monkeypatch.setenv("DEOBF_SITE_NAME", "Kod Ochar")
    c = gated().test_client()
    assert "Kod Ochar" in c.get("/login").get_data(as_text=True)
    login(c)
    html = c.get("/").get_data(as_text=True)
    assert "<title>Kod Ochar</title>" in html and "<h1>Kod Ochar</h1>" in html
