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
    (?P<num>0[xX][0-9A-Fa-f]+(?:[uUlL]|i64|i32|i16|i8)*|\d+(?:[uUlL]|i64|i32|i16|i8)*)
  | (?P<name>[A-Za-z_]\w*)
  | (?P<op>->|<<=|>>=|<<|>>|<=|>=|==|!=|&&|\|\||[-+*/%&|^~!<>?:()=\[\],.])
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

    def _cast_ahead(self) -> tuple[int, bool]:
        """'(' dan keyin tur nomi va ')' kelsa — bu cast. (uzunlik, ko'rsatkichmi) qaytaradi.

        `(unsigned int)x` — oddiy cast; `(_DWORD *)p` — ko'rsatkich cast (tur nomi noma'lum bo'lsa ham).
        """
        k = 1
        while self.peek(k) is not None and self.peek(k).kind == "name":
            k += 1
        words = [self.toks[self.i + j].text for j in range(1, k)]
        stars = 0
        while self.peek(k) is not None and self.peek(k).text == "*":
            k += 1
            stars += 1
        if not words or self.peek(k) is None or self.peek(k).text != ")":
            return 0, False
        if stars:
            return k, True
        return (k, False) if all(w in _TYPE_WORDS for w in words) else (0, False)

    def _span(self, start: int) -> str:
        """start..joriy token oralig'idagi matn — murakkab ifodani bitta "atom" nomiga aylantirish uchun."""
        out = ""
        for t in self.toks[start:self.i]:
            if out and (out[-1].isalnum() or out[-1] == "_") and (t.text[0].isalnum() or t.text[0] == "_"):
                out += " "
            out += t.text
        return out

    def _balanced(self, open_text: str, close_text: str) -> None:
        depth = 0
        while self.peek() is not None:
            t = self.take()
            if t.text == open_text:
                depth += 1
            elif t.text == close_text:
                depth -= 1
                if depth == 0:
                    return
        raise ExprError(f"yopuvchi '{close_text}' topilmadi")

    def unary(self):
        t = self.peek()
        if t is None:
            raise ExprError("ifoda kutilmaganda tugadi")
        if t.text in ("-", "~", "!", "+"):
            self.take()
            return ("un", t.text, self.unary())
        if t.text in ("*", "&"):
            # *p, &x, *(_DWORD *)(a1 + 8) — xotiraga murojaat. Uning qiymati noma'lum, shuning uchun
            # butun ifodani bitta o'zgaruvchi ("atom") deb olamiz: bir ifoda ichida u bir xil qiymatga ega.
            start = self.i
            self.take()
            self.unary()
            return ("var", self._span(start))
        if t.text == "(":
            k, is_ptr = self._cast_ahead()
            if k and is_ptr:
                start = self.i
                self.i += k + 1
                self.unary()
                return ("var", self._span(start))
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
            start = self.i
            self.take()
            postfix = False
            # a[i], f(x), s.field, p->field — bularning ham qiymati noma'lum: bitta atom
            while self.peek() is not None and self.peek().text in ("(", "[", ".", "->"):
                postfix = True
                op = self.peek().text
                if op == "(":
                    self._balanced("(", ")")
                elif op == "[":
                    self._balanced("[", "]")
                else:
                    self.take()
                    if self.peek() is None or self.peek().kind != "name":
                        raise ExprError("maydon nomi kutilgan edi")
                    self.take()
            return ("var", self._span(start) if postfix else t.text)
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


def type_info(type_text: str) -> tuple[int, bool] | None:
    """C turi matnidan (bitlar, ishorali) ni topadi: 'int' -> (32, True), 'unsigned __int64' -> (64, False).

    Ko'rsatkich — 64 bitli ishorasiz son. Noma'lum tur bo'lsa — None (bunda barcha variantlar sinaladi).
    """
    if "*" in type_text or "[" in type_text:
        return 64, False
    words = type_text.split()
    base = [w for w in words if w not in ("unsigned", "signed", "const", "volatile", "static", "register")]
    if base and all(w in _TYPE_BITS for w in base):
        return _cast_type(words)
    if not base and ("unsigned" in words or "signed" in words):
        return 32, "unsigned" not in words
    return None


def _literal(text: str):
    t = re.sub(r"(?:[uUlL]|i64|i32|i16|i8)+$", "", text)
    suffix = text[len(t):].lower().replace("i64", "ll").replace("i32", "").replace("i16", "").replace("i8", "")
    is_hex = t.lower().startswith("0x")
    value = int(t, 16) if is_hex else int(t)
    unsigned = "u" in suffix
    # C qoidasi: L/LL qo'shimchali son — 64 bit (x86-64 da); int ga sig'magan o'nlik son "long" bo'ladi,
    # o'n oltilik son esa avval "unsigned int" ga sig'ishga harakat qiladi.
    if value > 0xFFFFFFFF or "l" in suffix:
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


DEFAULT_TYPE = (32, False)    # turi noma'lum o'zgaruvchi (evaluate'ga types berilmaganda)
Types = dict[str, tuple[int, bool]]


def evaluate(node, env: dict[str, int], types: Types | None = None) -> tuple[int, int, bool]:
    """Daraxtni hisoblaydi. Natija: (qiymat, bitlar, ishorali).

    types — o'zgaruvchilar turlari {nom: (bitlar, ishorali)}; ko'rsatilmagan nom 32 bitli ishorasiz deb olinadi.
    """
    kind = node[0]
    if kind == "num":
        _, v, bits, signed = node
        return _wrap(v, bits, signed), bits, signed
    if kind == "var":
        if node[1] not in env:
            raise ExprError(f"noma'lum o'zgaruvchi: {node[1]}")
        bits, signed = (types or {}).get(node[1], DEFAULT_TYPE)
        return _wrap(env[node[1]], bits, signed), bits, signed
    if kind == "cast":
        _, bits, signed, a = node
        v, _, _ = evaluate(a, env, types)
        return _wrap(v, bits, signed), bits, signed
    if kind == "cond":
        c, _, _ = evaluate(node[1], env, types)
        return evaluate(node[2] if c else node[3], env, types)
    if kind == "un":
        op = node[1]
        v, bits, signed = evaluate(node[2], env, types)
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
            a, _, _ = evaluate(node[2], env, types)
            return (int(bool(evaluate(node[3], env, types)[0])) if a else 0), 32, True
        if op == "||":
            a, _, _ = evaluate(node[2], env, types)
            return (1 if a else int(bool(evaluate(node[3], env, types)[0]))), 32, True
        a, abits, asigned = evaluate(node[2], env, types)
        b, bbits, bsigned = evaluate(node[3], env, types)
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


def subnodes(node):
    """Daraxtning barcha tugunlari (o'zi bilan birga), yuqoridan pastga tartibda."""
    yield node
    for child in node[1:]:
        if isinstance(child, tuple):
            yield from subnodes(child)


def variables(node) -> list[str]:
    """Ifodadagi o'zgaruvchilar ro'yxati (takrorlanmasdan, uchrash tartibida)."""
    return list(dict.fromkeys(n[1] for n in subnodes(node) if n[0] == "var"))


def constants(node) -> list[int]:
    return list(dict.fromkeys(n[1] for n in subnodes(node) if n[0] == "num"))


def count_ops(node) -> tuple[int, int]:
    """(arifmetik amallar soni, bit amallar soni) — MBA ni tanish uchun."""
    arith = bitw = 0
    for n in subnodes(node):
        if n[0] in ("bin", "un"):
            arith += n[1] in ("+", "-", "*")
            bitw += n[1] in ("&", "|", "^", "~")
    return arith, bitw


def const_value(node) -> int | None:
    """O'zgaruvchisiz ifodaning 32 bitli qiymati; o'zgaruvchi bo'lsa yoki hisoblab bo'lmasa — None."""
    if variables(node):
        return None
    try:
        return evaluate(node, {})[0] & 0xFFFFFFFF
    except ExprError:
        return None


def const_of(text: str) -> int | None:
    """'0x3C1Fu', '0x10 + 3' kabi matnning qiymati (konstanta bo'lmasa — None)."""
    try:
        return const_value(parse(text))
    except ExprError:
        return None


_CAST_NAMES = {8: "char", 16: "short", 32: "int", 64: "long long"}
_NEGATED = {"==": "!=", "!=": "==", "<": ">=", ">=": "<", ">": "<=", "<=": ">"}


def literal_text(value: int, bits: int, signed: bool) -> str:
    """Sonni turi saqlangan holda C literaliga aylantiradi: (5, 32, False) -> '5u', (-5, 64, True) -> '(-5LL)'."""
    value &= (1 << bits) - 1
    suffix = ("" if signed else "u") + ("LL" if bits == 64 else "")
    if signed and value >> (bits - 1):
        return f"(-{(1 << bits) - value}{suffix})"
    return (hex(value) if value > 255 else str(value)) + suffix


def to_c(node, parent_prec: int = 0) -> str:
    """Daraxtdan qayta C matni yasaydi (kerakli joyda qavslar bilan, sonlarning turi saqlanadi)."""
    kind = node[0]
    if kind == "num":
        return literal_text(node[1], node[2], node[3])
    if kind == "var":
        return node[1]
    if kind == "cast":
        return f"({'unsigned ' if not node[2] else ''}{_CAST_NAMES[node[1]]}){to_c(node[3], 11)}"
    if kind == "un":
        return f"{node[1]}{to_c(node[2], 11)}"
    if kind == "cond":
        s = f"{to_c(node[1], 1)} ? {to_c(node[2])} : {to_c(node[3])}"
        return f"({s})" if parent_prec > 0 else s
    p = _BINARY_PREC[node[1]]
    s = f"{to_c(node[2], p)} {node[1]} {to_c(node[3], p + 1)}"
    return f"({s})" if p < parent_prec else s


def negate(node) -> str:
    """Shartning inkorini o'qishga qulay ko'rinishda yozadi: !(a < b) -> a >= b, !(!x) -> x."""
    if node[0] == "un" and node[1] == "!":
        return to_c(node[2])
    if node[0] == "bin" and node[1] in _NEGATED:
        return to_c(("bin", _NEGATED[node[1]], node[2], node[3]))
    return f"!({to_c(node)})"


# ---------------------------------------------------------------- tasodifiy test

_EDGES = [0, 1, 2, 3, 7, 8, 0xFF, 0x100, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, 0xFFFFFFFE]


_INTERPRETATIONS = [(32, False), (32, True), (64, False), (64, True)]


def _interesting(consts: list[int]) -> list[int]:
    """Koddagi konstantalar va ularning "qo'shnilari": x == C kabi shartlarni sinash uchun kerak."""
    out = list(_EDGES)
    for c in consts[:32]:
        out += [c, c + 1, c - 1, -c, ~c]
    return out


def random_inputs(names: list[str], n: int, seed: int = 1, types: Types | None = None,
                  consts: list[int] | None = None):
    """(qiymatlar, turlar) juftliklarini beradi.

    Turi noma'lum o'zgaruvchi har bir sinovda tasodifiy talqin qilinadi (32/64 bit, ishorali/ishorasiz) —
    shunda xulosa (masalan, "shart doim yolg'on") barcha talqinlarda to'g'ri bo'ladi.
    Qiymatlarning bir qismi koddagi konstantalardan olinadi: `v == 0x1337BEEF` kabi shartni
    faqat tasodifiy sonlar bilan sinab bo'lmaydi.
    """
    rng = random.Random(seed)
    special = _interesting(consts or [])
    types = types or {}
    for _ in range(n):
        env, sample_types = {}, {}
        for name in names:
            bits, signed = types.get(name) or rng.choice(_INTERPRETATIONS)
            sample_types[name] = (bits, signed)
            r = rng.random()
            if r < 0.3:
                env[name] = rng.choice(special)
            elif r < 0.5:
                env[name] = rng.randrange(64)
            else:
                env[name] = rng.getrandbits(bits)
        yield env, sample_types


def is_constant(node, n: int = 2000, types: Types | None = None) -> int | None:
    """Ifoda barcha sinovlarda bir xil qiymat bersa — o'sha qiymatni, aks holda None qaytaradi."""
    seen = None
    for env, st in random_inputs(variables(node), n, types=types, consts=constants(node)):
        try:
            v = evaluate(node, env, st)[0]
        except ExprError:
            continue
        if seen is None:
            seen = v
        elif v != seen:
            return None
    return seen


def equivalent(a, b, n: int = 2000, types: Types | None = None) -> bool:
    """Ikki ifoda tasodifiy sinovlarda bir xil natija beradimi?"""
    names = list(dict.fromkeys(variables(a) + variables(b)))
    checked = 0
    for env, st in random_inputs(names, n, seed=7, types=types, consts=constants(a) + constants(b)):
        try:
            va, abits, _ = evaluate(a, env, st)
            vb, bbits, _ = evaluate(b, env, st)
        except ExprError:
            continue
        mask = (1 << max(abits, bbits)) - 1
        checked += 1
        if va & mask != vb & mask:
            return False
    return checked > n // 2
