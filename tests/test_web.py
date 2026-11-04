"""Web UI va hisobot testlari (Flask test mijozi bilan)."""

from pathlib import Path

import pytest

from deobf_agent import report, sandbox
from deobf_agent.agent import AgentConfig, deobfuscate_text
from deobf_agent.web.app import create_app
from tests.fakes import FakeClient, FakeResponse, make_result

ROOT = Path(__file__).resolve().parents[1]
S1 = (ROOT / "samples/decompiled/s1_mba.angr.c").read_text()


def test_index_page_lists_samples():
    client = create_app().test_client()
    html = client.get("/").get_data(as_text=True)
    assert "deobf-agent" in html and "s3_flatten" in html and "Claude Haiku 5.5" in html


def test_analyze_offline_and_download(tmp_path):
    client = create_app({"CACHE_DIR": str(tmp_path)}).test_client()
    resp = client.post("/analyze", data={"code": S1, "engine": "offline", "effort": "low", "lang": "uz"})
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "status-verified" in html and "a0 + a1" in html
    rid = html.split("/download/")[1].split(".")[0]
    md = client.get(f"/download/{rid}.md").get_data(as_text=True)
    assert md.startswith("# Deobfuskatsiya hisoboti")
    assert client.get(f"/download/{rid}.json").json["functions"][0]["function"] == "mix"


def test_analyze_with_llm_fake():
    good = make_result("unsigned int mix(unsigned int a, unsigned int b)\n{ return ((a + b) ^ (a - b)) | (a & 0xFFu); }",
                       "mix", suggested_name="mix_values", summary="Ikki sonni aralashtiradi.")
    client = create_app({"CACHE_DIR": None, "CLIENT": FakeClient([FakeResponse(good)])}).test_client()
    html = client.post("/analyze", data={"code": S1, "engine": "haiku"}).get_data(as_text=True)
    assert "mix_values" in html and "Ikki sonni aralashtiradi." in html and "claude-haiku-5-5" in html


def test_empty_input_error():
    client = create_app().test_client()
    html = client.post("/analyze", data={"code": "  ", "engine": "offline"}).get_data(as_text=True)
    assert "Psevdokod kiritilmadi" in html


@pytest.fixture
def public_app(monkeypatch):
    # Public rejim DEOBF_PUBLIC orqali yoqiladi; test uchun to'g'ridan-to'g'ri o'rnatamiz.
    monkeypatch.setattr(sandbox, "PUBLIC", True)
    return create_app()


def test_public_mode_security_and_byok(public_app):
    c = public_app.test_client()
    r = c.get("/")
    assert r.headers["X-Frame-Options"] == "DENY" and r.headers["Referrer-Policy"] == "same-origin"
    csp = r.headers["Content-Security-Policy"]
    assert "script-src 'self'" in csp and "cdnjs" not in csp and "unsafe-inline'; img" in csp   # skriptlar faqat o'zimizdan
    assert 'name="api_key"' in r.get_data(as_text=True)          # tashrif buyuruvchi o'z kalitini kiritadi
    assert public_app.config["CACHE_DIR"] is None                # public rejimda disk kesh o'chirilgan
    # Claude modeli kalitsiz rad etiladi
    h = c.post("/analyze", data={"code": "int f(int a){return a+0;}", "engine": "sonnet"}).get_data(as_text=True)
    assert "API kalitingizni kiriting" in h
    # offline rejim kalitsiz ishlaydi
    assert "status-" in c.post("/analyze", data={"code": "int f(int a){return a+0;}",
                                                  "engine": "offline"}).get_data(as_text=True)


def test_public_mode_rejects_include_and_long_input(public_app):
    c = public_app.test_client()
    h = c.post("/analyze", data={"code": "#include <stdio.h>\nint f(int a){return a;}",
                                 "engine": "offline"}).get_data(as_text=True)
    assert "#include" in h
    h = c.post("/analyze", data={"code": "int f(){return 0;}\n" + "//x\n" * 20000,
                                 "engine": "offline"}).get_data(as_text=True)
    assert "juda uzun" in h


def test_report_formats_escape_html():
    code = S1.replace("unsigned int v0;", "unsigned int v0; /* <script>alert(1)</script> */")
    parsed, reps = deobfuscate_text(code, AgentConfig(offline=True))
    html = report.to_html(parsed, reps)
    assert "<script>alert(1)</script>" not in html            # XSS himoyasi: matn ekranlanadi
    assert "&lt;script&gt;" in html
    assert report.to_markdown(parsed, reps).count("```c") >= 2


def test_rate_limiter_survives_many_clients_and_denials_do_not_extend_window():
    from deobf_agent.web.app import RateLimiter

    lim = RateLimiter(2, 100)
    assert lim.allow("a", 0) and lim.allow("a", 1) and not lim.allow("a", 2)
    assert lim.allow("a", 101)                       # rad etilgan urinish oynani uzaytirmagan edi
    for i in range(5000):                            # ko'p mijoz: tozalashdan keyin ham yangi IP xato bermaydi
        assert lim.allow(f"ip{i}", 200 + i * 0.001)
    assert lim.allow("yangi", 300)


def test_personal_mode_rejects_foreign_host_and_cross_site_post():
    app = create_app()
    c = app.test_client()
    assert c.get("/", headers={"Host": "rebind.example"}).status_code == 403        # DNS rebinding
    assert c.post("/analyze", data={"code": "int f(){return 0;}", "engine": "offline"},
                  headers={"Origin": "http://evil.example"}).status_code == 403     # boshqa sayt formasi
    assert c.get("/", headers={"Host": "127.0.0.1:5000"}).status_code == 200
    ok = c.post("/analyze", data={"code": "int f(){return 0;}", "engine": "offline"}, headers={"Origin": "http://localhost"})
    assert ok.status_code == 200                                                     # o'z saytimizdan kelgan forma o'tadi
    assert c.post("/analyze", data={"code": "x"}, headers={"Origin": "null"}).status_code == 403
    assert c.post("/analyze", data={"code": "x"}, headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403


def test_public_mode_function_cap_check_key_throttle_and_no_key_echo(public_app):
    c = public_app.test_client()
    many = "\n".join(f"int f{i}(int a) {{ return a + {i}; }}" for i in range(6))
    h = c.post("/analyze", data={"code": many, "engine": "offline"}).get_data(as_text=True)
    assert "ko&#39;pi bilan 3 ta funksiya" in h
    secret = "sk-ant-api03-ZZZZZZZZZZZZZZZZZZZZZZZZ"
    h = c.post("/analyze", data={"code": "int f(int a){return a;}", "engine": "sonnet", "api_key": secret}
               ).get_data(as_text=True)
    assert "ZZZZZZZZ" not in h                       # kalit hech qachon sahifaga qaytarilmaydi
    codes = [c.post("/api/check-key", data={"model": "sonnet", "api_key": "yaroqsiz"}).status_code for _ in range(8)]
    assert 429 in codes                              # kalit tekshiruvi cheklangan (kalit "oracle"i bo'lmasin)


def test_error_pages_are_friendly():
    c = create_app().test_client()
    r = c.get("/download/yoq.md")
    assert r.status_code == 404 and "topilmadi" in r.get_data(as_text=True)


def test_report_html_is_self_contained_and_report_js_is_not_escaped():
    parsed, reps = deobfuscate_text(S1, AgentConfig(offline=True))
    html = report.to_html(parsed, reps)
    assert "cdnjs" not in html and "http://" not in html.replace("http://www.w3.org", "")   # internetsiz ochiladi
    assert 'aria-pressed' in html and "classList.toggle(&" not in html                       # skript buzilmagan
