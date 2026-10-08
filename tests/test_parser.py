"""Parser testlari: IDA, Ghidra, angr va oddiy C uslubidagi kirishlar."""

from pathlib import Path

from deobf_agent import parser

ROOT = Path(__file__).resolve().parents[1]

# Quyidagi parchalar parser uchun test ma'lumotlari: IDA va Ghidra chiqaradigan
# psevdokodning tipik ko'rinishini takrorlaydi.
IDA_SNIPPET = '''// write access to const memory has been detected, the output may be wrong!
__int64 __fastcall sub_401136(unsigned int a1, char **a2, int a3@<eax>)
{
  int v4; // [rsp+1Ch] [rbp-4h]

  v4 = sub_401000(a1, "a{b");   /* satr ichidagi { qavs hisoblanmasligi kerak */
  if ( v4 > 0 ) { LODWORD(v4) = 5; }
  return (unsigned int)v4;
}
unsigned char byte_4020[4] = { 0x14, 0x39, 0x30, 0x30 };
'''

GHIDRA_SNIPPET = '''
/* WARNING: Unknown calling convention */
undefined8 FUN_00101149(uint param_1,undefined4 *param_2)
{
  int iVar1;
  iVar1 = FUN_00101000(param_1);
  *param_2 = DAT_00104010;
  return CONCAT44(iVar1,param_1);
}
'''


def test_ida_style():
    r = parser.parse(IDA_SNIPPET)
    assert r.style == "ida"
    assert len(r.functions) == 1
    f = r.functions[0]
    assert f.name == "sub_401136"
    assert f.ret_type == "__int64"
    assert [(p.type, p.name) for p in f.params] == [("unsigned int", "a1"), ("char **", "a2"), ("int", "a3")]
    assert f.calls == ["sub_401000"]          # LODWORD makros, chaqiruv emas
    assert f.start_line == 2
    assert r.data_blobs["byte_4020"] == bytes([0x14, 0x39, 0x30, 0x30])


def test_ghidra_style():
    r = parser.parse(GHIDRA_SNIPPET)
    assert r.style == "ghidra"
    f = r.functions[0]
    assert f.name == "FUN_00101149"
    assert f.ret_type == "undefined8"
    assert f.param_types == ["uint", "undefined4 *"]
    assert f.calls == ["FUN_00101000"]


def test_multiple_functions_and_struct_skipped():
    src = "struct S { int a; };\nint f(void) { return 1; }\nstatic int g(int x)\n{\n  return f() + x;\n}\n"
    r = parser.parse(src)
    assert [f.name for f in r.functions] == ["f", "g"]
    assert r.functions[1].params[0].name == "x"
    assert r.functions[1].calls == ["f"]


def test_angr_samples():
    # Har bir namuna kamida bitta funksiyaga ega; s7_calls ikkita (rotl32 + rot_hash).
    expected = {"s7_calls": 2}
    for path in sorted((ROOT / "samples" / "decompiled").glob("*.angr.c")):
        r = parser.parse(path.read_text(encoding="utf-8"))
        assert r.style == "angr", path.name
        assert len(r.functions) == expected.get(path.name.split(".")[0], 1), path.name
    s4 = parser.parse((ROOT / "samples" / "decompiled" / "s4_strings.angr.c").read_text())
    assert len(s4.data_blobs["ENC"]) == 27
    s7 = parser.parse((ROOT / "samples" / "decompiled" / "s7_calls.angr.c").read_text())
    assert [f.name for f in s7.functions] == ["rotl32", "rot_hash"]
    assert s7.functions[1].calls == ["rotl32"]


def test_normalize_type():
    assert parser.normalize_type("char*") == "char *"
    assert parser.normalize_type("char * *") == "char **"
    assert parser.normalize_type("unsigned   int") == "unsigned int"
