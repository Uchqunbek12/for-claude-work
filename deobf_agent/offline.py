"""Offline (bepul) rejim: LLM'siz, faqat statik tahlil asosida natija.

Nima qiladi:
  * isbotlangan soddalashtirishlarni kodga qo'llaydi: MBA ifodalar -> oddiy ifoda,
    yashirin konstantalar -> son, soxta shartlar -> 0/1;
  * qolgan topilmalarni (flattening xaritasi, dekodlangan satrlar, keraksiz
    o'zgaruvchilar) kod boshida izoh sifatida beradi;
  * natijani LLM qaytaradigan tuzilmada (DeobfResult) qaytaradi.

Cheklov: boshqaruv oqimini (flattening) to'liq qayta qurish va mazmunli nomlar berish
uchun "tushunish" kerak — bu LLM rejimining vazifasi. Offline rejim natijasi
"qisman soddalashtirilgan kod + tahlil hisoboti" bo'ladi.
"""

from __future__ import annotations

import re

from . import expr as E
from .detectors import AnalysisResult, _LOGIC_OPS, _balanced, _statements, _split_stmt, simplify_mba, to_c
from .models import FunctionInfo
from .parser import _mask_comments_and_strings
from .schema import Block, DeobfResult

TECH_NAMES_UZ = {
    "mba": "MBA ifoda",
    "opaque_predicate": "Soxta shart (opaque predicate)",
    "control_flow_flattening": "Boshqaruv oqimini tekislash (flattening)",
    "encoded_strings": "Kodlangan satr",
    "encoded_constants": "Yashirilgan konstanta",
    "dead_code": "O'lik / keraksiz kod",
    "known_constants": "Mashhur algoritm konstantasi",
}


def _rewrite(node, is_condition: bool = False):
    """Ifoda daraxtini soddalashtiradi (faqat tasodifiy test bilan tasdiqlangan o'zgarishlar)."""
    if node[0] in ("num", "var"):
        return node
    names = E.variables(node)
    if not names and node[0] != "cast":
        try:
            v = E.evaluate(node, {})[0] & 0xFFFFFFFFFFFFFFFF
            return ("num", v, 64 if v > 0xFFFFFFFF else 32, False)
        except E.ExprError:
            return node
    if is_condition and names:
        const = E.is_constant(node, n=3000)
        if const is not None:
            return ("num", int(bool(const)), 32, True)
    logic = node[0] == "cond" or (node[0] == "bin" and node[1] in _LOGIC_OPS) or (node[0] == "un" and node[1] == "!")
    if not logic:
        arith, bitw = E.count_ops(node)
        if arith >= 1 and bitw >= 1 and arith + bitw >= 3:
            simple = simplify_mba(node)
            if simple:
                return E.parse(simple)
    # bolalarini rekursiv soddalashtiramiz
    if node[0] == "un":
        return ("un", node[1], _rewrite(node[2], is_condition and node[1] == "!"))
    if node[0] == "bin":
        sub_cond = is_condition and node[1] in ("&&", "||")
        return ("bin", node[1], _rewrite(node[2], sub_cond), _rewrite(node[3], sub_cond))
    if node[0] == "cast":
        return ("cast", node[1], node[2], _rewrite(node[3]))
    if node[0] == "cond":
        return ("cond", _rewrite(node[1], True), _rewrite(node[2]), _rewrite(node[3]))
    return node


def _simplify_text(text: str, is_condition: bool) -> str | None:
    try:
        node = E.parse(text)
    except E.ExprError:
        return None
    new = _rewrite(node, is_condition)
    if new == node:
        return None
    return to_c(new)


def simplify_code(func: FunctionInfo) -> tuple[str, list[tuple[int, str, str]]]:
    """Funksiya matniga soddalashtirishlarni qo'llaydi. Natija: (yangi_kod, [(qator, eski, yangi)])."""
    lines = func.text.splitlines()
    changes: list[tuple[int, str, str]] = []
    for st in _statements(func):
        targets = [(h, True) for h in st.headers if ";" not in h]
        assigns, _ = _split_stmt(st.text)
        targets += [(rhs, False) for _, _, rhs in assigns if rhs]
        if not assigns and st.text.startswith("return") and st.text[6:].strip():
            targets.append((st.text[6:].strip(), False))
        for old, is_cond in targets:
            new = _simplify_text(old, is_cond)
            if not new:
                continue
            for idx in range(st.line - 1, min(st.line + 3, len(lines))):   # gap bir necha qatorga cho'zilishi mumkin
                if old in lines[idx]:
                    before = lines[idx]
                    lines[idx] = lines[idx].replace(old, new, 1)
                    changes.append((idx + 1, before.strip(), lines[idx].strip()))
                    break
    return "\n".join(lines), changes


# ---------------------------------------------------------------- o'lik tarmoqlarni kesish

def _skip_ws(s: str, i: int) -> int:
    while i < len(s) and s[i].isspace():
        i += 1
    return i


def _stmt_end(m: str, i: int) -> int:
    """m[i] dan boshlanadigan C gapining oxirini topadi ({...}, if/while/for, oddiy gap;)."""
    i = _skip_ws(m, i)
    if i >= len(m):
        return i
    if m[i] == "{":
        depth = 0
        for j in range(i, len(m)):
            if m[j] == "{":
                depth += 1
            elif m[j] == "}":
                depth -= 1
                if depth == 0:
                    return j + 1
        return len(m)
    kw = re.match(r"(if|while|for|switch)\s*\(", m[i:])
    if kw:
        close = _balanced(m, i + m[i:].index("("))
        end = _stmt_end(m, close + 1)
        if kw.group(1) == "if":
            k = _skip_ws(m, end)
            if m.startswith("else", k) and not (k + 4 < len(m) and (m[k + 4].isalnum() or m[k + 4] == "_")):
                end = _stmt_end(m, k + 4)
        return end
    depth = 0
    for j in range(i, len(m)):
        if m[j] == "(":
            depth += 1
        elif m[j] == ")":
            depth -= 1
        elif m[j] == ";" and depth == 0:
            return j + 1
    return len(m)


def prune_constant_branches(code: str) -> str:
    """if (0) {...} va if (1) {...} else {...} kabi tarmoqlarni soddalashtiradi."""
    for _ in range(50):
        m = _mask_comments_and_strings(code)
        hit = re.search(r"\bif\s*\(\s*([01])\s*\)", m)
        if not hit:
            return code
        then_start = _skip_ws(m, hit.end())
        then_end = _stmt_end(m, then_start)
        k = _skip_ws(m, then_end)
        has_else = m.startswith("else", k) and not (k + 4 < len(m) and (m[k + 4].isalnum() or m[k + 4] == "_"))
        else_start = _skip_ws(m, k + 4) if has_else else None
        else_end = _stmt_end(m, else_start) if has_else else None
        if hit.group(1) == "0":
            repl = code[else_start:else_end] if has_else else ""
        else:
            repl = code[then_start:then_end]
        code = code[:hit.start()] + repl + code[(else_end if has_else else then_end):]
    return code


def remove_dead_variables(code: str, dead: list[str]) -> str:
    """Keraksiz o'zgaruvchilarning e'loni va ularga qiymat beruvchi gaplarni olib tashlaydi."""
    for var in dead:
        assign = rf"\b{re.escape(var)}\s*(?:=|\+=|-=|\*=|\^=|\|=|&=|<<=|>>=)(?!=)[^;]*;"
        code = re.sub(assign, ";", code)
        code = re.sub(rf"^[ \t]*[A-Za-z_][\w \t\*]*\b{re.escape(var)}\s*;[ \t]*(//[^\n]*)?\n", "", code, flags=re.M)
    # "if (shart) ;" — bo'sh gapli shartni olib tashlaymiz (shartda funksiya chaqiruvi bo'lmasa)
    for _ in range(50):
        m = _mask_comments_and_strings(code)
        found = False
        for hit in re.finditer(r"\bif\s*\(", m):
            close = _balanced(m, hit.end() - 1)
            nxt = _skip_ws(m, close + 1)
            cond = m[hit.end():close]
            if nxt < len(m) and m[nxt] == ";" and not re.search(r"\w\s*\(|\+\+|--|[^=!<>]=[^=]", cond):
                code = code[:hit.start()] + code[nxt + 1:]
                found = True
                break
        if not found:
            break
    # yolg'iz qolgan ";" qatorlarini tozalaymiz
    return re.sub(r"^[ \t]*;[ \t]*\n", "", code, flags=re.M)


def _static_preamble(preamble: str) -> str:
    """Kirish matnidagi e'lonlarni nomzod kodga ko'chiradi (izohlarsiz; massivlar static qilinadi)."""
    masked = _mask_comments_and_strings(preamble)
    lines = [ln.rstrip() for ln in masked.splitlines() if ln.strip()]
    out = []
    for ln in lines:
        if re.search(r"\w+\s*\[[^\]]*\]\s*=", ln) and not ln.lstrip().startswith("static"):
            ln = "static " + ln.lstrip()
        out.append(ln)
    return "\n".join(out)


def run_offline(func: FunctionInfo, analysis: AnalysisResult, preamble: str = "",
                aggressive: bool = True) -> DeobfResult:
    code, changes = simplify_code(func)
    if aggressive:
        code = prune_constant_branches(code)
        code = remove_dead_variables(code, [f.snippet for f in analysis.findings if f.technique == "dead_code"])
    pre = _static_preamble(preamble)
    if pre:
        code = pre + "\n\n" + code

    header = ["/*", " * deobf-agent: offline (statik) tahlil natijasi — LLM ishlatilmadi."]
    for name, text in analysis.decoded_strings.items():
        header.append(f" *  - kodlangan satr {name} = \"{text}\"")
    for sm in analysis.state_machines:
        header.append(" *  - flattening holatlar xaritasi:")
        header += [f" *      {ln.strip()}" for ln in sm.describe_uz().splitlines()]
    dead = [f.snippet for f in analysis.findings if f.technique == "dead_code"]
    if dead:
        header.append(f" *  - keraksiz o'zgaruvchilar (natijaga ta'sir qilmaydi): {', '.join(dead)}")
    header.append(" */")
    code = "\n".join(header) + "\n" + code

    func_lines = func.text.splitlines()
    blocks = []
    for f in analysis.findings:
        line_text = func_lines[f.line - 1].strip() if 0 < f.line <= len(func_lines) else f.snippet
        simplified = next((new for ln, _, new in changes if ln == f.line), f.suggestion or "")
        blocks.append(Block(
            title=TECH_NAMES_UZ.get(f.technique, f.technique),
            original_lines=str(f.line),
            original_code=line_text,
            simplified_code=simplified,
            explanation=f.message,
        ))
    for ln, old, new in changes:
        if not any(b.original_lines == str(ln) for b in blocks):
            blocks.append(Block(title="Soddalashtirish", original_lines=str(ln), original_code=old,
                                simplified_code=new, explanation="Isbotlangan soddalashtirish qo'llandi."))
    blocks.sort(key=lambda b: int(re.match(r"\d+", b.original_lines).group()))

    techniques = [t for t in analysis.techniques() if t != "known_constants"]
    known = [f.message for f in analysis.findings if f.technique == "known_constants"]
    summary = (f"Statik tahlil {len(analysis.findings)} ta belgi topdi"
               + (f": {', '.join(TECH_NAMES_UZ.get(t, t) for t in techniques)}." if techniques else
                  "; obfuskatsiya belgilari topilmadi.")
               + (f" {len(changes)} ta ifoda isbotlangan holda soddalashtirildi." if changes else "")
               + ("".join(f" {k}." for k in known) if known else "")
               + " To'liq tushuntirish va boshqaruv oqimini tiklash uchun LLM rejimidan foydalaning.")
    return DeobfResult(
        function_name=func.name,
        suggested_name=func.name,
        summary=summary,
        techniques=techniques,
        c_code=code,
        blocks=blocks,
        renames=[],
        confidence="medium" if changes or techniques else "low",
        notes="Offline rejim: faqat matematik isbotlangan o'zgarishlar qo'llandi; nomlar o'zgartirilmadi.",
    )
