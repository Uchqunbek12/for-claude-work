"""Control-flow flattening ni avtomatik "yechish" (LLM'siz).

Flattening qilingan kod:                         Tiklangan kod:
    state = A;                                       <A tanasi>
    while (1) switch (state) {                       while (shart) {
      case A: <A tanasi>; state = B; break;              <C tanasi>
      case B: state = shart ? C : D; break;          }
      case C: <C tanasi>; state = B; break;          <D tanasi>   (return ...)
      case D: return ...;
    }

Algoritm (graflar nazariyasi):
  1. Har bir `case` — graf tuguni, `state = X` — X tuguniga yo'nalgan qirra.
  2. Boshlang'ich holatdan yurib chiqamiz:
       * bitta chiqishli tugun  -> tanasini yozamiz va keyingisiga o'tamiz (chiziqli ketma-ketlik);
       * shartli tugun (state = c ? X : Y):
           - agar X tarmog'i qaytib shu tugunga kelsa -> bu TSIKL:  while (c) { X... }, keyin Y;
           - aks holda -> if (c) { X... } else { Y... }, keyin ikkala tarmoq qo'shiladigan tugun.
  3. Murakkab holatlarda (ichma-ich halqalar, case ichida shartli state o'zgarishi va h.k.)
     algoritm hech narsani o'zgartirmaydi (None qaytaradi) — bu holatlar LLM'ga qoldiriladi.

Natija har doim differensial test bilan tekshiriladi, shuning uchun xato o'zgarish o'tib ketmaydi.
"""

from __future__ import annotations

import re

from . import expr as E
from .parser import find_close, mask_code


class _Bail(Exception):
    """Bu holatni xavfsiz qayta qurib bo'lmaydi."""


def _match_brace(m: str, i: int) -> int:
    j = find_close(m, i)
    if j < 0:
        raise _Bail("yopuvchi qavs topilmadi")
    return j


def _strip_parens(t: str) -> str:
    t = t.strip()
    while t.startswith("(") and t.endswith(")"):
        depth = 0
        for i, ch in enumerate(t):
            depth += ch == "("
            depth -= ch == ")"
            if depth == 0 and i < len(t) - 1:
                return t                     # "(a) + (b)" — tashqi qavslar bir juft emas
        t = t[1:-1].strip()
    return t


def _split_ternary(rhs: str) -> tuple[str, str, str]:
    """'(shart ? A : B)' -> ('shart', 'A', 'B'). Shart matn sifatida olinadi — uni hisoblash shart emas,
    shuning uchun a0[v1], *(p + 4) kabi murakkab ifodalar ham ishlaydi."""
    t = _strip_parens(rhs)
    depth, q = 0, -1
    for i, ch in enumerate(t):
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == "?" and depth == 0 and q < 0:
            q = i
        elif ch == ":" and depth == 0 and q >= 0:
            return _strip_parens(t[:q]), t[q + 1:i].strip(), t[i + 1:].strip()
    raise _Bail("ternar ifoda emas")


_INVERSE = {"==": "!=", "!=": "==", "<": ">=", ">=": "<", ">": "<=", "<=": ">"}


def _negate_text(cond: str) -> str:
    """Shart inkori: 'a < b' -> 'a >= b', '!x' -> 'x', murakkab holatda '!(...)'."""
    c = cond.strip()
    if c.startswith("!") and not c.startswith("!=") and re.fullmatch(r"!\s*[\w\[\]]+", c):
        return c[1:].strip()
    ops = [m for m in re.finditer(r"==|!=|<=|>=|<(?!<)|>(?!>)", c)
           if c[:m.start()].count("(") == c[:m.start()].count(")")]
    if len(ops) == 1 and "&&" not in c and "||" not in c and "?" not in c:
        m = ops[0]
        prev = c[m.start() - 1] if m.start() else ""
        if prev not in "<>":
            return c[:m.start()].rstrip() + " " + _INVERSE[m.group()] + " " + c[m.end():].lstrip()
    return f"!({c})"


class _Case:
    def __init__(self, body: str, succ: list[tuple[str | None, int | None]], returns: bool, has_code: bool = True):
        self.body = body            # state o'zgaruvchisisiz va break'siz tana
        self.has_code = has_code    # tanada (izohlardan tashqari) kod bormi
        self.succ = succ            # [(shart yoki None, keyingi holat)]
        self.returns = returns


def _parse_cases(text: str, masked: str, var: str, start: int, end: int) -> dict[int, _Case]:
    block_m, block_t = masked[start:end], text[start:end]
    labels = list(re.finditer(r"\bcase\s+([^:]+):|\bdefault\s*:", block_m))
    cases: dict[int, _Case] = {}
    for k, lab in enumerate(labels):
        seg_end = labels[k + 1].start() if k + 1 < len(labels) else len(block_m)
        seg_m, seg_t = block_m[lab.end():seg_end], block_t[lab.end():seg_end]
        if lab.group(1) is None:
            continue                                   # default: odatda tuzoq, e'tiborsiz qoldiramiz
        state = E.const_of(lab.group(1))
        if state is None:
            raise _Bail("case qiymati konstanta emas")
        assigns = list(re.finditer(rf"(?<![\w.>])\b{var}\s*=(?!=)\s*([^;]+);", seg_m))
        for a in assigns:
            before = seg_m[:a.start()]
            if before.count("{") != before.count("}"):
                raise _Bail("state ichki blokda o'zgaradi")
            prev = before.rstrip()
            if prev and not prev.endswith((";", "}", ":")):
                raise _Bail("state shart ostida o'zgaradi")
        returns = bool(re.search(r"\breturn\b", seg_m))
        stripped = seg_m.rstrip()
        if not returns and not stripped.endswith("break;"):
            raise _Bail("case break bilan tugamaydi (fall-through)")
        if len(assigns) > 1 or (not assigns and not returns):
            raise _Bail("murakkab holat o'tishi")
        succ: list[tuple[str | None, int | None]] = []
        body_t, body_m = seg_t, seg_m
        if assigns:
            a = assigns[0]
            rhs = a.group(1).strip()
            c = E.const_of(rhs)
            if c is not None:
                succ = [(None, c)]
            else:
                cond, yes, no = _split_ternary(rhs)
                if E.const_of(yes) is None or E.const_of(no) is None:
                    raise _Bail("holat o'tishi ternar konstanta emas")
                succ = [(cond, E.const_of(yes)), (_negate_text(cond), E.const_of(no))]
            if seg_m[a.end():].strip() not in ("break;", ""):
                raise _Bail("state o'zgarishidan keyin yana kod bor")
            body_t, body_m = seg_t[:a.start()], seg_m[:a.start()]
        body_t = re.sub(r"\bbreak\s*;\s*$", "", body_t.rstrip())
        body_m = re.sub(r"\bbreak\s*;\s*$", "", body_m.rstrip())
        cases[state] = _Case(body_t, succ, returns, has_code=bool(body_m.strip()))
    return cases


def _reach(cases: dict[int, _Case], start: int | None, avoid: set[int]) -> set[int]:
    seen: set[int] = set()
    stack = [start]
    while stack:
        s = stack.pop()
        if s is None or s in seen or s in avoid or s not in cases:
            continue
        seen.add(s)
        stack += [n for _, n in cases[s].succ]
    return seen


def _returns_to(cases: dict[int, _Case], start: int | None, target: int, stop: set[int]) -> bool:
    """start tarmog'idan (target va stop'dan o'tmasdan) target'ga qaytuvchi qirra bormi? — ya'ni halqa."""
    if start == target:
        return True
    for s in _reach(cases, start, avoid=stop | {target}):
        if any(n == target for _, n in cases[s].succ):
            return True
    return False


def _dedent(body: str) -> list[str]:
    lines = [ln for ln in body.splitlines() if ln.strip()]
    if not lines:
        return []
    pad = min(len(ln) - len(ln.lstrip()) for ln in lines)
    return [ln[pad:] for ln in lines]


def _structure(cases: dict[int, _Case], state: int | None, stop: set[int], depth: int = 0) -> list[str]:
    if depth > 50:
        raise _Bail("juda chuqur")
    out: list[str] = []
    visited: set[int] = set()
    while state is not None and state not in stop:
        if state not in cases:
            raise _Bail(f"noma'lum holat {state}")
        if state in visited:
            raise _Bail("kutilmagan halqa")
        visited.add(state)
        c = cases[state]
        out += _dedent(c.body)
        if c.returns or not c.succ:
            return out
        if len(c.succ) == 1:
            state = c.succ[0][1]
            continue
        (cond_t, a), (cond_f, b) = c.succ
        loop_a = _returns_to(cases, a, state, stop)
        loop_b = _returns_to(cases, b, state, stop)
        if loop_a and loop_b:
            raise _Bail("ikkala tarmoq ham halqa")
        if loop_a or loop_b:
            cond, body_start, exit_state = (cond_t, a, b) if loop_a else (cond_f, b, a)
            if c.has_code:
                raise _Bail("shart tugunida qo'shimcha kod bor")   # do-while holati — soddalik uchun o'tkazamiz
            inner = _structure(cases, body_start, stop | {state}, depth + 1)
            out.append(f"while ({cond}) {{")
            out += ["    " + ln for ln in inner]
            out.append("}")
            state = exit_state
            continue
        rb = _reach(cases, b, avoid=stop)
        merge = None
        for s in _chain_order(cases, a, stop):
            if s in rb:
                merge = s
                break
        then = _structure(cases, a, stop | ({merge} if merge is not None else set()), depth + 1)
        other = _structure(cases, b, stop | ({merge} if merge is not None else set()), depth + 1)
        if not then and other:                     # bo'sh "then" bo'lsa — shartni teskari qilamiz
            then, other, cond_t = other, [], cond_f
        if then:
            out.append(f"if ({cond_t}) {{")
            out += ["    " + ln for ln in then]
            if other:
                out.append("} else {")
                out += ["    " + ln for ln in other]
            out.append("}")
        state = merge
    return out


def _chain_order(cases: dict[int, _Case], start: int | None, stop: set[int]) -> list[int]:
    """Holatlarni BFS tartibida qaytaradi (qo'shilish nuqtasini topish uchun)."""
    order, queue, seen = [], [start], set()
    while queue:
        s = queue.pop(0)
        if s is None or s in seen or s in stop or s not in cases:
            continue
        seen.add(s)
        order.append(s)
        queue += [n for _, n in cases[s].succ]
    return order


def unflatten(func_text: str) -> str | None:
    """Funksiya matnidagi flattening'ni yechadi. Yecha olmasa — None."""
    masked = mask_code(func_text)
    sw = re.search(r"\bswitch\s*\(\s*([A-Za-z_]\w*)\s*\)\s*\{", masked)
    if not sw:
        return None
    var = sw.group(1)
    try:
        sw_open = sw.end() - 1
        sw_close = _match_brace(masked, sw_open)
        loop = None
        for lm in re.finditer(r"\bwhile\s*\(\s*(?:1|true|1u)\s*\)\s*\{|\bfor\s*\(\s*;\s*;\s*\)\s*\{", masked[:sw.start()]):
            loop = lm
        if loop is None:
            return None
        loop_open = loop.end() - 1
        loop_close = _match_brace(masked, loop_open)
        if masked[loop_open + 1:sw.start()].strip() or masked[sw_close + 1:loop_close].strip():
            raise _Bail("tsikl ichida switch'dan boshqa kod bor")
        cases = _parse_cases(func_text, masked, var, sw_open + 1, sw_close)
        inits = list(re.finditer(rf"\b{var}\s*=\s*([^;,]+)(?=[;,])", masked[:loop.start()]))
        if not inits or E.const_of(inits[-1].group(1)) is None:
            raise _Bail("boshlang'ich holat topilmadi")
        initial = E.const_of(inits[-1].group(1))
        lines = _structure(cases, initial, set())
    except (_Bail, E.ExprError):
        return None
    indent = re.match(r"[ \t]*", func_text[func_text.rfind("\n", 0, loop.start()) + 1:]).group()
    new_block = ("\n".join(indent + ln for ln in lines)).lstrip()
    init = inits[-1]
    text = func_text[:loop.start()] + new_block + func_text[loop_close + 1:]
    # Boshlang'ich "state = X;" ni olib tashlaymiz (endi state ishlatilmaydi).
    # Agar u e'lon ichida bo'lsa ("unsigned int state = X;"), faqat qiymatni olib tashlaymiz —
    # e'lonning o'zini keyinroq "ishlatilmagan o'zgaruvchi" sifatida tozalash bosqichi olib tashlaydi.
    stmt_start = max(masked.rfind(ch, 0, init.start()) for ch in ";{}") + 1
    after = init.end()
    if not masked[stmt_start:init.start()].strip() and masked[after] == ";":
        text = text[:init.start()] + text[after + 1:]              # "state = X;" — butun gap
    else:
        text = text[:init.start()] + var + text[after:]            # e'lon ichida: faqat "= X" olib tashlanadi
    return text
