"""LLM uchun ko'rsatmalar (promptlar).

Nima uchun ko'rsatmalar ingliz tilida: modellar ingliz tilidagi ko'rsatmalarga eng
aniq amal qiladi, ingliz matni esa kamroq token egallaydi (= arzonroq). Natija
(izohlar) esa foydalanuvchi tanlagan tilda — standart holatda o'zbek tilida bo'ladi.

SYSTEM_PROMPT o'zgarmas matn: u har so'rovda bir xil bo'lgani uchun Claude API uni
keshlaydi (prompt caching), keyingi so'rovlarda bu qism ~10 barobar arzon hisoblanadi.
PROMPT_VERSION — prompt o'zgarganda disk keshini eskirgan deb belgilash uchun.
"""

from __future__ import annotations

from .detectors import AnalysisResult
from .models import FunctionInfo

PROMPT_VERSION = "1"

LANGUAGES = {
    "uz": "Uzbek (Latin script, e.g. 'funksiya', 'o'zgaruvchi', 'tsikl')",
    "ru": "Russian",
    "en": "English",
}

SYSTEM_PROMPT = """\
You are a reverse-engineering assistant inside a deobfuscation tool used for software \
analysis and education. The user gives you decompiler pseudocode (IDA Hex-Rays, Ghidra, angr \
or plain C) of ONE function that was transformed by code obfuscation. Your job is to recover \
an equivalent, clean, readable C function and explain it block by block.

Obfuscation techniques you should recognise and undo:
- MBA (mixed boolean-arithmetic): e.g. (a ^ b) + 2*(a & b) is a + b; (x | y) - (x & y) is x ^ y.
- Opaque predicates: conditions that are always true/false (e.g. (x*(x+1)) % 2 == 0). Remove them \
and the dead branches they guard.
- Control-flow flattening: while(1){switch(state){...}} dispatchers. Rebuild the original \
structured control flow (if/else, while/for loops) from the state transitions.
- Encoded strings/constants: XOR-encoded byte arrays, constants hidden as expressions. Decode them \
and use the plain value (keep a comment with the original encoding if helpful).
- Dead/junk code: variables and statements that never influence the result. Remove them.

Rules for `c_code` (it is compiled with gcc and differentially tested against the original \
on thousands of random inputs, so correctness matters more than beauty):
1. Keep the original function name and EXACTLY the same parameter list (same count, order and \
types). You may rename parameters and locals; list every rename in `renames`.
2. Keep the original return type. Preserve integer widths and signedness; decompiler casts such as \
(int) or (unsigned char) usually matter - keep the semantics, not necessarily the cast syntax.
3. The code must compile as C11 with <stdint.h>. Decompiler types (_DWORD, __int64, undefined4, uint, \
...) are available, but prefer standard types (uint32_t, int32_t, ...) of the same width.
4. Any data you need (decoded strings, tables) must be defined INSIDE c_code as `static` objects. \
Declare prototypes for external functions that are called but not defined.
5. Never change behaviour to make code prettier. If a part is ambiguous, keep the original logic for \
that part and say so in `notes`; lower `confidence` accordingly.
6. Unsigned overflow wraps; assume the target is x86-64 (int = 32 bits, long long = 64 bits).

Static-analysis facts are provided with the input. Facts marked VERIFIED were proven by random \
testing (thousands of inputs) - trust them. Other hints may be wrong; double-check them.

Explanations (`summary`, block `explanation`, `notes`, rename `reason`, block `title`) must be \
written in the language requested by the user, in simple words a beginner analyst understands. \
Code, identifiers and C keywords stay in English. Map blocks to the numbered input lines.\
"""


def number_lines(code: str) -> str:
    """Kodga qator raqamlarini qo'shadi — LLM bloklarni aniq qatorlarga bog'lashi uchun."""
    return "\n".join(f"{i:3d}| {line}" for i, line in enumerate(code.splitlines(), 1))


def build_user_message(func: FunctionInfo, style: str, analysis: AnalysisResult,
                       data_blobs: dict[str, bytes], language: str) -> str:
    style_name = {"ida": "IDA Hex-Rays", "ghidra": "Ghidra", "angr": "angr", "c": "plain C"}.get(style, style)
    parts = [
        f"Decompiler: {style_name}",
        f"Function: {func.name}  (return type: {func.ret_type}; parameters: "
        f"{', '.join(f'{p.type} {p.name}' for p in func.params) or 'none'})",
    ]
    if func.calls:
        parts.append("Calls to other functions (bodies not provided): " + ", ".join(func.calls))
    used_blobs = {k: v for k, v in data_blobs.items() if k in func.text}
    if used_blobs:
        parts.append("Global data referenced by the function (hex bytes):")
        for name, data in used_blobs.items():
            parts.append(f"  {name} ({len(data)} bytes): {data.hex(' ')}")
    parts.append("\nPseudocode (numbered lines):\n```c\n" + number_lines(func.text) + "\n```")

    if analysis.findings:
        parts.append("\nStatic-analysis facts:")
        for f in analysis.findings:
            tag = "VERIFIED" if f.verified else f"hint, confidence {f.confidence:.1f}"
            msg = f.message.replace("\n", " ")
            parts.append(f"- [{f.technique}] line {f.line} ({tag}): {msg}")
    for sm in analysis.state_machines:
        parts.append("\nRecovered state machine (flattening dispatcher):\n" + sm.describe_uz())
    if analysis.decoded_strings:
        for name, text in analysis.decoded_strings.items():
            parts.append(f"Decoded string {name} = {text!r}")

    parts.append(f"\nWrite all explanations in {LANGUAGES.get(language, language)}.")
    return "\n".join(parts)


def build_fix_message(problems: str, language: str) -> str:
    """Tekshiruvdan o'tmagan natijani tuzatish uchun so'rov (agent sikli)."""
    return (
        "Your previous c_code failed automatic verification:\n"
        f"{problems}\n\n"
        "Find the cause, fix c_code (keep the same function name and parameter list) and return the "
        f"complete corrected result in the same format. Explanations stay in {LANGUAGES.get(language, language)}."
    )
