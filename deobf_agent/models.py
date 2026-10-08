"""Loyihaning barcha modullari ishlatadigan ma'lumot tuzilmalari.

dataclass — Python'da "ma'lumot qutisi" yaratishning qulay usuli: maydonlar
ro'yxatini yozasiz, Python esa konstruktor va chiroyli chop etishni o'zi yaratadi.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Param:
    type: str
    name: str


@dataclass
class FunctionInfo:
    """Psevdokoddan ajratib olingan bitta funksiya."""

    name: str
    ret_type: str
    params: list[Param]
    signature: str          # "unsigned int __fastcall mix(unsigned int a1, unsigned int a2)"
    body: str               # { ... } ichidagi qism, qavslar bilan
    text: str               # funksiyaning to'liq matni (signatura + tana)
    start_line: int         # kirish matnidagi boshlang'ich qator raqami (1 dan)
    end_line: int
    calls: list[str] = field(default_factory=list)   # chaqirilgan boshqa funksiyalar

    @property
    def param_types(self) -> list[str]:
        return [p.type for p in self.params]

    @property
    def line_count(self) -> int:
        return self.text.count("\n") + 1


@dataclass
class ParsedInput:
    """Parser natijasi: uslub, funksiyalar va global ma'lumotlar."""

    style: str                                  # "ida" | "ghidra" | "angr" | "c"
    functions: list[FunctionInfo]
    data_blobs: dict[str, bytes] = field(default_factory=dict)
    raw: str = ""
    preamble: str = ""      # funksiyalardan tashqaridagi matn (e'lonlar, global o'zgaruvchilar)

    def get(self, name: str) -> FunctionInfo | None:
        return next((f for f in self.functions if f.name == name), None)


@dataclass
class Finding:
    """Statik tahlil topgan bitta obfuskatsiya belgisi."""

    technique: str          # "mba", "opaque_predicate", "control_flow_flattening", ...
    line: int               # funksiya ichidagi qator raqami (1 dan)
    snippet: str            # topilgan kod parchasi
    message: str            # o'zbekcha izoh
    suggestion: str = ""    # soddalashtirilgan variant (agar bo'lsa)
    confidence: float = 0.5 # 0..1 — ishonch darajasi
    verified: bool = False  # tasodifiy test bilan tasdiqlanganmi

    def to_dict(self) -> dict:
        return asdict(self)
