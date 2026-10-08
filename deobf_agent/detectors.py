"""Statik tahlil: obfuskatsiya usullarini LLM'siz (bepul) aniqlovchi detektorlar.

Har bir detektor funksiya matnini ko'rib chiqadi va `Finding` (topilma) ro'yxatini
qaytaradi. Bu topilmalar ikki joyda ishlatiladi:
  1) LLM'ga "maslahat" sifatida beriladi — LLM ishini osonlashtiradi va xatolarini
     kamaytiradi (masalan, qaysi shart soxta ekanini biz allaqachon isbotlaganmiz);
  2) offline rejimda (API kalitsiz) to'g'ridan-to'g'ri foydalanuvchiga ko'rsatiladi.

Detektorlar:
  * mba                       — aralash arifmetik-mantiqiy ifodalar (+ soddalashtirish)
  * encoded_constants         — faqat konstantalardan iborat ifodalar (yig'ib hisoblash)
  * opaque_predicate          — har doim rost/yolg'on bo'lgan shartlar
  * dead_code                 — natijaga ta'sir qilmaydigan o'zgaruvchilar va o'lik tarmoqlar
  * control_flow_flattening   — while(1){switch(state)...} holatlar mashinasi
  * encoded_strings           — XOR bilan kodlangan satrlar
  * known_constants           — mashhur algoritmlarning "sehrli" konstantalari (FNV, CRC32, ...)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from itertools import permutations

from . import expr as E
from .models import Finding, FunctionInfo
from .parser import find_close, mask_code, split_top_level

# Mashhur algoritmlarning konstantalari: topilsa, funksiya nima qilishini tushunishga yordam beradi.
KNOWN_CONSTANTS = {
    0x811C9DC5: "FNV-1a xesh algoritmining boshlang'ich qiymati (offset basis)",
    0x01000193: "FNV xesh algoritmining tub soni (FNV prime)",
    0xEDB88320: "CRC-32 polinomi (teskari ko'rinishi)",
    0x04C11DB7: "CRC-32 polinomi",
    0x9E3779B9: "TEA/XTEA shifrlash algoritmining 'delta' konstantasi (oltin kesim)",
    0x67452301: "MD5/SHA-1 boshlang'ich holati (A)",
    0xEFCDAB89: "MD5/SHA-1 boshlang'ich holati (B)",
    0x6A09E667: "SHA-256 boshlang'ich holati (H0)",
    0x428A2F98: "SHA-256 raund konstantasi K[0]",
    0x5A827999: "SHA-1 raund konstantasi",
    0x1505: "djb2 xesh algoritmining boshlang'ich qiymati (5381)",
    0x5BD1E995: "MurmurHash2 konstantasi",
    0xCC9E2D51: "MurmurHash3 konstantasi (c1)",
    0x41C64E6D: "Chiziqli kongruent generator (LCG, glibc rand) ko'paytuvchisi",
    0x343FD: "Chiziqli kongruent generator (MSVC rand) ko'paytuvchisi",
}


@dataclass
class StateMachine:
    """Control-flow flattening dan tiklangan holatlar mashinasi."""

    state_var: str
    initial: int | None
    transitions: dict[int, list[tuple[str, int | None]]] = field(default_factory=dict)  # holat -> [(shart, keyingi)]
    returns: list[int] = field(default_factory=list)                                     # return qiluvchi holatlar
    order: list[int] = field(default_factory=list)                                      # bajarilish tartibi (DFS)

    def describe_uz(self) -> str:
        lines = [f"Holat o'zgaruvchisi: {self.state_var}; boshlang'ich holat: {self.initial}"]
        for st in self.order or list(self.transitions):
            outs = self.transitions.get(st, [])
            parts = []
            for cond, nxt in outs:
                target = "return (chiqish)" if nxt is None else str(nxt)
                parts.append(f"{target}" + (f"  [agar {cond}]" if cond else ""))
            if st in self.returns and not outs:
                parts.append("return (chiqish)")
            lines.append(f"  holat {st} -> " + (" | ".join(parts) if parts else "?"))
        return "\n".join(lines)


@dataclass
class AnalysisResult:
    findings: list[Finding]
    state_machines: list[StateMachine] = field(default_factory=list)
    decoded_strings: dict[str, str] = field(default_factory=dict)

    def techniques(self) -> list[str]:
        return list(dict.fromkeys(f.technique for f in self.findings))


# ====================================================================== yordamchilar

@dataclass
class _Stmt:
    text: str          # izohsiz matn
    line: int          # funksiya ichidagi qator (1 dan)
    headers: list[str] # oldidagi if(...)/while(...) shartlari


def _close_paren(text: str, start: int) -> int:
    """text[start] == '(' bo'lsa, mos ')' indeksi (yopilmagan bo'lsa — matn oxiri)."""
    j = find_close(text, start, "()")
    return len(text) - 1 if j < 0 else j


def _statements(func: FunctionInfo) -> list[_Stmt]:
    """Funksiya tanasini oddiy gaplarga ajratadi (';', '{', '}' bo'yicha)."""
    masked = mask_code(func.text)
    body_start = masked.find("{")
    out: list[_Stmt] = []
    i, n = body_start + 1, len(masked)
    cur_start = i
    while i < n:
        ch = masked[i]
        if ch == "(":
            i = _close_paren(masked, i) + 1
            continue
        if ch in ";{}":
            chunk = masked[cur_start:i]
            if ch == ";" or chunk.strip():
                lead = len(chunk) - len(chunk.lstrip())
                line = masked.count("\n", 0, cur_start + lead) + 1
                headers, rest = _peel_headers(chunk.strip())
                out.append(_Stmt(rest, line, headers))
            cur_start = i + 1
        i += 1
    return out


_HEADER_RE = re.compile(r"^(?:else\b|do\b|case\s+[^:]+:|default\s*:|[A-Za-z_]\w*\s*:(?!:))\s*")


def _peel_headers(chunk: str) -> tuple[list[str], str]:
    """'if (c) x = 1' -> (['c'], 'x = 1'). else/case/default/belgi (label) olib tashlanadi."""
    headers: list[str] = []
    while True:
        m = _HEADER_RE.match(chunk)
        if m:
            chunk = chunk[m.end():]
            continue
        m = re.match(r"^(if|while|for|switch)\s*\(", chunk)
        if m:
            open_idx = chunk.index("(", m.start(1))
            close = _close_paren(chunk, open_idx)
            headers.append(chunk[open_idx + 1:close])
            chunk = chunk[close + 1:].lstrip()
            continue
        return headers, chunk.strip()


_DECL_PREFIX_RE = re.compile(r"^((?:[A-Za-z_]\w*\s+)+\**\s*)(?=[A-Za-z_*])")
_NOT_TYPES = {"return", "goto", "case", "else", "do", "if", "while", "for", "switch", "break", "continue", "sizeof"}


def _split_stmt(text: str) -> list[tuple[str, str, str | None]]:
    """Gapdan qiymat berishlarni ajratadi: [(chap_tomon, operator, o'ng_tomon yoki None)].

      'v1 = a0 + 1'                    -> [('v1', '=', 'a0 + 1')]
      'unsigned int h = 0u, junk = 0u' -> [('h', '=', '0u'), ('junk', '=', '0u')]   (e'lon)
      'int v2'                         -> [('v2', '=', None)]                         (e'lon)
      'buf[i] ^= k'                    -> [('buf[i]', '^=', 'k')]                     (murakkab chap tomon)
    """
    d = _DECL_PREFIX_RE.match(text)
    if d and not (set(d.group(1).split()) & _NOT_TYPES):
        out = []
        for part in split_top_level(text[d.end():]):
            part = part.lstrip("*").strip()
            pm = re.match(r"^([A-Za-z_]\w*)\s*(?:\[[^\]]*\])?\s*(?:=\s*(.+))?$", part, re.S)
            if not pm:
                return []
            out.append((pm.group(1), "=", pm.group(2).strip() if pm.group(2) else None))
        return out
    found = _find_assign(text)
    return [found] if found else []


def is_declaration(text: str) -> bool:
    d = _DECL_PREFIX_RE.match(text)
    return bool(d) and not (set(d.group(1).split()) & _NOT_TYPES)


def _find_assign(text: str) -> tuple[str, str, str] | None:
    """Qavslardan tashqaridagi birinchi qiymat berish operatorini topadi (==, <=, >=, != hisobga olinmaydi)."""
    depth = 0
    for i, ch in enumerate(text):
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == "=" and depth == 0:
            prev = text[i - 1] if i else ""
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if nxt == "=" or prev in "=!":
                return None
            op_start = i
            if prev in "+-*/%&|^":
                op_start = i - 1
            elif prev in "<>":
                if i >= 2 and text[i - 2] == prev:
                    op_start = i - 2
                else:
                    return None                    # <= yoki >= — taqqoslash
            lhs, rhs = text[:op_start].strip(), text[i + 1:].strip()
            if lhs and rhs:
                return lhs, text[op_start:i + 1], rhs
            return None
    return None


def _expressions(func: FunctionInfo):
    """(qator, matn, turi) — funksiyadagi barcha ifodalar: o'ng tomonlar, return, shartlar."""
    for st in _statements(func):
        for h in st.headers:
            if h.count(";") == 0:
                yield st.line, h, "cond"
        assigns = _split_stmt(st.text)
        for _, _, rhs in assigns:
            if rhs:
                yield st.line, rhs, "rhs"
        if not assigns and st.text.startswith("return"):
            r = st.text[len("return"):].strip()
            if r:
                yield st.line, r, "return"


def var_types(func: FunctionInfo) -> E.Types:
    """Funksiya o'zgaruvchilarining turlari: parametrlar va e'lonlardan. {nom: (bitlar, ishorali)}

    Bu muhim: `int v2; if (v2 < 0)` dagi shart ishorali sonda ma'noli, ishorasizda esa doim yolg'on.
    Turi aniqlanmagan o'zgaruvchilar uchun kalkulyator barcha talqinlarni sinaydi.
    """
    types: E.Types = {}
    for p in func.params:
        t = E.type_info(p.type)
        if t:
            types[p.name] = t
    for st in _statements(func):
        d = _DECL_PREFIX_RE.match(st.text)
        if not d or not is_declaration(st.text):
            continue
        base = d.group(1)
        for part in split_top_level(st.text[d.end():]):
            m = re.match(r"(\**)\s*([A-Za-z_]\w*)\s*(\[)?", part.strip())
            if not m:
                continue
            t = (64, False) if (m.group(1) or m.group(3) or "*" in base) else E.type_info(base)
            if t:
                types[m.group(2)] = t
    return types


def _try_parse(text: str):
    try:
        return E.parse(text)
    except E.ExprError:
        return None


# ====================================================================== MBA va konstantalar

def _candidates(names: list[str], consts: list[int]):
    """Soddalashtirish uchun nomzod ifodalar — eng soddasidan boshlab."""
    ks = [k for k in consts if k <= 0xFFFFFFFF][:4]
    for k in (1, 2):
        if k not in ks:
            ks.append(k)
    for x in names:
        yield x
    for x in names:
        yield f"~{x}"
        yield f"-{x}"
    for x, y in permutations(names, 2):
        for op in ("+", "-", "^", "|", "&", "*"):
            if op in ("+", "^", "|", "&", "*") and names.index(x) > names.index(y):
                continue
            yield f"{x} {op} {y}"
    for x in names:
        for k in ks:
            for op in ("+", "-", "^", "&", "|", "*"):
                yield f"{x} {op} {k}"
    for x, y in permutations(names, 2):
        yield f"{x} & ~{y}"
        if names.index(x) < names.index(y):
            yield f"~({x} & {y})"
            yield f"~({x} | {y})"
            yield f"~({x} ^ {y})"
    if len(names) == 3:
        a, b, c = names
        for o1 in ("+", "^", "|", "&"):
            for o2 in ("+", "^", "|", "&", "-"):
                yield f"{a} {o1} {b} {o2} {c}"


def simplify_mba(node, types: E.Types | None = None) -> str | None:
    """MBA ifodaga teng oddiy ifodani qidiradi (tasodifiy test bilan tasdiqlanadi)."""
    names = E.variables(node)
    if not names:
        return None
    for cand in _candidates(names, E.constants(node)) if len(names) <= 3 else ():
        cnode = _try_parse(cand)
        if cnode is not None and E.equivalent(node, cnode, 600, types) and E.equivalent(node, cnode, 3000, types):
            return cand
    cand = _linear_fit(node, names, types)
    if cand is not None:
        cnode = _try_parse(cand)
        if cnode is not None and E.equivalent(node, cnode, 3000, types):
            return cand
    return None


def _term(coef: int, expr: str) -> str:
    """Koeffitsient va ifodani o'qishga qulay qo'shiluvchiga aylantiradi: (5, 'x') -> '+ x * 5'."""
    coef &= 0xFFFFFFFF
    if coef > 0x7FFFFFFF:
        sign, coef = "-", (-coef) & 0xFFFFFFFF
    else:
        sign = "+"
    body = expr if coef == 1 else (str(coef) if expr == "1" else f"{expr} * {coef}")
    return f"{sign} {body}"


def _linear_fit(node, names: list[str], types: E.Types | None = None) -> str | None:
    """Chiziqli MBA ni "koeffitsientlarni topish" orqali soddalashtiradi (SiMBA / MBA-Blast g'oyasi).

    1-2 o'zgaruvchili har qanday chiziqli MBA quyidagi shaklda yoziladi:
        c0 + c1*x + c2*y + c3*(x & y)
    Koeffitsientlar ifodani 4 nuqtada (x, y in {0, 1}) hisoblash orqali topiladi:
        c0 = E(0,0);  c1 = E(1,0) - c0;  c2 = E(0,1) - c0;  c3 = E(1,1) - c0 - c1 - c2
    Natija baribir tasodifiy test bilan tekshiriladi (chiziqli bo'lmagan ifodalar o'tmaydi).
    """
    if not 1 <= len(names) <= 2:
        return None

    def ev(*vals):
        return E.evaluate(node, dict(zip(names, vals)), types)[0] & 0xFFFFFFFF

    try:
        if len(names) == 1:
            c0 = ev(0)
            coefs = [(ev(1) - c0, names[0])]
        else:
            c0 = ev(0, 0)
            c1, c2 = ev(1, 0) - c0, ev(0, 1) - c0
            c3 = ev(1, 1) - c0 - c1 - c2
            x, y = names
            coefs = [(c1, x), (c2, y), (c3, f"({x} & {y})")]
            # k*x + k*y - k*(x&y) = k*(x | y);  k*x + k*y - 2k*(x&y) = k*(x ^ y)
            k = c1 & 0xFFFFFFFF
            if k and (c2 & 0xFFFFFFFF) == k:
                if (c3 + k) & 0xFFFFFFFF == 0:
                    coefs = [(k, f"({x} | {y})")]
                elif (c3 + 2 * k) & 0xFFFFFFFF == 0:
                    coefs = [(k, f"({x} ^ {y})")]
    except E.ExprError:
        return None
    terms = [_term(c, e) for c, e in coefs if c & 0xFFFFFFFF] + ([_term(c0, "1")] if c0 else [])
    if not terms:
        return "0"
    text = " ".join(terms)
    return text[2:] if text.startswith("+ ") else "-" + text[2:]


_LOGIC_OPS = {"==", "!=", "<", ">", "<=", ">=", "&&", "||"}


def is_logic(node) -> bool:
    """Taqqoslash/mantiqiy ifoda (==, <, &&, !, a ? b : c) — bular MBA emas, opaque predicate detektoriga tegishli."""
    return node[0] == "cond" or (node[0] == "bin" and node[1] in _LOGIC_OPS) or (node[0] == "un" and node[1] == "!")


def looks_like_mba(node) -> bool:
    """MBA belgisi: kamida bitta arifmetik va bitta bit amali, jami kamida 3 ta amal."""
    arith, bitw = E.count_ops(node)
    return arith >= 1 and bitw >= 1 and arith + bitw >= 3


def detect_mba_and_constants(func: FunctionInfo, types: E.Types | None = None) -> list[Finding]:
    findings: list[Finding] = []
    for line, text, kind in _expressions(func):
        root = _try_parse(text)
        if root is None:
            continue
        done: list = []   # allaqachon hisobotga kirgan (katta) tugunlar — ularning ichini qayta ko'rmaymiz

        def covered(n):
            return any(n is d or any(n is s for s in E.subnodes(d)) for d in done)

        for node in E.subnodes(root):
            if covered(node) or node[0] in ("num", "var"):
                continue
            # 1) Faqat konstantalardan iborat ifoda -> bitta songa yig'ish
            if not E.variables(node) and node[0] != "cast" and not (node[0] == "un" and node[2][0] == "num"):
                try:
                    v = E.evaluate(node, {})[0] & 0xFFFFFFFFFFFFFFFF
                except E.ExprError:
                    continue
                note = KNOWN_CONSTANTS.get(v & 0xFFFFFFFF, "")
                findings.append(Finding(
                    technique="encoded_constants", line=line, snippet=E.to_c(node), suggestion=str(v),
                    message=f"Konstanta yashirilgan: `{E.to_c(node)}` = {v} (0x{v:X})" + (f" — {note}" if note else ""),
                    confidence=1.0, verified=True))
                done.append(node)
                continue
            # 2) MBA
            if is_logic(node) or not looks_like_mba(node):
                continue
            simple = simplify_mba(node, types)
            if simple and simple.replace(" ", "") != E.to_c(node).replace(" ", ""):
                findings.append(Finding(
                    technique="mba", line=line, snippet=E.to_c(node), suggestion=simple,
                    message=f"MBA ifoda: `{E.to_c(node)}` aslida `{simple}` ga teng "
                            f"(3000 ta tasodifiy test bilan tekshirildi)",
                    confidence=0.95, verified=True))
                done.append(node)
            elif node is root and kind != "cond" and min(E.count_ops(node)) >= 2:
                findings.append(Finding(
                    technique="mba", line=line, snippet=E.to_c(node),
                    message="Murakkab aralash arifmetik-mantiqiy ifoda (MBA bo'lishi mumkin), "
                            "oddiy ekvivalenti avtomatik topilmadi",
                    confidence=0.4))
                done.append(node)
    return findings


# ====================================================================== opaque predicate

def detect_opaque_predicates(func: FunctionInfo, types: E.Types | None = None) -> list[Finding]:
    findings: list[Finding] = []
    for line, text, kind in _expressions(func):
        root = _try_parse(text)
        if root is None:
            continue
        conds = [root] if kind == "cond" else []
        conds += [n[1] for n in E.subnodes(root) if n[0] == "cond"]       # a ? b : c ichidagi shartlar
        for c in conds:
            if not E.variables(c):
                continue                                                  # while(1) — oddiy cheksiz tsikl
            # Shart ichidagi ba'zi qismlar (&& bilan bog'langan) alohida ham tekshiriladi
            parts = [c] + [n for n in E.subnodes(c) if n is not c and n[0] == "bin"
                           and n[1] in ("==", "!=", "<", ">", "<=", ">=", "&", "%") and E.variables(n)]
            for part in parts:
                val = E.is_constant(part, 3000, types)
                if val is None:
                    continue
                truth = "ROST" if val else "YOLG'ON"
                findings.append(Finding(
                    technique="opaque_predicate", line=line, snippet=E.to_c(part), suggestion=str(int(bool(val))),
                    message=f"Soxta shart (opaque predicate): `{E.to_c(part)}` har doim {truth} "
                            f"(o'zgaruvchilar qiymatidan qat'i nazar, 3000 test)"
                            + (". Bu shart ostidagi kod hech qachon bajarilmaydi (o'lik kod)." if not val and part is c else ""),
                    confidence=0.9, verified=True))
                break
    return findings


# ====================================================================== o'lik kod

def detect_dead_variables(func: FunctionInfo) -> list[Finding]:
    """Qiymati faqat o'ziga o'zlashtiriladigan, natijaga ta'sir qilmaydigan o'zgaruvchilar."""
    stmts = _statements(func)
    params = {p.name for p in func.params}
    defs: dict[str, list[int]] = {}
    real_reads: dict[str, int] = {}
    for st in stmts:
        for h in st.headers:
            for name in re.findall(r"\b[A-Za-z_]\w*\b", h):
                real_reads[name] = real_reads.get(name, 0) + 1
        assigns = _split_stmt(st.text)
        if not assigns:
            for name in re.findall(r"\b[A-Za-z_]\w*\b", st.text):
                real_reads[name] = real_reads.get(name, 0) + 1
            continue
        for lhs, _, rhs in assigns:
            if re.fullmatch(r"[A-Za-z_]\w*", lhs):
                lines = defs.setdefault(lhs, [])
                if rhs is not None:
                    lines.append(st.line)
            else:                                   # buf[i] = ... — bunda buf va i o'qiladi
                for name in re.findall(r"\b[A-Za-z_]\w*\b", lhs):
                    real_reads[name] = real_reads.get(name, 0) + 1
            for name in re.findall(r"\b[A-Za-z_]\w*\b", rhs or ""):
                if name != lhs:
                    real_reads[name] = real_reads.get(name, 0) + 1
    findings = []
    for var, lines in defs.items():
        if var in params or real_reads.get(var, 0) > 0 or not lines:
            continue
        findings.append(Finding(
            technique="dead_code", line=lines[0], snippet=var,
            message=f"O'zgaruvchi `{var}` ga {len(lines)} marta qiymat beriladi, lekin u hech qayerda "
                    f"ishlatilmaydi — keraksiz (junk) kod, olib tashlash mumkin (qatorlar: {', '.join(map(str, lines))})",
            confidence=0.8))
    return findings


# ====================================================================== flattening

_FOREVER_RE = re.compile(r"\bwhile\s*\(\s*(?:1|true|1u)\s*\)|\bfor\s*\(\s*;\s*;\s*\)|\bdo\b")


def detect_flattening(func: FunctionInfo) -> tuple[list[Finding], list[StateMachine]]:
    masked = mask_code(func.text)
    if not _FOREVER_RE.search(masked):
        return [], []
    findings, machines = [], []
    for sw in re.finditer(r"\bswitch\s*\(\s*([A-Za-z_]\w*)\s*\)", masked):
        var = sw.group(1)
        brace = masked.find("{", sw.end())
        depth, j = 0, brace
        while j < len(masked):
            if masked[j] == "{":
                depth += 1
            elif masked[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        block = masked[brace + 1:j]
        labels = list(re.finditer(r"\bcase\s+([^:]+):|\bdefault\s*:", block))
        if len(labels) < 3:
            continue
        sm = StateMachine(state_var=var, initial=None)
        assigned = 0
        for k, lab in enumerate(labels):
            if lab.group(1) is None:
                continue                                       # default: odatda tuzoq/qayta boshlash
            state = E.const_of(lab.group(1))
            if state is None:
                continue
            seg = block[lab.end(): labels[k + 1].start() if k + 1 < len(labels) else len(block)]
            outs: list[tuple[str, int | None]] = []
            for am in re.finditer(rf"\b{var}\s*=\s*([^;]+);", seg):
                rhs = am.group(1).strip()
                const = E.const_of(rhs)
                if const is not None:
                    outs.append(("", const))
                    assigned += 1
                    continue
                node = _try_parse(rhs)
                if node is not None and node[0] == "cond":
                    a, b = E.const_value(node[2]), E.const_value(node[3])
                    outs.append((E.to_c(node[1]), a))
                    outs.append((E.negate(node[1]), b))
                    assigned += 1
            if re.search(r"\breturn\b", seg):
                sm.returns.append(state)
            sm.transitions[state] = outs
        if assigned < 2:
            continue
        before = masked[:sw.start()]
        init = re.findall(rf"\b{var}\s*=\s*([^;]+);", before)
        sm.initial = E.const_of(init[-1]) if init else None
        # Bajarilish tartibini (DFS) tiklaymiz — LLM uchun foydali "xarita"
        order, stack = [], [sm.initial] if sm.initial in sm.transitions else list(sm.transitions)[:1]
        while stack:
            st = stack.pop()
            if st is None or st in order or st not in sm.transitions:
                continue
            order.append(st)
            for _, nxt in reversed(sm.transitions[st]):
                stack.append(nxt)
        sm.order = order + [s for s in sm.transitions if s not in order]
        machines.append(sm)
        line = masked.count("\n", 0, sw.start()) + 1
        findings.append(Finding(
            technique="control_flow_flattening", line=line, snippet=f"while(1) {{ switch ({var}) ... }}",
            message=f"Control-flow flattening: kod {len(sm.transitions)} ta holatga bo'lingan va "
                    f"`{var}` o'zgaruvchisi orqali boshqariladi. Tiklangan holatlar xaritasi:\n" + sm.describe_uz(),
            confidence=0.9))
    # IDA/Ghidra'da flattening ko'pincha switch emas, if-zanjiri ko'rinishida bo'ladi
    if not machines:
        for var in set(re.findall(r"\b([A-Za-z_]\w*)\s*==\s*(?:0x[0-9A-Fa-f]+|\d{3,})", masked)):
            cmp_consts = set(re.findall(rf"\b{var}\s*==\s*(0x[0-9A-Fa-f]+|\d+)", masked))
            set_consts = set(re.findall(rf"\b{var}\s*=\s*(0x[0-9A-Fa-f]+|\d+)\s*;", masked))
            if len(cmp_consts) >= 3 and len(set_consts) >= 3:
                findings.append(Finding(
                    technique="control_flow_flattening", line=1, snippet=var,
                    message=f"Control-flow flattening (if-zanjiri ko'rinishida): `{var}` o'zgaruvchisi "
                            f"{len(cmp_consts)} ta konstanta bilan solishtiriladi va {len(set_consts)} ta "
                            f"konstanta qabul qiladi — bu holatlar mashinasi belgisi",
                    confidence=0.7))
    return findings, machines


# ====================================================================== kodlangan satrlar

def _text_score(data: bytes) -> float:
    """Matn "tabiiy tilga" qanchalik o'xshashi: eng ko'p uchraydigan harflar va bo'sh joy ulushi."""
    common = set(b"etaoinshrdlu ETAOINSHRDLU")
    return sum(1 for b in data if b in common) / max(1, len(data))


def _looks_like_text(data: bytes) -> bool:
    data = data.rstrip(b"\x00")
    printable = sum(1 for b in data if 32 <= b < 127 or b in (9, 10, 13))
    if len(data) < 4 or printable / len(data) < 0.95:
        return False
    letters = sum(1 for b in data if chr(b).isalpha() or b == 32)
    return letters / len(data) >= 0.6


def detect_encoded_strings(func: FunctionInfo, data_blobs: dict[str, bytes]) -> tuple[list[Finding], dict[str, str]]:
    masked = mask_code(func.text)
    keys = []
    for k in re.findall(r"\^=?\s*(0x[0-9A-Fa-f]+|\d+)[uUlL]*\b", masked):
        v = int(k, 0)
        if 0 < v <= 0xFF and v not in keys:
            keys.append(v)
    findings, decoded = [], {}
    used = [name for name in data_blobs if re.search(rf"\b{re.escape(name)}\b", masked)]
    blobs = {name: data_blobs[name] for name in used}
    # Stekdagi satrlar: v[0] = 0x14; v[1] = 0x39; ... yoki *((char *)&v3 + 1) = 57;
    stack: dict[str, dict[int, int]] = {}
    for m in re.finditer(r"(?:\*\(\([\w\s]+\*\)\s*&?(\w+)\s*\+\s*(\d+)\)|\b(\w+)\[(\d+)\])\s*=\s*(0x[0-9A-Fa-f]+|\d+)\s*;", masked):
        name = m.group(1) or m.group(3)
        idx = int(m.group(2) or m.group(4))
        val = int(m.group(5), 0)
        if val <= 0xFF:
            stack.setdefault(name, {})[idx] = val
    for name, items in stack.items():
        if len(items) >= 4:
            blobs[f"{name} (stek)"] = bytes(items.get(i, 0) for i in range(max(items) + 1))
    for name, data in blobs.items():
        best = None
        if _looks_like_text(data):
            best = (None, data)
        else:
            for k in keys:
                cand = bytes(b ^ k for b in data)
                if _looks_like_text(cand):
                    best = (k, cand)
                    break
            if best is None:                                  # kalit topilmadi — barcha 255 kalitni sinaymiz
                scored = []
                for k in range(1, 256):
                    cand = bytes(b ^ k for b in data)
                    if _looks_like_text(cand):
                        scored.append((_text_score(cand), k, cand))
                if scored:
                    _, k, cand = max(scored)
                    best = (k, cand)
        if best is None:
            continue
        key, plain = best
        text = plain.rstrip(b"\x00").decode("latin-1")
        decoded[name] = text
        how = "ochiq matn" if key is None else f"XOR kaliti 0x{key:02X}" + ("" if key in keys else " (kalit tanlab topildi)")
        findings.append(Finding(
            technique="encoded_strings", line=1, snippet=name, suggestion=text,
            message=f"Kodlangan satr `{name}` ({how}): \"{text}\"",
            confidence=0.95 if key in keys or key is None else 0.6, verified=key in keys or key is None))
    return findings, decoded


def detect_known_constants(func: FunctionInfo) -> list[Finding]:
    masked = mask_code(func.text)
    findings, seen = [], set()
    for m in re.finditer(r"\b(0x[0-9A-Fa-f]+|\d+)[uUlL]*\b", masked):
        v = int(m.group(1), 0) & 0xFFFFFFFF
        if v in KNOWN_CONSTANTS and v not in seen:
            seen.add(v)
            findings.append(Finding(
                technique="known_constants", line=masked.count("\n", 0, m.start()) + 1, snippet=m.group(0),
                message=f"Mashhur konstanta {m.group(0)} (0x{v:X}): {KNOWN_CONSTANTS[v]}", confidence=0.8))
    return findings


# ====================================================================== umumiy

def analyze(func: FunctionInfo, data_blobs: dict[str, bytes] | None = None) -> AnalysisResult:
    """Barcha detektorlarni ishga tushiradi."""
    types = var_types(func)
    findings: list[Finding] = []
    findings += detect_mba_and_constants(func, types)
    findings += detect_opaque_predicates(func, types)
    flat, machines = detect_flattening(func)
    findings += flat
    findings += detect_dead_variables(func)
    strings, decoded = detect_encoded_strings(func, data_blobs or {})
    findings += strings
    findings += detect_known_constants(func)
    findings.sort(key=lambda f: f.line)
    return AnalysisResult(findings=findings, state_machines=machines, decoded_strings=decoded)
