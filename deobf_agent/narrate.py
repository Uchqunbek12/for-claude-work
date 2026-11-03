"""Soddalashtirilgan C koddan odam tushunadigan o'zbekcha izoh yasash (LLM'siz, qoidalar asosida).

Nima uchun kerak: offline rejimda vosita faqat "MBA ifoda topildi" kabi usul nomlarini aytar edi, kod
*aslida nima qilishini* esa aytmas edi. Bu modul tozalangan funksiyani gaplarga ajratib, har bir qadamni
konkret jumla bilan tushuntiradi ("v2 ga v1 % v0 ni yozadi"), funksiya nima hisoblashini (EKUB, FNV xesh,
saralash, XOR shifrlash ...) taniydigan oddiy qoidalar bilan aytadi. Har bir matn ikki xil beriladi:

  * mutaxassis uchun — o'zgaruvchi va amallar nomi bilan (`v1 % v0`);
  * oddiy tilda      — «quti», «son» kabi hayotiy so'zlar bilan, kod belgilarisiz.

Hammasi deterministik: bir xil kod uchun har safar bir xil matn chiqadi (LLM yo'q, narx yo'q).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import expr as E
from .detectors import KNOWN_CONSTANTS, _split_stmt, is_declaration
from .parser import find_close, mask_code, split_top_level

# ---------------------------------------------------------------- gaplar daraxti


@dataclass
class Node:
    kind: str                       # simple | return | if | while | for | do | switch
    text: str                       # simple/return: gap matni (';'siz); boshqalar: shart
    line: int                       # funksiya matni ichida 1-dan boshlanadigan qator
    end: int
    src: str                        # shu gapning asl matni
    body: list["Node"] = field(default_factory=list)
    other: list["Node"] = field(default_factory=list)      # else tarmog'i
    extra: tuple[str, str] = ("", "")                      # for: (boshlanish, o'zgarish)


_KEYWORD_RE = re.compile(r"(if|while|for|switch|do|return|else)\b")
_LABEL_RE = re.compile(r"(?:case\b[^:;{}]*|default\s*):")


def _stmt_end(m: str, i: int, end: int) -> int:
    """i dan boshlangan oddiy gapning ';' belgisigacha indeksi (qavslar ichidagi ';' hisobga olinmaydi)."""
    depth = 0
    while i < end:
        ch = m[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == ";" and depth <= 0:
            return i
        i += 1
    return end


def _skip_ws(m: str, i: int, end: int) -> int:
    while i < end and m[i].isspace():
        i += 1
    return i


def _parse_body(text: str, m: str, i: int, end: int) -> tuple[list[Node], int]:
    """'{ ... }' bloki yoki bitta gap. (tugunlar, keyingi indeks)."""
    i = _skip_ws(m, i, end)
    if i < end and m[i] == "{":
        close = find_close(m, i, "{}")
        close = end if close < 0 else close
        return _parse_range(text, m, i + 1, close), close + 1
    nodes, nxt = _parse_stmt(text, m, i, end)
    return nodes, nxt


def _parse_range(text: str, m: str, start: int, end: int) -> list[Node]:
    out: list[Node] = []
    i = start
    while True:
        i = _skip_ws(m, i, end)
        if i >= end:
            return out
        nodes, i = _parse_stmt(text, m, i, end)
        out += nodes


def _node(text: str, m: str, kind: str, cond: str, a: int, b: int, **kw) -> Node:
    return Node(kind, cond, m.count("\n", 0, a) + 1, m.count("\n", 0, max(a, b - 1)) + 1, text[a:b].strip(), **kw)


def _parse_stmt(text: str, m: str, i: int, end: int) -> tuple[list[Node], int]:
    lab = _LABEL_RE.match(m, i)
    if lab:                                           # case X: / default: — belgi, o'zi gap emas
        return [], lab.end()
    if m[i] == ";":
        return [], i + 1
    if m[i] == "{":
        close = find_close(m, i, "{}")
        close = end if close < 0 else close
        return _parse_range(text, m, i + 1, close), close + 1
    kw = _KEYWORD_RE.match(m, i)
    word = kw.group(1) if kw else ""
    if word in ("if", "while", "for", "switch"):
        open_ = _skip_ws(m, kw.end(), end)
        if open_ < end and m[open_] == "(":
            close = find_close(m, open_, "()")
            if close > 0:
                head = text[open_ + 1:close].strip()
                body, j = _parse_body(text, m, close + 1, end)
                other: list[Node] = []
                if word == "if":
                    k = _skip_ws(m, j, end)
                    el = re.match(r"else\b", m[k:end])
                    if el:
                        other, j = _parse_body(text, m, k + el.end(), end)
                extra = ("", "")
                if word == "for":
                    parts = split_top_level(head, ";")
                    if len(parts) == 3:
                        head, extra = parts[1].strip(), (parts[0].strip(), parts[2].strip())
                return [_node(text, m, word, head, i, j, body=body, other=other, extra=extra)], j
    if word == "do":
        body, j = _parse_body(text, m, kw.end(), end)
        k = _skip_ws(m, j, end)
        wm = re.match(r"while\s*\(", m[k:end])
        if wm:
            open_ = k + wm.end() - 1
            close = find_close(m, open_, "()")
            if close > 0:
                j2 = _stmt_end(m, close + 1, end) + 1
                return [_node(text, m, "do", text[open_ + 1:close].strip(), i, j2, body=body)], j2
    j = _stmt_end(m, i, end)
    stmt = text[i:j].strip()
    nxt = j + 1
    if word == "return":
        return [_node(text, m, "return", stmt[6:].strip(), i, nxt)], nxt
    if not stmt or re.match(r"(break|continue|goto)\b", stmt):
        return [], nxt
    if is_declaration(stmt):                          # 'int a = 1, b;' -> faqat boshlang'ich qiymatli qismlar
        parts = [(n, r) for n, _, r in _split_stmt(stmt) if r is not None]
        return [_node(text, m, "simple", f"{n} = {r}", i, nxt) for n, r in parts], nxt
    return [_node(text, m, "simple", stmt, i, nxt)], nxt


def parse_function(func_text: str) -> list[Node]:
    """Funksiya tanasining gaplar daraxti (e'lonlar tashlab ketiladi)."""
    m = mask_code(func_text)
    open_ = m.find("{")
    if open_ < 0:
        return []
    close = find_close(m, open_, "{}")
    return _parse_range(func_text, m, open_ + 1, len(m) if close < 0 else close)


# ---------------------------------------------------------------- ifodalarni gapga aylantirish

_ARR_RE = re.compile(r"^(\w+)\[(.+)\]$")
_CALL_RE = re.compile(r"^(\w+)\((.*)\)$", re.S)
_ASSIGN_OPS = ("<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "=")


def _name(s: str, simple: bool) -> str:
    return f"«{s}»" if simple else f"`{s}`"


def _is_atom(n) -> bool:
    return n[0] in ("num", "var") or (n[0] == "cast" and _is_atom(n[3]))


def _value(n, simple: bool) -> str:
    """Ifodaning bosh kelishikdagi ko'rinishi: `x`, 5, `a0[v1]` (sharti/solishtirishlar uchun)."""
    if n[0] == "num":
        return str(n[1])
    if n[0] == "cast" and n[1] != 8:
        return _value(n[3], simple)
    text = E.to_c(n)
    if simple:                                                    # oddiy tilda kod bo'laklari (formula, xotira manzili, 0x...) ko'rsatilmaydi
        if text.startswith(("*", "&")) or "->" in text:
            return "«xotiradagi qiymat»"
        if (len(text) > 14 or "0x" in text) and not _ARR_RE.match(text):
            return "«hisob natijasi»"
    return _name(text, simple)


def _rotate(n):
    """(x << k) | (x >> (32 - k)) kabi aylantirishni taniydi: (x, k) yoki None."""
    if n[0] == "bin" and n[1] == "|" and n[2][0] == "bin" and n[3][0] == "bin" and n[2][1] == "<<" and n[3][1] == ">>" \
            and n[2][2] == n[3][2]:
        return n[2][2], n[2][3]
    return None


def phrase(n, simple: bool = False) -> str:
    """Ifodaning tushum kelishigidagi ta'rifi: «A va B yig'indisini»."""
    k = n[0]
    if k == "num":
        return f"{n[1]} sonini"
    if k == "var":
        am = _ARR_RE.match(n[1])
        if am:
            return (f"{_name(am.group(1), True)} ro'yxatining {_name(am.group(2), True)}-elementini" if simple
                    else f"{_name(n[1], False)} elementini")
        cm = _CALL_RE.match(n[1])
        if cm:
            fn, args = cm.groups()
            return (f"{_name(fn, True)} yordamchi funksiyasi ({_name(args, True)} bo'yicha) topgan sonni" if simple
                    else f"{_name(fn, False)} funksiyasini ({_name(args, False)}) bilan chaqirib olingan qiymatni")
        return f"{_value(n, True)} dagi qiymatni" if simple else f"{_name(n[1], False)} qiymatini"
    if k == "cast":
        if n[1] == 8:
            return (f"{_value(n[3], True)} ning oxirgi baytini (0 dan 255 gacha son)" if simple
                    else f"{_value(n[3], False)} ning pastki baytini")
        return phrase(n[3], simple)
    if k == "un":
        a = _value(n[2], simple)
        return {"-": f"{a} ning qarama-qarshi ishorali qiymatini", "~": f"{a} ning har bir biti teskarisini",
                "!": f"{a} nolga tengligini (1 yoki 0)"}.get(n[1], f"{_name(E.to_c(n), simple)} ifodani")
    if k == "cond":
        return f"{cond_text(n[1], simple)} bo'lsa {_value(n[2], simple)}, aks holda {_value(n[3], simple)} ni"
    op, a, b = n[1], n[2], n[3]
    rot = _rotate(n)
    if rot:
        x, c = rot
        return (f"{_value(x, True)} ning bitlarini aylana bo'ylab {_value(c, True)} qadam surib chiqqan sonni" if simple
                else f"{_value(x, False)} ni {_value(c, False)} bit chapga aylantirilgan (rotate-left) qiymatini")
    A, B = _value(a, simple), _value(b, simple)
    if op == "&" and b[0] == "num":
        mask = b[1]
        if mask == 0xFF:
            return (f"{A} ning oxirgi baytini (0 dan 255 gacha son)" if simple else f"{A} ning pastki baytini")
        if mask > 0 and mask & (mask + 1) == 0:
            return (f"{A} ning faqat kichik qismini (0 dan {mask} gacha son)" if simple
                    else f"{A} ning pastki {mask.bit_length()} bitini (0..{mask} oraliqdagi son)")
    if simple:
        table = {
            "+": f"{A} bilan {B} ni qo'shganda chiqqan sonni", "-": f"{A} dan {B} ni ayirganda chiqqan sonni",
            "*": f"{A} ni {B} ga ko'paytirganda chiqqan sonni", "/": f"{A} ni {B} ga bo'lganda chiqqan butun sonni",
            "%": f"{A} ni {B} ga bo'lganda qoladigan qoldiqni",
            "&": f"{A} va {B} ning ikkalasida ham 1 bo'lgan bitlaridan tuzilgan sonni",
            "|": f"{A} va {B} ning kamida birida 1 bo'lgan bitlaridan tuzilgan sonni",
            "^": f"{A} va {B} ning faqat bittasida 1 bo'lgan bitlaridan tuzilgan sonni",
            "<<": f"{A} ning bitlarini {B} qadam chapga surib chiqqan sonni",
            ">>": f"{A} ning bitlarini {B} qadam o'ngga surib chiqqan sonni",
        }
    else:
        table = {
            "+": f"{A} va {B} yig'indisini", "-": f"{A} dan {B} ni ayirganda chiqadigan sonni",
            "*": f"{A} ning {B} ga ko'paytmasini", "/": f"{A} ni {B} ga bo'lgandagi bo'linmani",
            "%": f"{A} ni {B} ga bo'lgandagi qoldiqni", "&": f"{A} va {B} ning bitli VA natijasini",
            "|": f"{A} va {B} ning bitli YOKI natijasini", "^": f"{A} va {B} ning XOR natijasini",
            "<<": f"{A} ni {B} bit chapga siljitilgan qiymatini", ">>": f"{A} ni {B} bit o'ngga siljitilgan qiymatini",
        }
    if op in table:
        return table[op]
    return f"{cond_text(n, simple)} shartining natijasini (1 yoki 0)"


_CMP = {"<": "dan kichik", ">": "dan katta", "<=": "dan katta emas", ">=": "dan kichik emas",
        "==": "ga teng", "!=": "ga teng emas"}


def cond_text(n, simple: bool = False) -> str:
    """Shartning gap ko'rinishi: «`v0` `a1` dan kichik»."""
    if n[0] == "bin":
        op, a, b = n[1], n[2], n[3]
        if op in _CMP:
            if b[0] == "num" and b[1] == 0 and op in ("==", "!="):
                return f"{_value(a, simple)} nolga {'teng' if op == '==' else 'teng emas'}"
            return f"{_value(a, simple)} {_value(b, simple)} {_CMP[op]}"
        if op == "&&":
            return f"{cond_text(a, simple)} va {cond_text(b, simple)}"
        if op == "||":
            return f"{cond_text(a, simple)} yoki {cond_text(b, simple)}"
    if n[0] == "un" and n[1] == "!":
        return f"{_value(n[2], simple)} nolga teng"
    return f"{_value(n, simple)} noldan farqli"


def _parse(s: str):
    try:
        return E.parse(s)
    except E.ExprError:
        return None


def _cond(s: str, simple: bool) -> str:
    n = _parse(s)
    return cond_text(n, simple) if n is not None else _name(s, simple)


def _split_assign(text: str):
    """'a[i] ^= k' -> ('a[i]', '^', 'k'); '=' uchun op ''. Topilmasa None."""
    found = _split_stmt(text)
    if len(found) != 1:
        return None
    lhs, op, rhs = found[0]
    if rhs is None:
        return None
    return lhs, op[:-1] if op != "=" else "", rhs


def _verb(op: str, lhs: str, rhs, simple: bool) -> str:
    L = _name(lhs, simple)
    if simple:
        verbs = {"+": f"{L} dagi songa {_value(rhs, True)} ni qo'shadi", "-": f"{L} dagi sondan {_value(rhs, True)} ni ayiradi",
                 "*": f"{L} dagi sonni {_value(rhs, True)} ga ko'paytiradi",
                 "/": f"{L} dagi sonni {_value(rhs, True)} ga bo'ladi", "%": f"{L} dagi sondan {_value(rhs, True)} ga bo'lgandagi qoldiqni qoldiradi",
                 "^": f"{L} dagi son bilan {_value(rhs, True)} ni bit darajasida «aralashtiradi» (XOR)",
                 "&": f"{L} dagi sonning faqat {_value(rhs, True)} ko'rsatgan bitlarini qoldiradi",
                 "|": f"{L} dagi songa {_value(rhs, True)} ning bitlarini qo'shib qo'yadi",
                 "<<": f"{L} dagi son bitlarini {_value(rhs, True)} qadam chapga suradi",
                 ">>": f"{L} dagi son bitlarini {_value(rhs, True)} qadam o'ngga suradi"}
    else:
        verbs = {"+": f"{L} ga {_value(rhs, False)} ni qo'shadi", "-": f"{L} dan {_value(rhs, False)} ni ayiradi",
                 "*": f"{L} ni {_value(rhs, False)} ga ko'paytiradi", "/": f"{L} ni {_value(rhs, False)} ga bo'ladi",
                 "%": f"{L} ni {_value(rhs, False)} ga bo'lgandagi qoldiq bilan almashtiradi",
                 "^": f"{L} ni {_value(rhs, False)} bilan XOR qiladi",
                 "&": f"{L} ni {_value(rhs, False)} bilan bitli VA qiladi",
                 "|": f"{L} ni {_value(rhs, False)} bilan bitli YOKI qiladi",
                 "<<": f"{L} ni {_value(rhs, False)} bit chapga siljitadi", ">>": f"{L} ni {_value(rhs, False)} bit o'ngga siljitadi"}
    return verbs.get(op, f"{L} ni o'zgartiradi")


def known_notes(text: str) -> list[str]:
    """Matndagi mashhur algoritm konstantalari uchun qisqa izohlar (mutaxassis uchun)."""
    notes: list[str] = []
    for m in E.C_INT_RE.finditer(mask_code(text)):
        raw = E.c_int(m.group(1))
        v = (raw or 0) & 0xFFFFFFFF
        if raw is not None and v in KNOWN_CONSTANTS and raw > 255:
            note = f"{m.group(1)} — {KNOWN_CONSTANTS[v]}"
            if note not in notes:
                notes.append(note)
    return notes


def describe_simple_stmt(text: str, simple: bool = False) -> str:
    """Bitta oddiy gapni jumlaga aylantiradi (oxirida nuqta bilan)."""
    parts = _split_assign(text)
    if parts is None:
        call = _CALL_RE.match(text.strip())
        if call:
            fn, args = call.groups()
            return (f"{_name(fn, True)} yordamchi funksiyasini ishga tushiradi." if simple
                    else f"{_name(fn, False)} funksiyasini ({_name(args, False)}) bilan chaqiradi.")
        return f"{_name(text.strip(), simple)} amalini bajaradi."
    lhs, op, rhs_s = parts
    rhs = _parse(rhs_s)
    if rhs is None:
        return f"{_name(lhs, simple)} ga {_name(rhs_s, simple)} natijasini yozadi."
    am = _ARR_RE.match(lhs.replace(" ", ""))
    L = _name(lhs, simple)
    if op:                                                    # x op= E
        return _verb(op, lhs, rhs, simple) + "."
    if rhs[0] == "bin" and rhs[2] == ("var", lhs.replace(" ", "")) and rhs[1] in "+-*^|&" and len(rhs[1]) == 1:
        if am and rhs[1] == "^":                              # a[i] = a[i] ^ k
            return (f"Ro'yxatdagi {_name(am.group(2), True)}-belgini {_value(rhs[3], True)} bilan «aralashtirib» (XOR), "
                    "o'z joyiga qaytarib qo'yadi." if simple else
                    f"{L} ni {_value(rhs[3], False)} bilan XOR qilib, shu joyga qaytarib yozadi.")
        if rhs[1] in "+-" and rhs[3][0] == "num":
            if simple:
                return f"{L} dagi sonni {rhs[3][1]} taga {'oshiradi' if rhs[1] == '+' else 'kamaytiradi'}."
            return f"{L} ni {rhs[3][1]} ga {'oshiradi' if rhs[1] == '+' else 'kamaytiradi'}."
        return _verb(rhs[1], lhs, rhs[3], simple) + "."
    if am:
        where = (f"{_name(am.group(1), True)} ro'yxatining {_name(am.group(2), True)}-joyiga" if simple
                 else f"{L} elementiga")
        return (f"{phrase(rhs, True)[0].upper()}{phrase(rhs, True)[1:]} hisoblab, {where} qo'yadi." if simple
                else f"{where} {phrase(rhs, False)} yozadi.")
    if rhs[0] == "num":
        return (f"{L} qutisiga {rhs[1]} sonini soladi." if simple else f"{L} ga {rhs[1]} sonini yozadi.")
    if rhs[0] == "var" and not _ARR_RE.match(rhs[1]) and not _CALL_RE.match(rhs[1]):
        return (f"{_name(rhs[1], True)} dagi sonning nusxasini {L} qutisiga soladi." if simple
                else f"{L} ga {_name(rhs[1], False)} qiymatini ko'chiradi.")
    if simple:
        p = phrase(rhs, True)
        return f"{p[0].upper()}{p[1:]} hisoblab, {L} qutisiga soladi."
    return f"{L} ga {phrase(rhs, False)} yozadi."


# ---------------------------------------------------------------- qadamlar

@dataclass
class Step:
    line: int
    end: int
    code: str
    title: str
    text: str            # mutaxassis uchun
    simple: str          # oddiy tilda


def _swap(nodes: list[Node], i: int):
    """t = A; A = B; B = t — o'rin almashtirish. (A, B, t) yoki None."""
    if i + 2 >= len(nodes) or any(n.kind != "simple" for n in nodes[i:i + 3]):
        return None
    p = [_split_assign(n.text) for n in nodes[i:i + 3]]
    if any(x is None or x[1] for x in p):
        return None
    (t, _, a), (a2, _, b), (b2, _, t2) = p
    norm = lambda s: s.replace(" ", "")  # noqa: E731
    if norm(a2) == norm(a) and norm(t2) == norm(t) and norm(b2) == norm(b) and norm(a) != norm(b):
        return a.strip(), b.strip(), t
    return None


def _loop_counter(n: Node) -> str:
    """Tsikl sharti ichidagi o'zgaruvchi tanada 1 ga oshsa — uning nomi."""
    cond_vars = set(re.findall(r"[A-Za-z_]\w*", n.text))
    for c in n.body + ([_Fake(n.extra[1])] if n.kind == "for" and n.extra[1] else []):
        if c.kind != "simple":
            continue
        s = c.text.replace(" ", "")
        m = re.match(r"(\w+)(?:\+\+|\+=1$|=\1\+1$)", s)
        if m and m.group(1) in cond_vars:
            return m.group(1)
    return ""


def _Fake(text: str) -> Node:
    return Node("simple", text, 0, 0, text)


def _short(n: Node) -> str:
    return re.sub(r"\s+", " ", n.text)[:40]


def describe_nodes(nodes: list[Node], simple: bool = False, depth: int = 0) -> list[str]:
    """Tugunlar ro'yxatini jumlalar ro'yxatiga aylantiradi (ichma-ich tuzilma bo'laklar bilan)."""
    out: list[str] = []
    i = 0
    pad = "  " * depth
    while i < len(nodes):
        n = nodes[i]
        sw = _swap(nodes, i)
        if sw:
            a, b, t = sw
            out.append(pad + (f"«{a}» va «{b}» dagi qiymatlarning o'rnini almashtiradi («{t}» — vaqtincha quti)." if simple
                              else f"{_name(a, False)} va {_name(b, False)} ning o'rnini almashtiradi ({_name(t, False)} — vaqtincha o'zgaruvchi)."))
            i += 3
            continue
        if n.kind == "simple":
            out.append(pad + describe_simple_stmt(n.text, simple))
        elif n.kind == "return":
            if not n.text:
                out.append(pad + ("Hech narsa qaytarmasdan tugaydi." if not simple else "Ish tugaydi, javob berilmaydi."))
            else:
                e = _parse(n.text)
                p = phrase(e, simple) if e is not None else f"{_name(n.text, simple)} ni"
                out.append(pad + (f"Javob sifatida {p} qaytaradi." if simple else f"{p[0].upper()}{p[1:]} natija qilib qaytaradi."))
        else:
            out += _describe_compound(n, simple, depth)
        i += 1
    return out


def _describe_compound(n: Node, simple: bool, depth: int) -> list[str]:
    pad = "  " * depth
    inner = describe_nodes(n.body, simple, depth + 1)
    bullet = lambda lines: [f"{ln[:len(pad) + 2]}• {ln[len(pad) + 2:]}" if not ln.lstrip().startswith("•") else ln  # noqa: E731
                            for ln in lines]
    if n.kind == "if":
        head = (f"Agar {_cond(n.text, simple)} bo'lsa:" if not simple else f"Agar {_cond(n.text, True)} bo'lsa:")
        res = [pad + head] + bullet(inner)
        if n.other:
            res += [pad + "Aks holda:"] + bullet(describe_nodes(n.other, simple, depth + 1))
        return res
    if n.kind in ("while", "for", "do"):
        cnt = _loop_counter(n)
        if n.kind == "for" and n.extra[0]:
            init = n.extra[0]
            pre = [pad + describe_simple_stmt(init, simple)]
        else:
            pre = []
        cond = _cond(n.text, simple)
        if simple:
            head = f"Quyidagi ishlarni, {cond} ekan, qayta-qayta bajaradi" + (f" ({_name(cnt, True)} har safar 1 taga oshib boradi)" if cnt else "") + ":"
        else:
            head = (f"{cond[0].upper()}{cond[1:]} bo'lib turguncha takrorlaydi" if n.kind != "do" else f"Kamida bir marta, so'ng {cond} bo'lib turguncha takrorlaydi")
            head += (f" ({_name(cnt, False)} har aylanishda 1 ga oshadi)" if cnt else "") + ":"
        return pre + [pad + head] + bullet(inner)
    return [pad + ("Qiymatga qarab tarmoqlanadi:" if not simple else "Qiymatga qarab turli yo'ldan boradi:")] + bullet(inner)


def _title(n: Node) -> str:
    if n.kind == "if":
        return f"Shart: {_short(n)}"
    if n.kind in ("while", "for", "do"):
        return f"Takrorlash: {_short(n)}"
    if n.kind == "return":
        return "Natijani qaytaradi"
    if n.kind == "switch":
        return "Tarmoqlanish"
    parts = _split_assign(n.text)
    if parts is None:
        return "Funksiyani chaqiradi"
    lhs, op, rhs_s = parts
    rhs = _parse(rhs_s)
    ops = {"+": "Qo'shadi", "-": "Ayiradi", "*": "Ko'paytiradi", "/": "Bo'ladi", "%": "Qoldiqni oladi", "^": "XOR qiladi",
           "&": "Bitlarni ajratadi", "|": "Bitlarni birlashtiradi", "<<": "Bitlarni siljitadi", ">>": "Bitlarni siljitadi"}
    if op:
        return f"{ops.get(op, 'O`zgartiradi')}: {lhs}"
    if rhs is None:
        return f"Hisoblaydi: {lhs}"
    if _rotate(rhs):
        return f"Bitlarni aylantiradi: {lhs}"
    if rhs[0] == "num":
        return f"Qiymat beradi: {lhs} = {rhs[1]}"
    if rhs[0] == "var":
        return f"Ko'chiradi: {lhs}"
    if rhs[0] == "bin" and rhs[2] == ("var", lhs.replace(" ", "")) and rhs[3][0] == "num" and rhs[1] in "+-":
        return f"Hisoblagich: {lhs}"
    if rhs[0] == "bin" and rhs[2] == ("var", lhs.replace(" ", "")) and rhs[1] == "^" and _ARR_RE.match(lhs.replace(" ", "")):
        return f"Buferni XOR qiladi: {lhs}"
    if rhs[0] == "bin":
        return f"{ops.get(rhs[1], 'Hisoblaydi')}: {lhs}"
    return f"Hisoblaydi: {lhs}"


def _run_title(run: list[Node]) -> str:
    """Ketma-ket oddiy gaplar guruhi uchun sarlavha."""
    def plain(n: Node) -> bool:
        a = _split_assign(n.text)
        r = _parse(a[2]) if a and not a[1] else None
        return r is not None and (r[0] in ("num", "var") and not _CALL_RE.match(r[1] if r[0] == "var" else ""))
    if len(run) > 1 and all(plain(n) for n in run):
        return "Boshlang'ich qiymatlar"
    return _title(run[0]) + (f" va yana {len(run) - 1} ta amal" if len(run) > 1 else "")


def walkthrough(func_text: str, max_run: int = 3) -> list[Step]:
    """Tozalangan funksiyani bajarilish tartibida qadamlarga ajratadi: har bir tsikl/shart/qaytarish — alohida
    qadam, ketma-ket oddiy gaplar esa (<= max_run) bitta qadamga yig'iladi."""
    nodes = parse_function(func_text)
    steps: list[Step] = []
    run: list[Node] = []

    def flush() -> None:
        if not run:
            return
        sentences = describe_nodes(run, False)
        simples = describe_nodes(run, True)
        title = _run_title(run)
        steps.append(Step(run[0].line, run[-1].end, "\n".join(n.src for n in run), title,
                          "\n".join(sentences), "\n".join(simples)))
        run.clear()

    for n in nodes:
        if n.kind == "simple":
            run.append(n)
            if len(run) >= max_run:
                flush()
            continue
        flush()
        steps.append(Step(n.line, n.end, n.src, _title(n), "\n".join(describe_nodes([n], False)),
                          "\n".join(describe_nodes([n], True))))
    flush()
    return steps


# ---------------------------------------------------------------- funksiya nima qiladi

def _walk(nodes: list[Node]):
    for n in nodes:
        yield n
        yield from _walk(n.body)
        yield from _walk(n.other)


def _subst(n, env: dict):
    """Ifodadagi o'zgaruvchilarni ularga yozilgan ifodalar bilan almashtiradi."""
    if n[0] == "var":
        return env.get(n[1], n)
    if n[0] == "num":
        return n
    if n[0] == "cast":
        return ("cast", n[1], n[2], _subst(n[3], env))
    if n[0] == "un":
        return ("un", n[1], _subst(n[2], env))
    if n[0] == "cond":
        return ("cond", _subst(n[1], env), _subst(n[2], env), _subst(n[3], env))
    return ("bin", n[1], _subst(n[2], env), _subst(n[3], env))


def readable(n, parent: str = "") -> str:
    """Ifodani qavslar bilan o'qishga qulay yozadi: (a + b) ^ (a - b) — bitli va arifmetik amallar aralashmasi
    C ustuvorliklariga tayanmasdan, aniq ko'rinadi."""
    if n[0] != "bin":
        return E.to_c(n)
    left, right = readable(n[2], n[1]), readable(n[3], n[1] + "R")
    text = f"{left} {n[1]} {right}"
    if not parent:
        return text
    plain = (parent in ("+", "-") and n[1] in ("*", "/", "%")) or (parent == n[1] and n[1] in ("+", "*", "^", "|", "&"))
    return text if plain else f"({text})"


def _final_expr(nodes: list[Node]):
    """Tarmoqlanishsiz funksiyaning qaytariladigan ifodasi (oraliq o'zgaruvchilar o'rniga qo'yilgan) yoki None."""
    env: dict = {}
    for n in nodes:
        if n.kind == "return":
            e = _parse(n.text) if n.text else None
            return _subst(e, env) if e is not None else None
        parts = _split_assign(n.text) if n.kind == "simple" else None
        rhs = _parse(parts[2]) if parts else None
        if parts is None or rhs is None or not re.fullmatch(r"[A-Za-z_]\w*", parts[0]):
            return None
        lhs, op, _ = parts
        val = _subst(rhs, env)
        env[lhs] = ("bin", op, env.get(lhs, ("var", lhs)), val) if op else val
    return None


def straight_line_formula(nodes: list[Node]) -> str | None:
    """Tarmoqlanish va tsiklsiz funksiyani bitta formulaga yig'adi (oraliq o'zgaruvchilar o'rniga qo'yiladi)."""
    env: dict = {}
    for n in nodes:
        if n.kind == "return":
            e = _parse(n.text)
            return readable(_subst(e, env)) if e is not None and n.text else None
        if n.kind != "simple":
            return None
        parts = _split_assign(n.text)
        rhs = _parse(parts[2]) if parts else None
        if parts is None or rhs is None or not re.fullmatch(r"[A-Za-z_]\w*", parts[0]):
            return None
        lhs, op, _ = parts
        val = _subst(rhs, env)
        env[lhs] = ("bin", op, env.get(lhs, ("var", lhs)), val) if op else val
    return None


def _rotate_shape(n):
    """(x << s1) | (x >> s2) — aylantirish (rotate) shakli. (x, s1) yoki None."""
    if n[0] == "bin" and n[1] == "|" and n[2][0] == "bin" and n[3][0] == "bin" and {n[2][1], n[3][1]} == {"<<", ">>"} \
            and n[2][2] == n[3][2]:
        return n[2][2], (n[2][3] if n[2][1] == "<<" else n[3][3])
    return None


def _has_cmp_of_elements(nodes: list[Node]) -> str:
    """Qo'shni massiv elementlarini solishtiradigan shart bo'lsa, '>' yoki '<' qaytaradi."""
    for n in _walk(nodes):
        if n.kind == "if":
            e = _parse(n.text)
            if e is not None and e[0] == "bin" and e[1] in "<>" and _ARR_RE.match(E.to_c(e[2]).replace(" ", "")) \
                    and _ARR_RE.match(E.to_c(e[3]).replace(" ", "")):
                return e[1]
    return ""


def meaning(func_name: str, params: list[tuple[str, str]], func_text: str,
            decoded: dict[str, str] | None = None) -> tuple[str, str]:
    """Funksiya nima hisoblashini bir-ikki jumla bilan aytadi: (mutaxassis uchun, oddiy tilda).

    params — [(tur, nom)]. Bu oddiy qoidalar: aniq tanilgan usul (EKUB, FNV xesh, saralash, XOR ...) bo'lsa
    o'sha aytiladi, bo'lmasa kod tuzilmasidan umumiy tavsif yasaladi.
    """
    nodes = parse_function(func_text)
    allnodes = list(_walk(nodes))
    loops = [n for n in allnodes if n.kind in ("while", "for", "do")]
    masked = mask_code(func_text)
    consts = {(E.c_int(m.group(1)) or 0) & 0xFFFFFFFF for m in E.C_INT_RE.finditer(masked)}
    names = [n for _, n in params]
    ptrs = [n for t, n in params if "*" in t]
    ints = [n for t, n in params if "*" not in t]
    out: tuple[str, str] | None = None

    # 1) tanish mumkin bo'lgan usullar
    if 0x811C9DC5 in consts or 0x01000193 in consts:
        out = ("kirish ma'lumotining baytlaridan FNV-1a xesh (qisqa «barmoq izi» son) hisoblaydi: boshlang'ich qiymatga har bir bayt "
               "XOR qilinadi va natija FNV tub soniga ko'paytiriladi.",
               "Bu funksiya ma'lumotdan qisqa «barmoq izi» (xesh) yasaydi: baytlarni birma-bir olib, har birini oldingi natijaga "
               "aralashtirib boradi. Bir xil ma'lumotdan har doim bir xil «iz» chiqadi, boshqasidan esa deyarli har doim boshqacha.")
    elif 0xEDB88320 in consts or 0x04C11DB7 in consts:
        out = ("CRC-32 nazorat yig'indisini hisoblaydi (ma'lumot butunligini tekshirish uchun).",
               "Bu funksiya ma'lumot buzilmaganini tekshirish uchun qisqa «nazorat raqami» hisoblaydi, xuddi kitob sahifalarini "
               "sanab, oxirida «sahifalar soni to'g'rimi?» deb tekshirgandek.")
    elif any(n.kind == "while" and (e := _parse(n.text)) is not None and e[0] == "var" and any(
            c.kind == "simple" and re.search(rf"%\s*{re.escape(e[1])}\b", c.text) for c in _walk(n.body)) for n in loops):
        out = ("Evklid algoritmi bilan ikki sonning eng katta umumiy bo'luvchisini (EKUB) topadi: kattasini kichigiga bo'lib, "
               "qoldiq bilan davom etadi va qoldiq nolga teng bo'lganda javobni qaytaradi.",
               "Bu funksiya ikki sonni oladi va ikkalasiga ham qoldiqsiz bo'linadigan eng katta sonni topadi (12 va 18 uchun u 6). "
               "Usul qadimiy: kattasini kichigiga bo'lib, qolgan qoldiq bilan ishni davom ettiraveradi, qoldiq tugaguncha.")
    else:
        swap = any(_swap(lst, i) for lst in _lists(nodes) for i in range(len(lst)))
        cmp_ = _has_cmp_of_elements(nodes)
        arr_xor = any(n.kind == "simple" and (a := _split_assign(n.text)) and _ARR_RE.match(a[0].replace(" ", ""))
                      and ("^" in a[2] or a[1] == "^") for n in allnodes)
        if swap and len(loops) >= 2 and cmp_:
            order = "o'sish" if cmp_ == ">" else "kamayish"
            arr = ptrs[0] if ptrs else "massiv"
            out = (f"{_name(arr, False)} massivini {order} tartibida saralaydi (pufakchali saralash): qo'shni elementlar noto'g'ri "
                   "tartibda tursa, o'rnini almashtiradi va buni tartib to'g'ri bo'lguncha takrorlaydi.",
                   "Bu funksiya qatorga tizilgan sonlarni " + ("kichigidan kattasiga" if cmp_ == ">" else "kattasidan kichigiga") +
                   " qarab tartiblaydi. Qo'shni ikki sonni solishtiradi, tartib noto'g'ri bo'lsa ularning o'rnini almashtiradi, "
                   "va hamma narsa joyiga tushguncha qaytaraveradi — xuddi maktabda bolalarni bo'yi bo'yicha saflagandek.")
        elif arr_xor and loops:
            arr = ptrs[0] if ptrs else "bufer"
            key_upd = any(n.kind == "simple" and (a := _split_assign(n.text)) and re.fullmatch(r"\w+", a[0]) and
                          a[0] in (_split_assign(m.text)[2] if _split_assign(m.text) else "")
                          for m in allnodes if m.kind == "simple" and _split_assign(m.text) and _ARR_RE.match(
                              _split_assign(m.text)[0].replace(" ", "")) for n in allnodes)
            out = (f"{_name(arr, False)} buferining har bir baytini kalit bilan XOR qiladi (oddiy shifrlash/deshifrlash)"
                   + ("; kalit har qadamda yangilanib boradi." if key_upd else "."),
                   "Bu funksiya matn yoki ma'lumotni «qulflaydi» (yoki qulfni ochadi): har bir belgini kalit bilan aralashtirib "
                   "chiqadi. Xuddi shu amalni ikkinchi marta bajarsangiz, hammasi avvalgi holiga qaytadi.")
        elif decoded:
            name, text = next(iter(decoded.items()))
            out = (f"yashirin matn {text!r} ni ochadi ({name}) va uning belgilaridan foydalanadi.",
                   "Bu funksiya ichida yashirin yozuv bor: u qulflangan xat kabi saqlanadi va faqat kerak bo'lganda ochiladi. "
                   "Funksiya shu yozuvdan kerakli belgini topib beradi.")
    if out:
        return out

    # 2) tarmoqlanish va tsiklsiz — bitta formula
    if not loops and not any(n.kind in ("if", "switch") for n in allnodes):
        env_final = _final_expr(nodes)
        if env_final is not None and _rotate_shape(env_final):
            x, sh = _rotate_shape(env_final)
            return (f"{_name(E.to_c(x), False)} ning bitlarini {_name(E.to_c(sh), False)} bit chapga aylantiradi (rotate-left): "
                    "chapdan chiqib ketgan bitlar o'ng tomondan qaytib kiradi.",
                    "Bu funksiya sonning bitlarini aylana bo'ylab suradi: bir chetdan chiqib ketgan bitlar ikkinchi chetdan "
                    "qaytib kiradi, xuddi aylanma stoldagi likopchalar kabi.")
        formula = straight_line_formula(nodes)
        if formula and len(formula) <= 140:
            return (f"{_name(func_name, False)}({', '.join(names)}) = {_name(formula, False)} ni hisoblab qaytaradi.",
                    "Bu funksiya qisqa hisob qiladi: berilgan sonlardan bir necha amal bilan yangi son hosil qiladi va uni "
                    "javob sifatida qaytaradi. Qadamlari pastda tartib bilan yozilgan.")

    # 3) umumiy tavsif
    ops = []
    for sym, word in (("+", "qo'shish"), ("-", "ayirish"), ("*", "ko'paytirish"), ("%", "qoldiq olish"), ("^", "XOR"),
                      ("<<", "bit siljitish"), (">>", "bit siljitish"), ("&", "bitli VA"), ("|", "bitli YOKI")):
        if re.search(rf"(?<![<>&|=!+\-*/%^]){re.escape(sym)}(?!=)(?![{re.escape(sym)}])" if sym not in ("<<", ">>") else re.escape(sym), masked) and word not in ops:
            ops.append(word)
    n_if = sum(n.kind == "if" for n in allnodes)
    walks_array = bool(loops) and bool(ptrs) and any(
        re.search(rf"\b{re.escape(a)}\s*\[", n.src) for n in loops for a in ptrs)
    what = []
    if loops:
        what.append(f"{len(loops)} ta tsikl")
    if n_if:
        what.append(f"{n_if} ta shart")
    ret = next((n.text for n in reversed(nodes) if n.kind == "return" and n.text), "")
    tech = (f"{_name(func_name, False)}({', '.join(names)}) funksiyasi " + (" va ".join(what) + " ichida " if what else "")
            + (f"{', '.join(ops[:4])} amallarini bajaradi" if ops else "hisob-kitob qiladi")
            + (f" va {_name(ret, False)} ni qaytaradi." if ret else " va qiymat qaytarmaydi."))
    if not loops and n_if:
        tech = (f"{_name(func_name, False)}({', '.join(names)}) kirishlarni solishtiradi va shartlarga qarab mos qiymatni "
                f"tanlab {_name(ret, False) if ret else 'qaytaradi'}" + (" ni qaytaradi." if ret else "."))
    elif walks_array:
        tech = (f"{_name(ptrs[0], False)} ning elementlari bo'ylab tsiklda yuradi, har biri bilan hisob-kitob qilib, "
                "yig'ilgan qiymatni yangilab boradi" + (f" va oxirida {_name(ret, False)} ni qaytaradi." if ret else "."))
    plain = ("Bu funksiya berilgan sonlar ustida bir necha hisob-kitob qiladi"
             + (" va ro'yxatdagi har bir element uchun bir xil ishni takrorlaydi" if loops and ptrs else
                (" va bir xil ishni qayta-qayta takrorlaydi" if loops else ""))
             + (", ba'zi joylarda esa «agar ... bo'lsa» deb yo'l tanlaydi" if n_if else "")
             + (". Oxirida natijani javob qilib beradi." if ret else ". Natijani qaytarmaydi, faqat ma'lumotni joyida o'zgartiradi.")
             + " Har bir qadam pastda alohida tushuntirilgan.")
    if not loops and n_if:
        plain = ("Bu funksiya sonlarni bir-biri bilan solishtirib, qaysi yo'ldan borishni tanlaydi — yo'l ayrilishidagi "
                 "yo'lovchi kabi — va mos javobni beradi. Har bir qadam pastda alohida tushuntirilgan.")
    return tech, plain


def _lists(nodes: list[Node]):
    """Barcha ichma-ich tugunlar ro'yxatlari (o'rin almashtirish naqshini qidirish uchun)."""
    yield nodes
    for n in nodes:
        yield from _lists(n.body)
        yield from _lists(n.other)
