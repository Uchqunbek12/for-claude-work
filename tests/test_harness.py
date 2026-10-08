"""Differensial test (harness) va namunalar ekvivalentligi testlari."""

import json
from pathlib import Path

import pytest

from deobf_agent import compiler, harness

ROOT = Path(__file__).resolve().parents[1]
needs_cc = pytest.mark.skipif(compiler.find_compiler() is None, reason="C kompilyatori yo'q")


def test_is_integer_type():
    assert harness.is_integer_type("unsigned int")
    assert harness.is_integer_type("__int64")
    assert harness.is_integer_type("undefined4")
    assert not harness.is_integer_type("char *")
    assert not harness.is_integer_type("double")


@needs_cc
def test_equivalent_and_mismatch():
    a = "unsigned int f(unsigned int x, unsigned int y) { return x + y; }"
    b_ok = "unsigned int f(unsigned int x, unsigned int y) { return (x ^ y) + 2u * (x & y); }"
    b_bad = "unsigned int f(unsigned int x, unsigned int y) { return (x ^ y) + (x & y); }"
    assert harness.differential_test(a, "f", b_ok, "f", "unsigned int", ["unsigned int"] * 2).status == "equivalent"
    bad = harness.differential_test(a, "f", b_bad, "f", "unsigned int", ["unsigned int"] * 2)
    assert bad.status == "mismatch" and bad.mismatches > 0


@needs_cc
def test_skipped_for_unsupported_type():
    # double kabi turlar hali qo'llab-quvvatlanmaydi -> test o'tkazib yuboriladi
    r = harness.differential_test("", "f", "", "f", "int", ["double"])
    assert r.status == "skipped"


@needs_cc
def test_pointer_buffer_equivalent():
    # Ko'rsatkich (bufer) parametri bo'lgan funksiyalar endi sinaladi: bufer to'ldiriladi va solishtiriladi.
    a = "void f(unsigned char *p, int n) { for (int i = 0; i < n; i++) p[i] ^= 0x5Au; }"
    b = "void f(unsigned char *p, int n) { for (int i = 0; i < n; i++) p[i] = p[i] ^ 90; }"
    r = harness.differential_test(a, "f", b, "f", "void", ["unsigned char *", "int"])
    assert r.status == "equivalent", r.details


@needs_cc
def test_samples_clean_vs_obfuscated():
    manifest = json.loads((ROOT / "samples" / "manifest.json").read_text())
    for s in manifest["samples"]:
        clean = (ROOT / "samples/src/clean" / f"{s['id']}.c").read_text()
        obf = (ROOT / "samples/src/obf" / f"{s['id']}.c").read_text()
        r = harness.differential_test(clean, s["function"], obf, s["function"], s["ret"], s["params"])
        assert r.status == "equivalent", (s["id"], r.details)
