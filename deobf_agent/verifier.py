"""Natijani tekshirish: kompilyatsiya + differensial test.

Tekshiruv bosqichlari:
  1. Sintaksis: yangi C kod gcc'dan o'tadimi?
  2. Shakl: funksiya nomi va parametrlar soni aslidagidekmi? (aks holda solishtirib bo'lmaydi)
  3. Xatti-harakat: asl psevdokod va yangi kod minglab tasodifiy kirishda bir xil natija beradimi?

Holatlar (status):
  verified       — kompilyatsiya bo'ldi va barcha testlar mos keldi (eng yaxshi natija)
  compiled       — kompilyatsiya bo'ldi, lekin xatti-harakatni avtomatik solishtirib bo'lmadi
                   (masalan, funksiya ko'rsatkich qabul qiladi yoki tashqi funksiya chaqiradi)
  mismatch       — testlarda farq topildi (natija NOTO'G'RI)
  compile_error  — kod kompilyatsiya bo'lmadi
  no_compiler    — tizimda gcc/clang yo'q, tekshirib bo'lmadi
"""

from __future__ import annotations

import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from . import compiler, harness, parser
from .models import FunctionInfo, ParsedInput

STATUS_UZ = {
    "verified": "✅ Tasdiqlandi: kompilyatsiya bo'ldi va asl kod bilan ekvivalent",
    "compiled": "🟡 Kompilyatsiya bo'ldi, xatti-harakat avtomatik solishtirilmadi",
    "mismatch": "❌ Asl koddan farq qiladi",
    "compile_error": "❌ Kompilyatsiya xatosi",
    "no_compiler": "⚪ Tekshirilmadi (C kompilyatori yo'q)",
}
STATUS_RANK = {"verified": 4, "compiled": 3, "no_compiler": 2, "mismatch": 1, "compile_error": 0}


@dataclass
class VerifyReport:
    status: str
    details: str = ""
    problems: str = ""            # LLM'ga qaytariladigan muammo matni (bo'sh = muammo yo'q)
    tests: int = 0
    mismatches: int = 0

    @property
    def ok(self) -> bool:
        return self.status in ("verified", "compiled", "no_compiler")

    @property
    def label_uz(self) -> str:
        return STATUS_UZ.get(self.status, self.status)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["label"] = self.label_uz
        return d


def verify(parsed: ParsedInput, func: FunctionInfo, c_code: str, n_tests: int = 2000) -> VerifyReport:
    if compiler.find_compiler() is None:
        return VerifyReport("no_compiler", details="gcc yoki clang topilmadi — natija tekshirilmadi")

    with tempfile.TemporaryDirectory(prefix="deobf_verify_") as tmp:
        syn = compiler.syntax_check(c_code, Path(tmp))
    if not syn.ok:
        return VerifyReport("compile_error", details=syn.errors,
                            problems="gcc compilation errors:\n" + syn.errors)

    cand = parser.parse(c_code).get(func.name)
    if cand is None:
        return VerifyReport("compile_error", details=f"Kodda `{func.name}` funksiyasi topilmadi",
                            problems=f"c_code must define a function named exactly `{func.name}` "
                                     f"(keep the original name; put the suggested name only in suggested_name).")
    if len(cand.params) != len(func.params):
        return VerifyReport("compile_error",
                            details=f"Parametrlar soni o'zgargan: {len(func.params)} -> {len(cand.params)}",
                            problems=f"The parameter list changed ({len(func.params)} -> {len(cand.params)} params). "
                                     f"Keep exactly: ({', '.join(f'{p.type} {p.name}' for p in func.params)}).")

    support = harness.data_support_code(parsed.data_blobs, parsed.raw + "\n" + c_code)
    diff = harness.differential_test(parsed.raw, func.name, c_code, func.name,
                                     func.ret_type, func.param_types, n_tests=n_tests, support_code=support)
    if diff.status == "equivalent":
        return VerifyReport("verified", details=diff.details, tests=diff.tests)
    if diff.status == "mismatch":
        return VerifyReport("mismatch", details=diff.details, tests=diff.tests, mismatches=diff.mismatches,
                            problems="Differential testing against the original pseudocode found different results "
                                     "(args are the function parameters in order; values in hex):\n" + diff.details)
    # skipped / inconclusive: kod kompilyatsiya bo'ldi, lekin solishtirib bo'lmadi
    if diff.status == "inconclusive" and "Yangi kod kompilyatsiya" in diff.details:
        return VerifyReport("compile_error", details=diff.details,
                            problems="The code passes syntax check but fails to compile as an object file:\n"
                                     + diff.details)
    return VerifyReport("compiled", details=diff.details)
