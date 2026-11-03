"""Tushuntiruvchi modul (narrate) va offline bloklar testlari: matnlar aniq va tushunarli bo'lishi shart."""

import json
from pathlib import Path

import pytest

from deobf_agent import compiler, narrate
from deobf_agent.agent import AgentConfig, deobfuscate_text

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = sorted((ROOT / "samples" / "decompiled").glob("*.angr.c"))
needs_cc = pytest.mark.skipif(compiler.find_compiler() is None, reason="C kompilyatori yo'q")


def meaning(code, name, params, decoded=None):
    return narrate.meaning(name, params, code, decoded or {})


def test_statement_sentences_are_concrete():
    assert narrate.describe_simple_stmt("v2 = v1 % v0") == "`v2` ga `v1` ni `v0` ga bo'lgandagi qoldiqni yozadi."
    assert narrate.describe_simple_stmt("v0 = v0 + 1") == "`v0` ni 1 ga oshiradi."
    assert narrate.describe_simple_stmt("a0[v0] = a0[v0] ^ (char)v3").startswith("`a0[v0]` ni `(char)v3` bilan XOR qilib")
    s = narrate.describe_simple_stmt("v2 = v1 % v0", simple=True)
    assert "`" not in s and "qoldiq" in s


def test_swap_idiom_and_nested_structure():
    code = "void f(int *a, int n)\n{\n    int t;\n    while (n > 0) {\n        if (a[0] > a[1]) {\n            t = a[0];\n            a[0] = a[1];\n            a[1] = t;\n        }\n        n = n - 1;\n    }\n}"
    steps = narrate.walkthrough(code)
    assert len(steps) == 1 and steps[0].title.startswith("Takrorlash")
    assert "o'rnini almashtiradi" in steps[0].text and "• " in steps[0].text


def test_function_meaning_is_recognised():
    gcd = "unsigned gcd(unsigned a, unsigned b)\n{\n    unsigned t;\n    while (b) {\n        t = a % b;\n        a = b;\n        b = t;\n    }\n    return a;\n}"
    assert "EKUB" in meaning(gcd, "gcd", [("unsigned", "a"), ("unsigned", "b")])[0]
    fnv = "unsigned h(unsigned a)\n{\n    unsigned v = 2166136261;\n    v ^= a;\n    v *= 16777619;\n    return v;\n}"
    assert "FNV-1a" in meaning(fnv, "h", [("unsigned", "a")])[0]
    mix = "unsigned mix(unsigned a, unsigned b)\n{\n    unsigned x = a + b;\n    unsigned y = a - b;\n    return x ^ y;\n}"
    text, simple = meaning(mix, "mix", [("unsigned", "a"), ("unsigned", "b")])
    assert "(a + b) ^ (a - b)" in text and "`" not in simple


@needs_cc
@pytest.mark.parametrize("path", SAMPLES, ids=lambda p: p.name.split(".")[0])
def test_offline_blocks_are_understandable(path):
    _, reports = deobfuscate_text(path.read_text(encoding="utf-8"), AgentConfig(offline=True))
    for rep in reports:
        r = rep.result
        assert r.simple_summary.strip() and r.simple_summary != r.summary
        assert "chalkashtirish belgilari topilmadi" not in r.summary or not r.techniques
        assert r.blocks, f"{rep.function.name}: bloklar yo'q"
        titles = [b.title for b in r.blocks]
        assert not {"MBA ifoda", "Soddalashtirish", "O'lik / keraksiz kod"} & set(titles)    # usul nomi emas, nima qilishi
        for b in r.blocks:
            assert b.explanation.strip() and b.simple.strip(), b.title
            assert b.simple != b.explanation
            assert "`" not in b.simple and "0x" not in b.simple, (b.title, b.simple)         # oddiy tilda kod belgilari yo'q
        # bir xil matnli takroriy bloklar bo'lmasin
        keys = [(b.title, b.explanation) for b in r.blocks]
        assert len(keys) == len(set(keys))


@needs_cc
def test_summary_says_what_the_function_computes():
    expected = {"s3_flatten": "EKUB", "s5_combined": "FNV-1a", "s6_buffer": "XOR", "s8_sort": "saralaydi"}
    for sid, word in expected.items():
        text = (ROOT / "samples" / "decompiled" / f"{sid}.angr.c").read_text(encoding="utf-8")
        _, reports = deobfuscate_text(text, AgentConfig(offline=True))
        assert word in reports[0].result.summary, (sid, reports[0].result.summary)


def test_long_chained_straight_line_code_does_not_blow_up():
    # TEA kabi: har bir oraliq o'zgaruvchi oldingisidan ikki marta foydalanadi — qiymat qo'yish eksponensial o'sar edi
    lines = ["v0 = a1;"] + [f"v{i} = v{i - 1} + (v{i - 1} ^ {i});" for i in range(1, 60)]
    code = "unsigned f(unsigned a1)\n{\n    " + "\n    ".join(lines) + "\n    return v59;\n}"
    import time

    t0 = time.time()
    text, simple = narrate.meaning("f", [("unsigned", "a1")], code)
    assert time.time() - t0 < 5 and text and simple
    assert narrate.straight_line_formula(narrate.parse_function(code)) is None      # juda katta: formula tuzilmaydi
