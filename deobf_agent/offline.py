"""Offline (bepul) rejim: LLM'siz, faqat statik tahlil asosida natija.

Nima qiladi:
  * tasodifiy test bilan tasdiqlangan soddalashtirishlarni kodga qo'llaydi: MBA ifodalar ->
    oddiy ifoda, yashirin konstantalar -> son, soxta shartlar -> 0/1;
  * oddiy flattening'ni yechadi (unflatten.py), o'lik tarmoqlar va keraksiz o'zgaruvchilarni olib tashlaydi;
  * qolgan topilmalarni (holatlar xaritasi, dekodlangan satrlar) kod boshida izoh sifatida beradi;
  * natijani LLM qaytaradigan tuzilmada (DeobfResult) qaytaradi.

Murakkab holatlar va mazmunli nomlar berish — LLM rejimining vazifasi.
"""

from __future__ import annotations

import re

from . import expr as E
from . import parser as P
from .detectors import AnalysisResult, _expressions, _split_stmt, detect_dead_variables, is_declaration, \
    is_logic, looks_like_mba, simplify_mba, var_types
from .explain import TECH_NAMES_UZ, simple_explanation, simple_summary
from .models import FunctionInfo
from .schema import Block, DeobfResult
from .unflatten import unflatten


def _rewrite(node, types: E.Types, is_condition: bool = False):
    """Ifoda daraxtini soddalashtiradi (faqat tasodifiy test bilan tasdiqlangan o'zgarishlar)."""
    if node[0] in ("num", "var"):
        return node
    if not E.variables(node) and any(n[0] == "bin" for n in E.subnodes(node)):
        try:                                  # faqat haqiqiy hisob yig'iladi (-5 kabi literal emas)
            v, bits, signed = E.evaluate(node, {})
            return ("num", v & ((1 << bits) - 1), bits, signed)
        except E.ExprError:
            return node
    if is_condition and E.variables(node):
        const = E.is_constant(node, 3000, types)
        if const is not None:
            return ("num", int(bool(const)), 32, True)
    if not is_logic(node) and looks_like_mba(node):
        simple = simplify_mba(node, types)
        if simple:
            return E.parse(simple)
    # bolalarini rekursiv soddalashtiramiz
    if node[0] == "un":
        return ("un", node[1], _rewrite(node[2], types, is_condition and node[1] == "!"))
    if node[0] == "bin":
        sub_cond = is_condition and node[1] in ("&&", "||")
        return ("bin", node[1], _rewrite(node[2], types, sub_cond), _rewrite(node[3], types, sub_cond))
    if node[0] == "cast":
        return ("cast", node[1], node[2], _rewrite(node[3], types))
    if node[0] == "cond":
        return ("cond", _rewrite(node[1], types, True), _rewrite(node[2], types), _rewrite(node[3], types))
    return node


def _simplify_text(text: str, is_condition: bool, types: E.Types) -> str | None:
    try:
        node = E.parse(text)
    except E.ExprError:
        return None
    new = _rewrite(node, types, is_condition)
    return None if new == node else E.to_c(new)


def simplify_code(func: FunctionInfo) -> tuple[str, list[tuple[int, str, str]]]:
    """Funksiya matniga soddalashtirishlarni qo'llaydi. Natija: (yangi_kod, [(qator, eski, yangi)])."""
    lines = func.text.splitlines()
    changes: list[tuple[int, str, str]] = []
    types = var_types(func)
    for line, old, kind in _expressions(func):
        new = _simplify_text(old, kind == "cond", types)
        if not new:
            continue
        for idx in range(line - 1, min(line + 3, len(lines))):   # gap bir necha qatorga cho'zilishi mumkin
            if old in lines[idx]:
                before = lines[idx]
                lines[idx] = lines[idx].replace(old, new, 1)
                changes.append((idx + 1, before.strip(), lines[idx].strip()))
                break
    return "\n".join(lines), changes


# ---------------------------------------------------------------- o'lik tarmoqlarni kesish

_ELSE_RE = re.compile(r"else\b")


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
        j = P.find_close(m, i)
        return len(m) if j < 0 else j + 1
    kw = re.match(r"(if|while|for|switch)\s*\(", m[i:])
    if kw:
        close = P.find_close(m, i + m[i:].index("("), "()")
        end = _stmt_end(m, len(m) if close < 0 else close + 1)
        if kw.group(1) == "if":
            k = _skip_ws(m, end)
            if _ELSE_RE.match(m, k):
                end = _stmt_end(m, k + 4)
        return end
    depth = 0
    for j in range(i, len(m)):
        depth += (m[j] == "(") - (m[j] == ")")
        if m[j] == ";" and depth == 0:
            return j + 1
    return len(m)


def prune_constant_branches(code: str) -> str:
    """if (0) {...} va if (1) {...} else {...} kabi tarmoqlarni soddalashtiradi."""
    for _ in range(50):
        m = P.mask_code(code)
        hit = re.search(r"\bif\s*\(\s*([01])\s*\)", m)
        if not hit:
            return code
        then_start = _skip_ws(m, hit.end())
        then_end = _stmt_end(m, then_start)
        k = _skip_ws(m, then_end)
        if _ELSE_RE.match(m, k):
            else_start = _skip_ws(m, k + 4)
            else_end = _stmt_end(m, else_start)
            keep = code[else_start:else_end] if hit.group(1) == "0" else code[then_start:then_end]
            code = code[:hit.start()] + keep + code[else_end:]
        else:
            keep = "" if hit.group(1) == "0" else code[then_start:then_end]
            code = code[:hit.start()] + keep + code[then_end:]
    return code


def remove_dead_variables(code: str, dead: list[str]) -> str:
    """Keraksiz o'zgaruvchilarning e'loni va ularga qiymat beruvchi gaplarni olib tashlaydi."""
    for var in dead:
        v = re.escape(var)
        # 1) yagona e'lon: "unsigned int junk;" yoki "unsigned int junk = 0u;" — butun qatorni o'chiramiz
        code = re.sub(rf"^[ \t]*(?:[A-Za-z_]\w*[ \t]+)+\**[ \t]*{v}[ \t]*(?:=[^;,]*)?;[ \t]*(//[^\n]*)?\n",
                      "", code, flags=re.M)
        # 2) ko'p o'zgaruvchili e'lon: "int h = 0, junk = 0;" -> "int h = 0;"
        code = re.sub(rf",\s*\**{v}\s*(?:=\s*[^,;]+)?(?=\s*[,;])", "", code)
        code = re.sub(rf"(?<=[\s\*]){v}\s*(?:=\s*[^,;]+)?\s*,\s*(?=[A-Za-z_*])", "", code)
        # 3) oddiy qiymat berishlar: "junk = k * 7;" / "junk ^= h;" -> ";" (keyin tozalanadi)
        code = re.sub(rf"\b{v}\s*(?:=|\+=|-=|\*=|\^=|\|=|&=|<<=|>>=)(?!=)[^;]*;", ";", code)
    # "if (shart) ;" — bo'sh gapli shartni olib tashlaymiz (shartda funksiya chaqiruvi bo'lmasa)
    changed = True
    while changed:
        changed = False
        m = P.mask_code(code)
        for hit in re.finditer(r"\bif\s*\(", m):
            close = P.find_close(m, hit.end() - 1, "()")
            if close < 0:
                break
            nxt = _skip_ws(m, close + 1)
            cond = m[hit.end():close]
            if nxt < len(m) and m[nxt] == ";" and not re.search(r"\w\s*\(|\+\+|--|[^=!<>]=[^=]", cond):
                code = code[:hit.start()] + code[nxt + 1:]
                changed = True
                break
    # yolg'iz qolgan ";" qatorlarini tozalaymiz
    return re.sub(r"^[ \t]*;[ \t]*(?:/\*.*?\*/|//[^\n]*)?[ \t]*\n", "", code, flags=re.M)


def _static_preamble(preamble: str) -> str:
    """Kirish matnidagi e'lonlarni nomzod kodga ko'chiradi (izohlarsiz; massivlar static qilinadi)."""
    out = []
    for ln in P.mask_code(preamble).splitlines():
        if not ln.strip():
            continue
        if re.search(r"\w+\s*\[[^\]]*\]\s*=", ln) and not ln.lstrip().startswith("static"):
            ln = "static " + ln.lstrip()
        out.append(ln.rstrip())
    return "\n".join(out)


def _unused_locals(code: str) -> list[str]:
    """E'lon qilingan, lekin boshqa hech qayerda uchramaydigan lokal o'zgaruvchilar."""
    masked = P.mask_code(code)
    names = []
    for m in re.finditer(r"^[ \t]*((?:[A-Za-z_]\w*[ \t]+)+\**[ \t]*[A-Za-z_]\w*[^;{}()]*);", masked, flags=re.M):
        text = m.group(1).strip()
        if not is_declaration(text):
            continue
        for name, _, _ in _split_stmt(text):
            if len(re.findall(rf"\b{re.escape(name)}\b", masked)) == 1:
                names.append(name)
    return names


def run_offline(func: FunctionInfo, analysis: AnalysisResult, preamble: str = "",
                level: int = 2) -> DeobfResult:
    """level: 2 — flattening'ni yechish + tarmoqlarni kesish + o'lik kod; 1 — flattening'siz; 0 — faqat ifodalar."""
    work, unflattened = func, False
    if level >= 2 and analysis.state_machines:
        new_text = unflatten(func.text)
        reparsed = P.parse(new_text).get(func.name) if new_text else None
        if reparsed is not None:
            work, unflattened = reparsed, True
    code, changes = simplify_code(work)
    dead = [f.snippet for f in analysis.findings if f.technique == "dead_code"]
    if level >= 1:
        code = remove_dead_variables(prune_constant_branches(code), dead)
        reparsed = P.parse(code).get(func.name)
        if reparsed is not None:     # yangi paydo bo'lgan keraksiz o'zgaruvchilar (masalan, eski state)
            extra = [f.snippet for f in detect_dead_variables(reparsed)] + _unused_locals(code)
            if extra:
                code = remove_dead_variables(code, extra)
        code = re.sub(r"\n[ \t]*\n([ \t]*\n)+", "\n\n", code)          # ortiqcha bo'sh qatorlar
    pre = _static_preamble(preamble)
    if pre:
        code = pre + "\n\n" + code

    header = ["/*", " * deobf-agent: offline (statik) tahlil natijasi — LLM ishlatilmadi."]
    header += [f" *  - kodlangan satr {name} = \"{text}\"" for name, text in analysis.decoded_strings.items()]
    for sm in analysis.state_machines:
        header.append(" *  - flattening holatlar xaritasi:")
        header += [f" *      {ln.strip()}" for ln in sm.describe_uz().splitlines()]
    if dead:
        header.append(f" *  - keraksiz o'zgaruvchilar (natijaga ta'sir qilmaydi): {', '.join(dead)}")
    code = "\n".join(header + [" */"]) + "\n" + code

    func_lines = func.text.splitlines()
    blocks = []
    for f in analysis.findings:
        line_text = func_lines[f.line - 1].strip() if 0 < f.line <= len(func_lines) else f.snippet
        simplified = next((new for ln, _, new in changes if ln == f.line), f.suggestion or "")
        blocks.append(Block(title=TECH_NAMES_UZ.get(f.technique, f.technique), original_lines=str(f.line),
                            original_code=line_text, simplified_code=simplified, explanation=f.message,
                            simple=simple_explanation(f.technique)))
    for ln, old, new in changes:
        if not any(b.original_lines == str(ln) for b in blocks):
            blocks.append(Block(title="Soddalashtirish", original_lines=str(ln), original_code=old,
                                simplified_code=new, explanation="Test bilan tasdiqlangan soddalashtirish qo'llandi.",
                                simple=simple_explanation("simplify")))
    if unflattened:
        sm = analysis.state_machines[0]
        blocks.append(Block(
            title="Boshqaruv oqimi tiklandi (unflattening)",
            original_lines=str(next((f.line for f in analysis.findings if f.technique == "control_flow_flattening"), 1)),
            original_code=f"while (1) {{ switch ({sm.state_var}) {{ ... {len(sm.transitions)} ta holat ... }} }}",
            simplified_code="\n".join(ln for ln in code.splitlines() if re.search(r"\b(while|if|for)\b", ln))[:400],
            explanation=(f"Holatlar mashinasi ({sm.state_var} o'zgaruvchisi, {len(sm.transitions)} ta holat) graf sifatida "
                         "tahlil qilindi: holatga qaytuvchi tarmoq — tsikl (while), qolganlari — if/else. "
                         "Natijada dispetcher (while(1)+switch) va holat o'zgaruvchisi olib tashlandi."),
            simple=simple_explanation("unflatten"),
        ))
    blocks.sort(key=lambda b: int(re.match(r"\d+", b.original_lines).group()))

    techniques = [t for t in analysis.techniques() if t != "known_constants"]
    known = [f.message for f in analysis.findings if f.technique == "known_constants"]
    summary = (f"Statik tahlil {len(analysis.findings)} ta belgi topdi"
               + (f": {', '.join(TECH_NAMES_UZ.get(t, t) for t in techniques)}." if techniques else
                  "; obfuskatsiya belgilari topilmadi.")
               + (f" {len(changes)} ta ifoda soddalashtirildi (har biri tasodifiy test bilan tekshirilgan)." if changes else "")
               + (" Flattening yechildi: boshqaruv oqimi tuzilmali ko'rinishga (while/if) qaytarildi." if unflattened else "")
               + "".join(f" {k}." for k in known)
               + ("" if unflattened or not analysis.state_machines else
                  " Boshqaruv oqimini to'liq tiklash uchun LLM rejimidan foydalaning."))
    return DeobfResult(
        function_name=func.name,
        suggested_name=func.name,
        summary=summary,
        simple_summary=simple_summary(techniques, unflattened, bool(changes)),
        techniques=techniques,
        c_code=code,
        blocks=blocks,
        renames=[],
        confidence="medium" if changes or techniques else "low",
        notes="Offline rejim: faqat tasodifiy testlar bilan tekshirilgan o'zgarishlar qo'llandi; nomlar o'zgartirilmadi.",
    )
