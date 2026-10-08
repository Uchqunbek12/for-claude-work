"""C tilidagi butun sonli ifodalarni Python ichida hisoblovchi kichik "kalkulyator".

Nima uchun kerak:
  * opaque predicate (soxta shart) ni aniqlash: shartni minglab tasodifiy qiymatlar
    bilan hisoblaymiz; agar natija HAR DOIM bir xil bo'lsa — shart soxta;
  * MBA ifodalarni soddalashtirish: murakkab ifoda va oddiy nomzod (masalan, x + y)
    bir xil qiymat beradimi — tasodifiy sonlar bilan tekshiramiz.

Qanday ishlaydi: matn avval "tokenlar"ga (son, nom, operator) bo'linadi, so'ng
Pratt parser yordamida daraxtga (AST) aylantiriladi. Hisoblashda C qoidalari
taqlid qilinadi: 32/64 bitli "aylanib ketish", ishorali/ishorasiz taqqoslash va h.k.
Bu to'liq C emas — faqat obfuskatsiyada uchraydigan butun sonli ifodalar uchun.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

# ---------------------------------------------------------------- tokenlar

_TOKEN_RE = re.compile(r"""
    (?P<num>0[xX][0-9A-Fa-f]+[uUlL]*|\d+[uUlL]*)
  | (?P<name>[A-Za-z_]\w*)
  | (?P<op><<=|>>=|<<|>>|<=|>=|==|!=|&&|\|\||[-+*/%&|^~!<>?:()=])
  | (?P<ws>\s+)
""", re.VERBOSE)

# Tur nomlari: "(unsigned int)x" kabi tur o'zgartirishni (cast) tanish uchun.
_TYPE_BITS = {
    "char": (8, True), "short": (16, True), "int": (32, True), "long": (64, True),
    "__int8": (8, True), "__int16": (16, True), "__int32": (32, True), "__int64": (64, True),
    "_BYTE": (8, False), "_WORD": (16, False), "_DWORD": (32, False), "_QWORD": (64, False),
    "int8_t": (8, True), "int16_t": (16, True), "int32_t": (32, True), "int64_t": (64, True),
    "uint8_t": (8, False), "uint16_t": (16, False), "uint32_t": (32, False), "uint64_t": (64, False),
    "byte": (8, False), "uchar": (8, False), "ushort": (16, False), "uint": (32, False),
    "ulong": (64, False), "undefined1": (8, False), "undefined2": (16, False),
    "undefined4": (32, False), "undefined8": (64, False), "longlong": (64, True), "ulonglong": (64, False),
    "bool": (8, False), "_Bool": (8, False), "BYTE": (8, False), "WORD": (16, False), "DWORD": (32, False),
}
_TYPE_WORDS = set(_TYPE_BITS) | {"unsigned", "signed", "const", "volatile"}


class ExprError(Exception):
    """Ifodani tahlil qilib yoki hisoblab bo'lmadi."""


@dataclass
class Tok:
    kind: str
    text: str


def tokenize(src: str) -> list[Tok]:
    pos, out = 0, []
    while pos < len(src):
        m = _TOKEN_RE.match(src, pos)
        if not m:
            raise ExprError(f"tanilmagan belgi: {src[pos:pos + 10]!r}")
        pos = m.end()
        kind = m.lastgroup
        if kind != "ws":
            out.append(Tok(kind, m.group()))
    return out


# ---------------------------------------------------------------- AST tugunlari
# Daraxt oddiy kortejlar (tuple) ko'rinishida saqlanadi:
#   ("num", qiymat, bitlar, ishorali)   ("var", nom)
#   ("un", op, a)   ("bin", op, a, b)   ("cast", bitlar, ishorali, a)   ("cond", c, a, b)

_BINARY_PREC = {
    "||": 1, "&&": 2, "|": 3, "^": 4, "&": 5, "==": 6, "!=": 6,
    "<": 7, ">": 7, "<=": 7, ">=": 7, "<<": 8, ">>": 8, "+": 9, "-": 9, "*": 10, "/": 10, "%": 10,
}


class _Parser:
    def __init__(self, toks: list[Tok]):
        self.toks, self.i = toks, 0

    def peek(self, k: int = 0) -> Tok | None:
        j = self.i + k
        return self.toks[j] if j < len(self.toks) else None

    def take(self, text: str | None = None) -> Tok:
        t = self.peek()
        if t is None or (text is not None and t.text != text):
            raise ExprError(f"kutilgan: {text!r}, topildi: {t.text if t else 'oxiri'!r}")
        self.i += 1
        return t

    def parse(self):
        node = self.expr(0)
        if self.peek() is not None:
            raise ExprError(f"ortiqcha token: {self.peek().text!r}")
        return node

    def expr(self, min_prec: int):
        left = self.unary()
        while True:
            t = self.peek()
            if t is None:
                return left
            if t.text == "?" and min_prec <= 0:
                self.take("?")
                a = self.expr(0)
                self.take(":")
                b = self.expr(0)
                left = ("cond", left, a, b)
                continue
            prec = _BINARY_PREC.get(t.text)
            if prec is None or prec < min_prec or t.kind != "op":
                return left
            self.take()
            right = self.expr(prec + 1)
            left = ("bin", t.text, left, right)

    def _cast_ahead(self) -> int:
        """'(' dan keyin tur nomlari va ')' kelsa — bu cast. Uzunligini qaytaradi."""
        k = 1
        while self.peek(k) is not None and self.peek(k).text in _TYPE_WORDS:
            k += 1
        if k > 1 and self.peek(k) is not None and self.peek(k).text == ")":
            return k
        return 0

    def unary(self):
        t = self.peek()
        if t is None:
            raise ExprError("ifoda kutilmaganda tugadi")
        if t.text in ("-", "~", "!", "+"):
            self.take()
            return ("un", t.text, self.unary())
        if t.text == "(":
            k = self._cast_ahead()
            if k:
                words = [self.toks[self.i + j].text for j in range(1, k)]
                self.i += k + 1
                bits, signed = _cast_type(words)
                return ("cast", bits, signed, self.unary())
            self.take("(")
            node = self.expr(0)
            self.take(")")
            return node
        if t.kind == "num":
            self.take()
            return _literal(t.text)
        if t.kind == "name":
            self.take()
            if self.peek() is not None and self.peek().text == "(":
                raise ExprError(f"funksiya chaqiruvi qo'llab-quvvatlanmaydi: {t.text}")
            return ("var", t.text)
        raise ExprError(f"kutilmagan token: {t.text!r}")


def _cast_type(words: list[str]) -> tuple[int, bool]:
    signed = "unsigned" not in words
    bits = 32
    base = [w for w in words if w not in ("unsigned", "signed", "const", "volatile")]
    if base:
        bits, s = _TYPE_BITS.get(base[-1], (32, True))
        if base.count("long") >= 2:
            bits = 64
        if "unsigned" not in words and "signed" not in words:
            signed = s
    return bits, signed


def _literal(text: str):
    t = text.rstrip("uUlL")
    suffix = text[len(t):].lower()
    is_hex = t.lower().startswith("0x")
    value = int(t, 16) if is_hex else int(t)
    unsigned = "u" in suffix
    # C qoidasi: int ga sig'magan o'nlik son "long" bo'ladi, o'n oltilik son esa
    # avval "unsigned int" ga sig'ishga harakat qiladi.
    if value > 0xFFFFFFFF or suffix.count("l") >= 1 and value > 0x7FFFFFFF:
        bits = 64
    elif value > 0x7FFFFFFF and not (is_hex or unsigned):
        bits = 64
    else:
        bits = 32
    signed = not unsigned and not (is_hex and bits == 32 and value > 0x7FFFFFFF)
    return ("num", value, bits, signed)


def parse(src: str):
    """C ifoda matnini AST daraxtiga aylantiradi."""
    return _Parser(tokenize(src)).parse()


# ---------------------------------------------------------------- hisoblash

def _wrap(value: int, bits: int, signed: bool) -> int:
    value &= (1 << bits) - 1
    if signed and value >> (bits - 1):
        value -= 1 << bits
    return value


def evaluate(node, env: dict[str, int], var_bits: int = 32, var_signed: bool = False) -> tuple[int, int, bool]:
    """Daraxtni hisoblaydi. Natija: (qiymat, bitlar, ishorali)."""
    kind = node[0]
    if kind == "num":
        _, v, bits, signed = node
        return _wrap(v, bits, signed), bits, signed
    if kind == "var":
        if node[1] not in env:
            raise ExprError(f"noma'lum o'zgaruvchi: {node[1]}")
        return _wrap(env[node[1]], var_bits, var_signed), var_bits, var_signed
    if kind == "cast":
        _, bits, signed, a = node
        v, _, _ = evaluate(a, env, var_bits, var_signed)
        return _wrap(v, bits, signed), bits, signed
    if kind == "cond":
        c, _, _ = evaluate(node[1], env, var_bits, var_signed)
        return evaluate(node[2] if c else node[3], env, var_bits, var_signed)
    if kind == "un":
        op = node[1]
        v, bits, signed = evaluate(node[2], env, var_bits, var_signed)
        bits, signed = max(bits, 32), signed if bits >= 32 else True   # butun songa ko'tarish
        if op == "-":
            return _wrap(-v, bits, signed), bits, signed
        if op == "~":
            return _wrap(~v, bits, signed), bits, signed
        if op == "!":
            return int(v == 0), 32, True
        return _wrap(v, bits, signed), bits, signed
    if kind == "bin":
        op = node[1]
        if op == "&&":
            a, _, _ = evaluate(node[2], env, var_bits, var_signed)
            return (int(bool(evaluate(node[3], env, var_bits, var_signed)[0])) if a else 0), 32, True
        if op == "||":
            a, _, _ = evaluate(node[2], env, var_bits, var_signed)
            return (1 if a else int(bool(evaluate(node[3], env, var_bits, var_signed)[0]))), 32, True
        a, abits, asigned = evaluate(node[2], env, var_bits, var_signed)
        b, bbits, bsigned = evaluate(node[3], env, var_bits, var_signed)
        if op in ("<<", ">>"):
            bits, signed = max(abits, 32), asigned if abits >= 32 else True
            sh = b & (bits - 1)
            ua = _wrap(a, bits, signed)
            return _wrap(ua << sh if op == "<<" else ua >> sh, bits, signed), bits, signed
        # "odatiy arifmetik o'zgartirishlar" (C qoidasining soddalashtirilgan ko'rinishi)
        bits = max(abits, bbits, 32)
        a_s = asigned or abits < 32
        b_s = bsigned or bbits < 32
        if abits == bbits:
            signed = a_s and b_s
        else:
            signed = a_s if abits > bbits else b_s
        a, b = _wrap(a, bits, signed), _wrap(b, bits, signed)
        if op == "+":
            r = a + b
        elif op == "-":
            r = a - b
        elif op == "*":
            r = a * b
        elif op in ("/", "%"):
            if b == 0:
                raise ExprError("nolga bo'lish")
            q = abs(a) // abs(b) * (1 if (a >= 0) == (b >= 0) else -1)   # C da 0 tomonga yaxlitlanadi
            r = q if op == "/" else a - q * b
        elif op == "&":
            r = a & b
        elif op == "|":
            r = a | b
        elif op == "^":
            r = a ^ b
        elif op in ("==", "!=", "<", ">", "<=", ">="):
            res = {"==": a == b, "!=": a != b, "<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b}[op]
            return int(res), 32, True
        else:
            raise ExprError(f"noma'lum operator {op}")
        return _wrap(r, bits, signed), bits, signed
    raise ExprError(f"noma'lum tugun {kind}")


def variables(node) -> list[str]:
    """Ifodadagi o'zgaruvchilar ro'yxati (takrorlanmasdan, tartib bilan)."""
    out: list[str] = []

    def walk(n):
        if n[0] == "var":
            if n[1] not in out:
                out.append(n[1])
        elif n[0] in ("un",):
            walk(n[2])
        elif n[0] == "bin":
            walk(n[2])
            walk(n[3])
        elif n[0] == "cast":
            walk(n[3])
        elif n[0] == "cond":
            walk(n[1])
            walk(n[2])
            walk(n[3])

    walk(node)
    return out


def constants(node) -> list[int]:
    out: list[int] = []

    def walk(n):
        if n[0] == "num":
            if n[1] not in out:
                out.append(n[1])
        for child in n[1:]:
            if isinstance(child, tuple):
                walk(child)

    walk(node)
    return out


def count_ops(node) -> tuple[int, int]:
    """(arifmetik amallar soni, bit amallar soni) — MBA ni tanish uchun."""
    arith = bitw = 0

    def walk(n):
        nonlocal arith, bitw
        if n[0] == "bin":
            if n[1] in ("+", "-", "*"):
                arith += 1
            elif n[1] in ("&", "|", "^"):
                bitw += 1
        elif n[0] == "un":
            if n[1] == "~":
                bitw += 1
            elif n[1] == "-":
                arith += 1
        for child in n[1:]:
            if isinstance(child, tuple):
                walk(child)

    walk(node)
    return arith, bitw


# ---------------------------------------------------------------- tasodifiy test

_EDGES = [0, 1, 2, 3, 7, 8, 0xFF, 0x100, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, 0xFFFFFFFE]


def random_inputs(names: list[str], n: int, seed: int = 1, bits: int = 32):
    rng = random.Random(seed)
    for i in range(n):
        env = {}
        for name in names:
            r = rng.random()
            if r < 0.25:
                env[name] = rng.choice(_EDGES)
            elif r < 0.5:
                env[name] = rng.randrange(64)
            else:
                env[name] = rng.getrandbits(bits)
        yield env


def is_constant(node, n: int = 2000, var_bits: int = 32, var_signed: bool = False) -> int | None:
    """Ifoda barcha sinovlarda bir xil qiymat bersa — o'sha qiymatni, aks holda None qaytaradi."""
    names = variables(node)
    seen = None
    for env in random_inputs(names, n):
        try:
            v = evaluate(node, env, var_bits, var_signed)[0]
        except ExprError:
            continue
        if seen is None:
            seen = v
        elif v != seen:
            return None
    return seen


def equivalent(a, b, n: int = 2000, var_bits: int = 32, var_signed: bool = False) -> bool:
    """Ikki ifoda tasodifiy sinovlarda bir xil natija beradimi? (32 bit chegarasida)"""
    names = variables(a)
    for extra in variables(b):
        if extra not in names:
            names.append(extra)
    mask = (1 << var_bits) - 1
    checked = 0
    for env in random_inputs(names, n, seed=7):
        try:
            va = evaluate(a, env, var_bits, var_signed)[0] & mask
            vb = evaluate(b, env, var_bits, var_signed)[0] & mask
        except ExprError:
            continue
        checked += 1
        if va != vb:
            return False
    return checked > n // 2
