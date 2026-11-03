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

from . import blocks as blocks_mod
from . import narrate
from . import expr as E
from . import parser as P
from .detectors import AnalysisResult, _expressions, _split_stmt, _statements, detect_dead_variables, is_declaration, \
    is_logic, looks_like_mba, simplify_mba, var_types
from .models import FunctionInfo
from .schema import DeobfResult
from .unflatten import unflatten


def _result_type(node, types: E.Types) -> tuple[int, bool] | None:
    """Ifoda natijasining turi (razryad, ishora): barcha sinovlarda bir xil bo'lsa; bo'lmasa None."""
    seen = None
    for env, st in E.random_inputs(E.variables(node), 40, seed=3, types=types, consts=E.constants(node)):
        try:
            _, bits, signed = E.evaluate(node, env, st)
        except E.ExprError:
            continue
        if seen is None:
            seen = (bits, signed)
        elif seen != (bits, signed):
            return None
    return seen


def _keep_type(old, new, types: E.Types):
    """Soddalashtirilgan `new` asl `old` bilan bir xil QIYMAT VA TUR bersin. Tur farq qilsa (masalan `(unsigned short)(c - ...)`
    o'rniga `c`) — asl turga keltiruvchi cast qo'shamiz; baribir mos kelmasa — o'zgartirmaymiz (None)."""
    if E.equivalent(old, new, 1500, types):
        return new
    t = _result_type(old, types)
    if t:
        wrapped = ("cast", t[0], t[1], new)
        if E.equivalent(old, wrapped, 1500, types):
            return wrapped
    return None


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
            return _keep_type(node, E.parse(simple), types) or node
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
            head = code[:hit.start()]
            if not keep:
                head = re.sub(r"\belse\s*$", "", head)       # `else if (0) {...}` butunlay o'chadi: yolg'iz `else` qolmasin
            code = head + keep + code[then_end:]
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
    code = re.sub(r"\belse\s*;", "", code)                 # `else v = ...;` o'chsa, yolg'iz `else` keyingi gapni yutmasin
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
            if nxt < len(m) and m[nxt] == ";" and not re.search(r"\w\s*\(|\+\+|--|[^=!<>]=[^=]", cond) \
                    and not _ELSE_RE.match(m, _skip_ws(m, nxt + 1)):       # `if (c) ; else S` — else yo'qolmasin
                code = code[:hit.start()] + code[nxt + 1:]
                changed = True
                break
    # yolg'iz qolgan ";" qatorlarini tozalaymiz
    return re.sub(r"^[ \t]*;[ \t]*(?:/\*.*?\*/|//[^\n]*)?[ \t]*\n", "", code, flags=re.M)


def _static_preamble(preamble: str) -> str:
    """Kirish matnidagi e'lonlarni nomzod kodga ko'chiradi (izohlarsiz; massivlar static qilinadi)."""
    out = []
    for ln in preamble.splitlines():              # aslidek (mask_code qatorlardagi matnni bo'sh joyga aylantirib yuborar edi)
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


def remove_dead_stores(code: str, func_name: str) -> str:
    """`x = 0;` kabi qiymat berish, agar x keyingi o'qishdan OLDIN qayta yozilsa (yoki umuman o'qilmasa) — keraksiz.

    Faqat funksiya ichida e'lon qilingan lokal o'zgaruvchilar, faqat yon ta'siri yo'q o'ng tomonlar va faqat
    funksiya tanasining eng yuqori darajasidagi gaplar ko'rib chiqiladi. Ehtiyotkorlik: x keyingi gaplarning
    birortasida (ichma-ich tsikl/shart ichida bo'lsa ham) tilga olinsa va u shunchaki "x = ..." qayta yozish bo'lmasa — qoldiriladi.
    """
    f = P.parse(code).get(func_name)
    if f is None:
        return code
    declared = {n for st in _statements(f) if is_declaration(st.text) for n, _, _ in _split_stmt(st.text)}
    local = declared - {p.name for p in f.params}
    nodes = narrate.parse_function(f.text)
    lines = f.text.splitlines(keepends=True)
    drop: list[narrate.Node] = []
    for i, n in enumerate(nodes):
        parts = narrate._split_assign(n.text) if n.kind == "simple" else None
        if not parts or parts[1] or parts[0] not in local:
            continue
        x, _, rhs_text = parts
        rhs = narrate._parse(rhs_text)
        if rhs is None or E.has_side_effects(rhs) or re.search(rf"\b{re.escape(x)}\b", rhs_text):
            continue
        for m in nodes[i + 1:]:
            if not re.search(rf"\b{re.escape(x)}\b", m.src):
                continue
            again = narrate._split_assign(m.text) if m.kind == "simple" else None
            if again and not again[1] and again[0] == x and not re.search(rf"\b{re.escape(x)}\b", again[2]):
                drop.append(n)                       # keyingi gap x ni o'qimay qayta yozadi
            break
        else:
            drop.append(n)                           # x bundan keyin umuman tilga olinmaydi
    for n in drop:
        if n.line == n.end and n.src in lines[n.line - 1]:
            lines[n.line - 1] = lines[n.line - 1].replace(n.src, "", 1)
    new_text = "".join(ln for ln in lines if ln.strip() or ln == "\n" or not ln)
    new_text = re.sub(r"^[ \t]+\n", "", new_text, flags=re.M) if drop else new_text
    return code.replace(f.text, new_text, 1) if drop else code


def run_offline(func: FunctionInfo, analysis: AnalysisResult, preamble: str = "",
                level: int = 2) -> DeobfResult:
    """level: 2 — flattening'ni yechish + tarmoqlarni kesish + o'lik kod; 1 — flattening'siz; 0 — faqat ifodalar;
    -1 — hech narsa o'zgartirilmaydi (oxirgi himoya: tushuntirish bor, lekin kod aslidek qoladi)."""
    work, unflattened = func, False
    if level >= 2 and analysis.state_machines:
        new_text = unflatten(func.text)
        reparsed = P.parse(new_text).get(func.name) if new_text else None
        if reparsed is not None:
            work, unflattened = reparsed, True
    if level >= 0:
        code, changes = simplify_code(work)
    else:
        code, changes = func.text, []
    dead = [f.snippet for f in analysis.findings if f.technique == "dead_code"] if level >= 1 else []
    if level >= 1:
        code = remove_dead_variables(prune_constant_branches(code), dead)
        code = remove_dead_stores(code, func.name)
        reparsed = P.parse(code).get(func.name)
        if reparsed is not None:     # yangi paydo bo'lgan keraksiz o'zgaruvchilar (masalan, eski state)
            extra = [f.snippet for f in detect_dead_variables(reparsed)] + _unused_locals(code)
            if extra:
                code = remove_dead_variables(code, extra)
        code = re.sub(r"\n[ \t]*\n([ \t]*\n)+", "\n\n", code)          # ortiqcha bo'sh qatorlar
    final = P.parse(code).get(func.name)
    final_text = final.text if final is not None else code
    pre = _static_preamble(preamble)
    if pre:
        code = pre + "\n\n" + code

    header = ["/*", " * deobf-agent: offline (statik) tahlil natijasi — LLM ishlatilmadi."]
    if level < 0:
        header.append(" *  - ehtiyotkorlik: xavfsiz soddalashtirish topilmadi, kod aslidek qoldirildi")
    header += [f" *  - kodlangan satr {name} = \"{text}\"" for name, text in analysis.decoded_strings.items()]
    for sm in analysis.state_machines:
        header.append(" *  - flattening holatlar xaritasi:")
        header += [f" *      {ln.strip()}" for ln in sm.describe_uz().splitlines()]
    if dead:
        header.append(f" *  - keraksiz o'zgaruvchilar (natijaga ta'sir qilmaydi): {', '.join(dead)}")
    code = "\n".join(header + [" */"]) + "\n" + code

    blocks = blocks_mod.build(func, analysis, changes, final_text, unflattened)
    summary, simple = blocks_mod.summaries(func, analysis, final_text, changes, unflattened)
    techniques = [t for t in analysis.techniques() if t != "known_constants"]
    return DeobfResult(
        function_name=func.name,
        suggested_name=func.name,
        summary=summary,
        simple_summary=simple,
        techniques=techniques,
        c_code=code,
        blocks=blocks,
        renames=[],
        confidence="medium" if changes or techniques else "low",
        notes="Offline rejim: faqat tasodifiy testlar bilan tekshirilgan o'zgarishlar qo'llandi; nomlar o'zgartirilmadi."
              + (" Xavfsiz soddalashtirish topilmadi, shuning uchun kod o'zgartirilmadi." if level < 0 else ""),
    )
