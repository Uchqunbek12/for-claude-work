"""Flattening'ni avtomatik yechish (unflatten) testlari."""

from pathlib import Path

import pytest

from deobf_agent import compiler, harness, parser
from deobf_agent.unflatten import unflatten

ROOT = Path(__file__).resolve().parents[1]
needs_cc = pytest.mark.skipif(compiler.find_compiler() is None, reason="C kompilyatori yo'q")

CASES = ["samples/decompiled/s3_flatten.angr.c", "samples/decompiled/s5_combined.angr.c",
         "samples/src/obf/s3_flatten.c", "samples/src/obf/s5_combined.c"]


@needs_cc
@pytest.mark.parametrize("path", CASES)
def test_unflatten_equivalent(path):
    raw = (ROOT / path).read_text()
    p = parser.parse(raw)
    f = p.functions[0]
    new = unflatten(f.text)
    assert new is not None
    assert "switch" not in new and "while (" in new
    d = harness.differential_test(raw, f.name, p.preamble + "\n" + new, f.name, f.ret_type, f.param_types)
    assert d.status == "equivalent", d.details


def test_if_else_diamond():
    code = """int f(int x) {
    int r = 0; int s = 1;
    while (1) {
        switch (s) {
        case 1: s = x > 0 ? 2 : 3; break;
        case 2: r = 10; s = 4; break;
        case 3: r = 20; s = 4; break;
        case 4: return r + 1;
        }
    }
}"""
    new = unflatten(code)
    assert new is not None and "if (x > 0) {" in new and "} else {" in new and "return r + 1;" in new


def test_bails_on_conditional_state_change():
    code = """int f(int x) {
    int s = 1;
    while (1) {
        switch (s) {
        case 1: if (x) s = 2; else s = 3; break;
        case 2: return 1;
        case 3: return 2;
        }
    }
}"""
    assert unflatten(code) is None          # xavfsiz yechib bo'lmaydi -> o'zgartirmaydi


def test_no_flattening_returns_none():
    assert unflatten("int f(int a) { return a + 1; }") is None
