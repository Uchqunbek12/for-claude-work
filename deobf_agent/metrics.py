"""Kod murakkabligi metrikalari — deobfuskatsiya qanchalik foyda berganini o'lchash uchun.

* lines        — bo'sh bo'lmagan, izohsiz qatorlar soni
* cyclomatic   — tsiklomatik murakkablik (McCabe): 1 + tarmoqlanishlar soni
                 (if, while, for, case, &&, ||, ?). Qanchalik katta bo'lsa, kodni
                 tushunish va test qilish shunchalik qiyin.
* operators    — arifmetik va bit amallari soni
* constants    — "katta" (>255) konstantalar soni (holat raqamlari, kalitlar va h.k.)
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .parser import _mask_comments_and_strings


@dataclass
class Metrics:
    lines: int
    cyclomatic: int
    operators: int
    constants: int

    def to_dict(self) -> dict:
        return asdict(self)


def measure(code: str) -> Metrics:
    masked = _mask_comments_and_strings(code)
    lines = sum(1 for ln in masked.splitlines() if ln.strip() and ln.strip() not in ("{", "}"))
    branches = len(re.findall(r"\b(?:if|while|for|case)\b", masked))
    branches += masked.count("&&") + masked.count("||") + masked.count("?")
    ops = len(re.findall(r"(?<![=!<>&|+\-*/%^])(?:[+\-*/%^~]|&(?!&)|\|(?!\|)|<<|>>)(?![=+\-&|])", masked))
    consts = len([c for c in re.findall(r"\b(0x[0-9A-Fa-f]+|\d+)[uUlL]*\b", masked) if int(c, 0) > 255])
    return Metrics(lines=lines, cyclomatic=1 + branches, operators=ops, constants=consts)
