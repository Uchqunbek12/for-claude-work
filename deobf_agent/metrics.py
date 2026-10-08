"""Kod murakkabligi metrikalari — deobfuskatsiya qanchalik foyda berganini o'lchash uchun.

* lines        — bo'sh bo'lmagan, izohsiz va faqat '{' / '}' dan iborat bo'lmagan qatorlar soni
* cyclomatic   — tsiklomatik murakkablik (McCabe): 1 + tarmoqlanishlar soni
                 (if, while, for, case, &&, ||, ?). Qanchalik katta bo'lsa, kodni
                 tushunish va test qilish shunchalik qiyin.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .parser import mask_code


@dataclass
class Metrics:
    lines: int
    cyclomatic: int

    def to_dict(self) -> dict:
        return asdict(self)


def measure(code: str) -> Metrics:
    masked = mask_code(code)
    lines = sum(1 for ln in masked.splitlines() if ln.strip() and ln.strip() not in ("{", "}"))
    branches = len(re.findall(r"\b(?:if|while|for|case)\b", masked))
    branches += masked.count("&&") + masked.count("||") + masked.count("?")
    return Metrics(lines=lines, cyclomatic=1 + branches)
