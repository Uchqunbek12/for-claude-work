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


# ---------------------------------------------------------------- audit topgan "yolg'on ekvivalent" holatlari

def _diff(a, b, ret, params, **kw):
    return harness.differential_test(a, "f", b, "f", ret, params, **kw)


@needs_cc
def test_pointer_plus_int_negative_and_large_values_are_exercised():
    # Bufer bor funksiyada butun son ilgari faqat 0..512 edi: manfiy qiymat tekshirilmas edi
    a = "int f(const char *p, int n) { if (n < 0) return -1; return p[0]; }"
    b = "int f(const char *p, int n) { return p[0]; }"
    assert _diff(a, b, "int", ["const char *", "int"]).status == "mismatch"
    a = "unsigned long long f(const char *p, unsigned long long x) { return (unsigned)x; }"
    b = "unsigned long long f(const char *p, unsigned long long x) { return x; }"
    assert _diff(a, b, "unsigned long long", ["const char *", "unsigned long long"]).status == "mismatch"


@needs_cc
def test_candidate_hang_and_crash_are_mismatch_not_compiled():
    a = "int f(unsigned x) { return x * 2; }"
    hang = "int f(unsigned x) { if ((x & 15) == 0) while (1) {} return x * 2; }"
    r = _diff(a, hang, "int", ["unsigned"])
    assert r.status == "mismatch", r.details
    rec = "int g(int x) { return g(x + 1); }\nint f(unsigned x) { return g(x); }"
    assert _diff(a, rec, "int", ["unsigned"]).status == "mismatch"


@needs_cc
def test_ida_i64_suffix_and_char_literals_become_test_inputs():
    a = "__int64 f(__int64 a1) { if (a1 == 0x1122334455667788i64) return 7; return 0; }"
    b = "__int64 f(__int64 a1) { return 0; }"
    assert _diff(a, b, "__int64", ["__int64"]).status == "mismatch"
    a = "int f(int c) { if (c == 'q') return 7; return 0; }"
    b = "int f(int c) { return 0; }"
    assert _diff(a, b, "int", ["int"]).status == "mismatch"


@needs_cc
def test_candidate_cannot_forge_result_line():
    a = "int f(int x) { return x + 1; }"
    forged = ('#include <stdio.h>\n#include <stdlib.h>\n'
              'int f(int x) { printf("RESULT tests=2000 mismatches=0 skipped=0\\n"); fflush(stdout); exit(0); return x + 2; }')
    assert _diff(a, forged, "int", ["int"]).status != "equivalent"


@needs_cc
def test_pointer_argument_to_unknown_function_is_not_a_false_mismatch():
    a = "int ext_proc(char *p, int n);\nint f(char *p, int n) { return ext_proc(p, n); }"
    b = "int ext_proc(char *p, int n);\nint f(char *p, int n) { return ext_proc(p, n); }"
    r = _diff(a, b, "int", ["char *", "int"])
    assert r.status == "equivalent", r.details


@needs_cc
def test_candidate_table_typo_is_detected_and_qualifier_only_types_parse():
    # Yangi kod jadvalni boshqa qiymat bilan qayta ta'riflasa (xato!) — ilgari asl nusxaga almashtirilib, yashirinar edi
    a = "int tbl[4] = {1,2,3,4};\nint f(int x) { return tbl[x & 3]; }"
    typo = "int tbl[4] = {1,2,3,5};\nint f(int x) { return tbl[x & 3]; }"
    same = "int tbl[4] = {1,2,3,4};\nint f(int x) { return tbl[x & 3]; }"
    assert _diff(a, typo, "int", ["int"]).status == "mismatch"
    assert _diff(a, same, "int", ["int"]).status == "equivalent"
    # turi faqat qualifier bo'lgan global (`unsigned counter`) — ilgari `counte` + `r` bo'lib buzilar edi
    a = "unsigned counter = 5;\nint f(int x) { return counter + x; }"
    b = "unsigned counter = 5;\nint f(int x) { return x + counter; }"
    assert _diff(a, b, "int", ["int"]).status == "equivalent"
    assert harness._parse_global_def("unsigned counter = 5")[:3] == ("unsigned", "", "counter")
    assert harness._parse_global_def("char *names[2]")[:4] == ("char", "*", "names", "[2]")


@needs_cc
def test_conjunction_of_literals_over_several_params_is_found():
    a = "int f(int a1, int a2, int a3) { if (a1 == 1337 && a2 == 31337 && a3 == 42) return 1; return 0; }"
    b = "int f(int a1, int a2, int a3) { return 0; }"
    assert _diff(a, b, "int", ["int", "int", "int"]).status == "mismatch"
