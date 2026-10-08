"""Agent sikli testlari: tekshiruv, xatoni qaytarish, qayta urinish, offline rejim."""

import json
from pathlib import Path

import pytest

from deobf_agent import compiler
from deobf_agent.agent import AgentConfig, deobfuscate_text
from tests.fakes import FakeClient, FakeResponse, make_result

ROOT = Path(__file__).resolve().parents[1]
needs_cc = pytest.mark.skipif(compiler.find_compiler() is None, reason="C kompilyatori yo'q")

S1 = (ROOT / "samples/decompiled/s1_mba.angr.c").read_text()
GOOD = "unsigned int mix(unsigned int a, unsigned int b)\n{\n    return ((a + b) ^ (a - b)) | (a & 0xFFu);\n}\n"
WRONG = "unsigned int mix(unsigned int a, unsigned int b)\n{\n    return ((a | b) ^ (a - b)) | (a & 0xFFu);\n}\n"


@needs_cc
def test_agent_fixes_wrong_answer():
    client = FakeClient([FakeResponse(make_result(WRONG, "mix")), FakeResponse(make_result(GOOD, "mix"))])
    cfg = AgentConfig(model="haiku", cache_dir=None, client=client)
    _, reports = deobfuscate_text(S1, cfg)
    r = reports[0]
    assert [a.status for a in r.attempts] == ["mismatch", "verified"]
    assert r.verification.status == "verified"
    assert r.result.c_code == GOOD
    # 2-so'rovda xato misollari Claude'ga yuborilgan
    fix_msg = client.messages.calls[1]["messages"][-1]["content"]
    assert "Differential testing" in fix_msg and "MISMATCH" in fix_msg
    assert r.usage.requests == 2


@needs_cc
def test_agent_compile_error_feedback():
    broken = "unsigned int mix(unsigned int a, unsigned int b) { return a + ; }"
    client = FakeClient([FakeResponse(make_result(broken, "mix")), FakeResponse(make_result(GOOD, "mix"))])
    _, reports = deobfuscate_text(S1, AgentConfig(cache_dir=None, client=client))
    assert [a.status for a in reports[0].attempts] == ["compile_error", "verified"]
    assert "gcc compilation errors" in client.messages.calls[1]["messages"][-1]["content"]


@needs_cc
def test_agent_keeps_best_after_max_rounds():
    client = FakeClient([FakeResponse(make_result(WRONG, "mix")) for _ in range(2)])
    _, reports = deobfuscate_text(S1, AgentConfig(cache_dir=None, client=client, max_rounds=2))
    assert len(reports[0].attempts) == 2
    assert reports[0].verification.status == "mismatch"           # yolg'on "muvaffaqiyat" yo'q


@needs_cc
def test_llm_error_falls_back_to_offline():
    client = FakeClient([FakeResponse(None, stop_reason="refusal")])
    _, reports = deobfuscate_text(S1, AgentConfig(cache_dir=None, client=client))
    r = reports[0]
    assert r.engine == "offline" and "bosh tortdi" in r.error
    assert r.verification.status == "verified"


@needs_cc
def test_offline_all_samples_verified():
    manifest = json.loads((ROOT / "samples/manifest.json").read_text())
    for s in manifest["samples"]:
        text = (ROOT / "samples/decompiled" / f"{s['id']}.angr.c").read_text()
        _, reports = deobfuscate_text(text, AgentConfig(offline=True))
        assert reports[0].verification.status == "verified", (s["id"], reports[0].verification.details)


def test_unknown_function_name():
    with pytest.raises(ValueError, match="topilmadi"):
        deobfuscate_text(S1, AgentConfig(offline=True), function="yoq_funksiya")
