"""O'rnatish va sozlash testlari: .env o'qish (turli kodlashlar), kalitni tekshirish, diagnostika."""

import os

import anthropic
import httpx2
import pytest

from deobf_agent import cli, llm
from deobf_agent.web.app import create_app
from tests.fakes import FakeClient

LINE = "ANTHROPIC_API_KEY=sk-ant-api03-TESTKEY1234567890\r\n"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("DEOBF_MODEL", raising=False)


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig", "utf-16", "utf-16-le"])
def test_dotenv_any_encoding(tmp_path, encoding):
    # PowerShell "echo ... > .env" UTF-16 yozadi, Notepad — UTF-8 BOM bilan
    p = tmp_path / ".env"
    p.write_bytes(LINE.encode(encoding))
    assert llm.load_dotenv(p) == p
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-api03-TESTKEY1234567890"


def test_dotenv_variants(tmp_path, monkeypatch):
    p = tmp_path / ".env"
    p.write_text('# izoh\nset DEOBF_MODEL = sonnet\nexport ANTHROPIC_API_KEY="sk-ant-xyz"\n', encoding="utf-8")
    llm.load_dotenv(p)
    assert os.environ["DEOBF_MODEL"] == "sonnet" and os.environ["ANTHROPIC_API_KEY"] == "sk-ant-xyz"
    assert llm.resolve_model(None) == "claude-sonnet-5-5"


def test_dotenv_only_key_and_txt_extension(tmp_path, monkeypatch):
    # Notepad ".env" ni ".env.txt" qilib saqlashi mumkin; faylga faqat kalitning o'zi yozilgan bo'lishi mumkin
    (tmp_path / ".env.txt").write_text("sk-ant-onlykey\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(llm, "PROJECT_ROOT", tmp_path)
    assert llm.find_dotenv().name == ".env.txt"
    llm.load_dotenv()
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-onlykey"


def test_mask_key():
    assert llm.mask_key("sk-ant-api03-ABCDEFGHIJKLMNOP1234") == "sk-ant-api03...1234"
    assert llm.mask_key(None) == "(yo'q)"


def test_check_api_key_ok_and_errors(monkeypatch):
    ok, msg = llm.check_api_key("haiku", client=FakeClient())
    assert ok and "ishlayapti" in msg
    req = httpx2.Request("GET", "https://api.anthropic.com/v1/models/x")
    err = anthropic.AuthenticationError("bad", response=httpx2.Response(401, request=req), body=None)
    ok, msg = llm.check_api_key("haiku", client=FakeClient(model_error=err))
    assert not ok and "noto'g'ri" in msg
    err = anthropic.NotFoundError("nf", response=httpx2.Response(404, request=req), body=None)
    ok, msg = llm.check_api_key("claude-yoq", client=FakeClient(model_error=err))
    assert not ok and "mavjud emas" in msg


def test_check_without_key_is_clear():
    ok, msg = llm.check_api_key("haiku")
    assert not ok and ".env" in msg


def test_cli_check_offline(capsys):
    code = cli.main(["check", "--no-network"])
    out = capsys.readouterr().out
    assert "Python" in out and "ANTHROPIC_API_KEY" in out and code == 1


def test_web_check_key_endpoint():
    client = create_app({"CLIENT": FakeClient()}).test_client()
    data = client.post("/api/check-key", data={"model": "sonnet"}).json
    assert data["ok"] and "claude-sonnet-5-5" in data["message"]
    assert client.post("/api/check-key", data={"model": "offline"}).json["ok"]


def test_web_custom_model_requires_name():
    client = create_app().test_client()
    html = client.post("/analyze", data={"code": "int f(int a){return a;}", "engine": "custom"}).get_data(as_text=True)
    assert "model nomi yozilmagan" in html
