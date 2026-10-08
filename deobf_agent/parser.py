"""Psevdokod parseri: matnni funksiyalarga ajratadi va uslubini aniqlaydi.

Nima uchun to'liq C parser (masalan, pycparser) ishlatmadik: dekompilyator chiqargan
psevdokod standart C emas (`__fastcall`, `LODWORD(x) = ...`, `int a1@<eax>` va h.k.),
shuning uchun qat'iy parserlar unda xato beradi. Biz soddaroq, lekin "chidamli"
yondashuvni tanladik: figurali qavslarni ({ }) sanab, funksiya chegaralarini topamiz.
Izohlar va satr literallari ichidagi qavslar hisobga olinmaydi.
"""

from __future__ import annotations

import re

from .models import FunctionInfo, Param, ParsedInput

# Funksiya chaqiruvi emas, balki C kalit so'zlari yoki makroslar.
_NOT_CALLS = {
    "if", "for", "while", "switch", "return", "sizeof", "do", "else", "case",
    "LOBYTE", "LOWORD", "LODWORD", "HIBYTE", "HIWORD", "HIDWORD", "BYTE1", "BYTE2", "BYTE3",
    "BYTEn", "SLOBYTE", "SLODWORD", "SHIDWORD", "__PAIR64__",
    "__ROL1__", "__ROR1__", "__ROL2__", "__ROR2__", "__ROL4__", "__ROR4__", "__ROL8__", "__ROR8__",
    "CONCAT11", "CONCAT22", "CONCAT44", "SUB41", "SUB42", "SUB81", "SUB84",
    "ZEXT14", "ZEXT24", "ZEXT48", "SEXT14", "SEXT24", "SEXT48",
}

# Signaturadan olib tashlanadigan so'zlar (chaqiruv kelishuvlari va sifatlovchilar).
_SIG_NOISE = r"\b(__fastcall|__cdecl|__stdcall|__thiscall|__usercall|__userpurge|__noreturn|static|inline|extern|__hidden)\b"

_STYLE_PATTERNS = {
    "ida": [r"\bsub_[0-9A-Fa-f]+\b", r"\b_DWORD\b", r"\b_QWORD\b", r"\b_BYTE\b", r"__fastcall",
            r"\bLODWORD\(", r"\bHIDWORD\(", r"//\s*\[[re][sb]p[+-]", r"\bLABEL_\d+\b", r"\b__int64\b",
            r"//\s*(?:eax|ecx|edx|rax|rcx|rdx|rdi|rsi|r8|r9)\b"],
    "ghidra": [r"\bFUN_[0-9a-fA-F]+\b", r"\bundefined[1248]?\b", r"\blocal_[0-9a-fA-F]+\b",
               r"\bparam_\d+\b", r"\b[iu]Var\d+\b", r"\bDAT_[0-9a-fA-F]+\b", r"\bLAB_[0-9a-fA-F]+\b",
               r"\bCONCAT\d\d\(", r"/\*\s*WARNING:"],
    "angr": [r"//\s*\[bp-0x[0-9a-f]+\]"],
}


def detect_style(text: str) -> str:
    """Matn qaysi dekompilyatordan olinganini taxmin qiladi (ball tizimi)."""
    scores = {style: sum(len(re.findall(p, text)) for p in pats) for style, pats in _STYLE_PATTERNS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "c"


def _mask_comments_and_strings(text: str) -> str:
    """Izohlar va satrlarni bo'sh joy bilan almashtiradi (uzunlik va qatorlar saqlanadi).

    Bu qavslarni sanashda izoh yoki satr ichidagi '{' '}' belgilar xalaqit bermasligi uchun.
    """
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            j = text.find("\n", i)
            j = n if j == -1 else j
            for k in range(i, j):
                out[k] = " "
            i = j
        elif c == "/" and nxt == "*":
            j = text.find("*/", i + 2)
            j = n if j == -1 else j + 2
            for k in range(i, j):
                if out[k] != "\n":
                    out[k] = " "
            i = j
        elif c in "\"'":
            j = i + 1
            while j < n and text[j] != c and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            for k in range(i + 1, min(j, n)):
                out[k] = " "
            i = j + 1
        else:
            i += 1
    return "".join(out)


def _split_top_level(s: str, sep: str = ",") -> list[str]:
    parts, depth, cur = [], 0, []
    for ch in s:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p.strip() for p in parts if p.strip()]


def normalize_type(t: str) -> str:
    """'char*', 'char  *', 'char * *' -> 'char *', 'char **' (yagona ko'rinish)."""
    t = re.sub(r"\s+", " ", t).strip()
    while re.search(r"\*\s+\*", t):
        t = re.sub(r"\*\s+\*", "**", t)
    return re.sub(r"\s*(\*+)\s*", lambda m: " " + m.group(1), t).strip()


def parse_params(param_str: str) -> list[Param]:
    """'unsigned int a1, char *a2' -> [Param('unsigned int','a1'), Param('char *','a2')]"""
    param_str = re.sub(r"@<\w+>", "", param_str)          # IDA: int a1@<eax>
    if param_str.strip() in ("", "void"):
        return []
    params = []
    for i, p in enumerate(_split_top_level(param_str)):
        if p == "...":
            params.append(Param("...", "..."))
            continue
        fp = re.match(r"(.*\(\s*\*\s*)(\w+)(\s*\).*)", p)   # funksiya ko'rsatkichi: int (*cb)(int)
        if fp:
            params.append(Param((fp.group(1) + fp.group(3)).strip(), fp.group(2)))
            continue
        m = re.match(r"(.*?[\s\*])(\w+)\s*((?:\[[^\]]*\])*)$", p)
        if m and m.group(1).strip():
            ptype = m.group(1).strip() + (" *" if m.group(3) else "")
            params.append(Param(normalize_type(ptype), m.group(2)))
        else:                                              # faqat tur berilgan: "int"
            params.append(Param(p, f"arg{i}"))
    return params


def _parse_signature(sig: str):
    sig_clean = re.sub(_SIG_NOISE, " ", sig)
    sig_clean = re.sub(r"\s+", " ", sig_clean).strip()
    m = re.match(r"^(.*?)\b([A-Za-z_]\w*)\s*\((.*)\)\s*$", sig_clean, flags=re.S)
    if not m:
        return None
    ret_type, name, params = m.group(1).strip(), m.group(2), m.group(3)
    if not ret_type or name in ("if", "while", "for", "switch", "return"):
        return None
    if "=" in ret_type or ret_type.endswith(("struct", "union", "enum")):
        return None
    ret_type = normalize_type(ret_type)
    return name, ret_type, parse_params(params)


def _find_calls(body_masked: str, own_name: str) -> list[str]:
    seen = []
    for m in re.finditer(r"\b([A-Za-z_]\w*)\s*\(", body_masked):
        name = m.group(1)
        # "(unsigned int)(x)" kabi tur o'zgartirishlarni chaqiruv deb hisoblamaymiz
        if name in _NOT_CALLS or name == own_name or name in ("int", "char", "long", "short", "unsigned"):
            continue
        if name not in seen:
            seen.append(name)
    return seen


def parse_data_blobs(text: str) -> dict[str, bytes]:
    """Global ma'lumotlarni topadi.

    Qo'llab-quvvatlanadigan ikki format:
      1) scripts/decompile_angr.py yaratadigan izoh:
         // ENC @ 0x402010 (27 bayt): 14 39 30 ...
      2) IDA "Shift+E -> C array" eksporti yoki oddiy C massiv:
         unsigned char byte_4020[27] = { 0x14, 0x39, ... };
    """
    blobs: dict[str, bytes] = {}
    for m in re.finditer(r"//\s*(\w+)\s*@\s*0x[0-9A-Fa-f]+\s*\(\d+\s*bayt\):\s*([0-9A-Fa-f ]+)", text):
        blobs[m.group(1)] = bytes(int(h, 16) for h in m.group(2).split())
    arr_re = (r"\b(?:unsigned\s+char|char|_BYTE|uint8_t|uchar|byte|undefined1?)\s+(\w+)\s*\[\s*\w*\s*\]"
              r"\s*=\s*\{([^}]*)\}\s*;")
    for m in re.finditer(arr_re, text):
        values = []
        for item in m.group(2).split(","):
            item = item.strip().rstrip("uU")
            if not item:
                continue
            try:
                values.append(int(item, 0) & 0xFF)
            except ValueError:
                break
        else:
            blobs[m.group(1)] = bytes(values)
    return blobs


def parse(text: str) -> ParsedInput:
    """Asosiy funksiya: psevdokod matnini tahlil qiladi."""
    text = text.replace("\r\n", "\n")
    masked = _mask_comments_and_strings(text)
    functions: list[FunctionInfo] = []
    i, n = 0, len(masked)
    last_boundary = 0     # oxirgi ';' yoki '}' (yuqori darajadagi) dan keyingi pozitsiya
    while i < n:
        ch = masked[i]
        if ch == ";":
            last_boundary = i + 1
        elif ch == "{":
            # mos keluvchi yopuvchi '}' ni topamiz
            depth, j = 0, i
            while j < n:
                if masked[j] == "{":
                    depth += 1
                elif masked[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            sig_raw = masked[last_boundary:i]
            # preprotsessor qatorlarini (#include ...) signaturadan chiqarib tashlaymiz
            sig_lines = [ln for ln in sig_raw.split("\n") if not ln.strip().startswith("#")]
            sig = " ".join(ln.strip() for ln in sig_lines).strip()
            parsed = _parse_signature(sig) if sig.endswith(")") else None
            if parsed:
                name, ret_type, params = parsed
                sig_start = last_boundary + (len(sig_raw) - len(sig_raw.lstrip()))
                start_line = text.count("\n", 0, sig_start) + 1
                end_line = text.count("\n", 0, j) + 1
                functions.append(FunctionInfo(
                    name=name,
                    ret_type=ret_type,
                    params=params,
                    signature=re.sub(r"\s+", " ", text[sig_start:i]).strip(),
                    body=text[i:j + 1],
                    text=text[sig_start:j + 1],
                    start_line=start_line,
                    end_line=end_line,
                    calls=_find_calls(masked[i:j + 1], name),
                ))
            i = j + 1
            last_boundary = i
            continue
        i += 1
    return ParsedInput(style=detect_style(text), functions=functions,
                       data_blobs=parse_data_blobs(text), raw=text)
