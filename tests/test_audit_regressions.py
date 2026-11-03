"""Mustaqil audit topgan xatolar uchun regressiya testlari: har bir test auditdagi aniq kirishni qayta ishlatadi."""

import pytest

from deobf_agent import compiler, parser
from deobf_agent.agent import AgentConfig, deobfuscate_text

needs_cc = pytest.mark.skipif(compiler.find_compiler() is None, reason="C kompilyatori yo'q")


def run(code: str, **kw):
    _, reps = deobfuscate_text(code, AgentConfig(offline=True, **kw))
    return reps[0]


@needs_cc
@pytest.mark.parametrize("cond", [
    "a1 == 1337 && a2 == 31337 && a3 == 42",
    "(a1 >> 16) == 0xDEAD",
    "a1 + 1000 == 5000",
    "a1 * 3 == 99999",
])
def test_data_dependent_equality_is_not_removed_as_opaque_predicate(cond):
    # Ilgari bunday shartlar "doim yolg'on" deb o'chirilib, natija «Tasdiqlandi» ko'rsatilar edi
    rep = run(f"int check3(int a1, int a2, int a3)\n{{\n    if ({cond}) return 1;\n    return 0;\n}}")
    assert "return 1" in rep.result.c_code
    assert rep.verification.status != "mismatch"


@needs_cc
def test_typed_rewrites_keep_result_type():
    rep = run("long long f(short c, long long b)\n{\n    return (unsigned short)(c - (c & b) + (c & b));\n}")
    assert rep.verification.status == "verified", rep.verification.details
    rep = run("int s1(int a, int b)\n{\n    if (((unsigned)a ^ b) + 2*(a & b) > 100) return 1;\n    return 0;\n}")
    assert rep.verification.status == "verified", rep.verification.details


@needs_cc
def test_side_effects_are_not_dropped():
    rep = run("unsigned f(unsigned a, unsigned b)\n{\n    unsigned i = 0;\n    unsigned r = i++ + ((a ^ b) + 2*(a & b));\n    return r + i;\n}")
    assert rep.verification.status in ("verified", "compiled"), rep.verification.details
    rep = run("int next_val(void);\nint f(int x)\n{\n    if (next_val() == next_val()) return x + 1;\n    return x;\n}")
    assert rep.result.c_code.count("next_val") >= 2


@needs_cc
def test_string_and_char_literals_in_preamble_survive():
    rep = run('static const char greeting[] = "hello world";\nunsigned pick(unsigned i)\n{\n    return greeting[i % 11];\n}')
    assert "hello world" in rep.result.c_code and rep.verification.status == "verified"
    rep = run("#define KEYCH 'k'\nchar sep = ',';\nunsigned mix(unsigned a, unsigned b)\n{\n    return (a ^ b) + 2*(a & b);\n}")
    assert "'k'" in rep.result.c_code and "','" in rep.result.c_code


@pytest.mark.parametrize("sig", [
    "__attribute__((noinline)) unsigned mix(unsigned a, unsigned b)",
    "__declspec(dllexport) unsigned mix(unsigned a, unsigned b)",
    "unsigned __int64 __usercall mix@<rax>(unsigned a@<edi>, unsigned b@<esi>)",
])
def test_parser_accepts_attributes_and_usercall(sig):
    r = parser.parse(sig + "\n{\n    return a + b;\n}")
    assert [f.name for f in r.functions] == ["mix"] and len(r.functions[0].params) == 2


@pytest.mark.parametrize("code", [
    "double scale(double x)\n{\n    return x * 0.05;\n}",
    "int f(int a)\n{\n    return a + 0755;\n}",
])
def test_float_and_octal_literals_do_not_crash(code):
    assert run(code).function.name in ("scale", "f")


@needs_cc
def test_dangling_else_never_swallows_following_statement():
    rep = run("int e1(int a1, int a2)\n{\n    int v3, v4;\n    v4 = (a2 ^ 5) + 2 * (a2 & 5);\n"
              "    if (a1 > 0) v4 = v4 + a1; else v3 = a2 * 7;\n    return v4;\n}")
    assert rep.verification.status == "verified", rep.verification.details
    rep = run("int g(int a1)\n{\n    int r = 0;\n    if (a1 > 3) { r = 1; } else if (a1 * 0 == 1) { r = 2; }\n    r += 5;\n    return r;\n}")
    assert rep.verification.status == "verified", rep.verification.details


@needs_cc
def test_global_stores_are_not_junk():
    rep = run("int dword_404010;\nint d2(int a1)\n{\n    dword_404010 = a1 * 2;\n    return a1 + 1;\n}")
    assert "dword_404010" in rep.result.c_code and rep.verification.status != "mismatch"


@needs_cc
def test_unflatten_refuses_unsafe_state_machines():
    code = """int f(int x)
{
    int r = 0, s = 1;
    while (1) {
        switch (s) {
        case 1: if (x < 0) return -1; r = x + 4; s = 2; break;
        case 2: r = r * 3; s = 3; break;
        case 3: return r;
        }
    }
}"""
    rep = run(code)
    assert rep.verification.status == "verified", rep.verification.details


@needs_cc
def test_offline_never_emits_known_wrong_code():
    # Qaysi daraja tekshiruvdan o'tmasa, oxirgi himoya (kod aslidek) ishlaydi: hech qachon «mismatch» bilan tugamaydi
    rep = run("unsigned f(unsigned a, unsigned b)\n{\n    return (a & ~b) + b;\n}")
    assert rep.verification.status != "mismatch"
