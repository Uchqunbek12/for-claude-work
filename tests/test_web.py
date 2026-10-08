"""Web UI va hisobot testlari (Flask test mijozi bilan)."""

from pathlib import Path

from deobf_agent import report
from deobf_agent.agent import AgentConfig, deobfuscate_text
from deobf_agent.web.app import create_app
from tests.fakes import FakeClient, FakeResponse, make_result

ROOT = Path(__file__).resolve().parents[1]
S1 = (ROOT / "samples/decompiled/s1_mba.angr.c").read_text()


def test_index_page_lists_samples():
    client = create_app().test_client()
    html = client.get("/").get_data(as_text=True)
    assert "Deobf Agent" in html and "s3_flatten" in html and "Claude Haiku 5.5" in html


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


def test_report_formats_escape_html():
    code = S1.replace("unsigned int v0;", "unsigned int v0; /* <script>alert(1)</script> */")
    parsed, reps = deobfuscate_text(code, AgentConfig(offline=True))
    html = report.to_html(parsed, reps)
    assert "<script>alert(1)</script>" not in html            # XSS himoyasi: matn ekranlanadi
    assert "&lt;script&gt;" in html
    assert report.to_markdown(parsed, reps).count("```c") >= 2
