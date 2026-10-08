"""Differensial test: ikki funksiya bir xil ishlaydimi?

G'oya: asl (obfuskatsiyalangan) funksiya va yangi (soddalashtirilgan) funksiyani BIR XIL
tasodifiy kirishlar bilan minglab marta chaqiramiz va natijalarni solishtiramiz.
Farq chiqmasa — funksiyalar amalda ekvivalent (bu isbot emas, lekin kuchli dalil).

Nimalar solishtiriladi:
  * qaytish qiymati (ko'rsatkich qaytarsa — u qaysi buferning qaysi joyini ko'rsatishi);
  * ko'rsatkichli parametrlar orqali o'zgartirilgan bufer mazmuni;
  * global o'zgaruvchilar (IDA/Ghidra'dagi dword_404010, DAT_00104010 kabi) mazmuni;
  * tashqi funksiyalar chaqiruvlari ketma-ketligi (stublar orqali).

Xotira modeli: har bir ko'rsatkichli parametr uchun 4096 baytlik bufer ajratiladi va u
tasodifiy baytlar, NUL bilan tugaydigan matn yoki nollar bilan to'ldiriladi. Funksiyada
ko'rsatkich bo'lsa, butun son parametrlari kichik qiymatlar (0..300) bilan beriladi —
odatda ular bufer uzunligi bo'ladi va bufer chegarasidan chiqmaslik kerak.

Himoya: har bir chaqiruv "qulash" (segfault, nolga bo'lish) va "osilib qolish"dan himoyalangan:
xato bitta testda ushlanadi va butun test to'xtab qolmaydi. Ikkala funksiya ham bir xil
kirishda qulasa — bu kirish o'tkazib yuboriladi; faqat bittasi qulasa — bu farq.
"""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from . import compiler, parser, sandbox

# Butun son turlarini tashkil qiluvchi so'zlar (C, IDA, Ghidra uslublari).
INTEGER_WORDS = {
    "char", "short", "int", "long", "signed", "unsigned", "const", "volatile",
    "__int8", "__int16", "__int32", "__int64",
    "_BYTE", "_WORD", "_DWORD", "_QWORD", "_BOOL1", "_BOOL2", "_BOOL4", "_BOOL8",
    "int8_t", "int16_t", "int32_t", "int64_t", "uint8_t", "uint16_t", "uint32_t", "uint64_t",
    "size_t", "ssize_t", "uintptr_t", "intptr_t",
    "undefined", "undefined1", "undefined2", "undefined4", "undefined8",
    "byte", "word", "dword", "qword", "uchar", "ushort", "uint", "ulong",
    "longlong", "ulonglong", "bool", "_Bool", "BOOL", "DWORD", "WORD", "BYTE",
}
WIDE_WORDS = {"long", "__int64", "_QWORD", "int64_t", "uint64_t", "size_t", "ssize_t", "uintptr_t",
              "intptr_t", "undefined8", "qword", "ulong", "longlong", "ulonglong"}

SYMBOL_A = "deobf_fn_original"
SYMBOL_B = "deobf_fn_candidate"
BUF_SIZE = 4096


TEST_TIMEOUT = 20.0       # butun test dasturi uchun soniyalar


@dataclass
class DiffResult:
    status: str          # "equivalent" | "mismatch" | "inconclusive" | "skipped"
    tests: int = 0
    mismatches: int = 0
    details: str = ""
    failed: str = ""     # "original" | "candidate" — qaysi kod kompilyatsiya bo'lmadi


def is_integer_type(type_str: str) -> bool:
    """'unsigned int', '__int64', 'undefined4' kabi turlar butun sonmi?"""
    if "*" in type_str or "[" in type_str:
        return False
    words = type_str.split()
    return bool(words) and all(w in INTEGER_WORDS for w in words)


def is_data_pointer(type_str: str) -> bool:
    """'char *', '_DWORD *', 'void *', 'struct ctx_t *' — bitta darajali ma'lumot ko'rsatkichi.

    Struktura ko'rsatkichi ham bufer sifatida beriladi: funksiya uning maydonlarini bufer ichidan o'qiydi.
    """
    if type_str.count("*") != 1 or not type_str.rstrip().endswith("*") or "(" in type_str:
        return False
    base = type_str.replace("*", " ").split()
    return bool(base) and all(re.fullmatch(r"[A-Za-z_]\w*", w) for w in base)


def pointer_like_params(code: str, params: list[tuple[str, str]]) -> set[int]:
    """Butun son turida e'lon qilingan, lekin ko'rsatkich sifatida ishlatilgan parametrlar.

    Ghidra ko'pincha `long param_1` deb yozadi va `*(int *)(param_1 + 8)` qilib o'qiydi —
    bunday parametrga tasodifiy son emas, bufer manzili berilishi kerak.
    """
    out = set()
    for i, (ptype, name) in enumerate(params):
        if not is_integer_type(ptype) or not (set(ptype.split()) & WIDE_WORDS):
            continue
        n = re.escape(name)
        if re.search(rf"\*\s*\([^()]*\*\s*\)\s*\(?\s*{n}\b", code) or re.search(rf"\(\s*{n}\s*\+", code):
            out.add(i)
    return out


def classify(ret_type: str, param_types: list[str], intptr: set[int]) -> tuple[list[str], str] | str:
    """Parametrlarni turlarga ajratadi: 'int' | 'ptr' | 'intptr'. Qo'llab-quvvatlanmasa — sabab matni."""
    kinds = []
    for i, t in enumerate(param_types):
        if i in intptr:
            kinds.append("intptr")
        elif is_integer_type(t):
            kinds.append("int")
        elif is_data_pointer(t):
            kinds.append("ptr")
        else:
            return f"qo'llab-quvvatlanmaydigan parametr turi: '{t}'"
    if ret_type.strip() == "void":
        rkind = "void"
    elif is_integer_type(ret_type):
        rkind = "int"
    elif is_data_pointer(ret_type):
        rkind = "ptr"
    else:
        return f"qo'llab-quvvatlanmaydigan qaytish turi: '{ret_type}'"
    return kinds, rkind


_HARNESS_PRELUDE = r"""
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <signal.h>
#include <setjmp.h>
#ifndef _WIN32
#include <sys/time.h>
#define JMP_BUF sigjmp_buf
#define SETJMP(b) sigsetjmp(b, 1)
#define LONGJMP(b, v) siglongjmp(b, v)
#else
#define JMP_BUF jmp_buf
#define SETJMP(b) setjmp(b)
#define LONGJMP(b, v) longjmp(b, v)
#endif

#define BUF BUFSIZE_PLACEHOLDER
/*INTERESTING*/
extern void deobf_support_reset(uint64_t seed);
extern uint64_t deobf_support_hash(void);

static uint64_t rng_state;
static uint64_t rnd64(void) {
    rng_state ^= rng_state << 13; rng_state ^= rng_state >> 7; rng_state ^= rng_state << 17;
    return rng_state;
}
/* Chegaraviy qiymatlar xatolarni ko'proq ochadi, shuning uchun ularni ham sinaymiz. */
static const uint64_t EDGES[] = {0, 1, 2, 3, 7, 8, 15, 16, 31, 32, 0x7F, 0x80, 0xFF, 0x100,
    0x7FFF, 0x8000, 0xFFFF, 0x7FFFFFFF, 0x80000000ull, 0xFFFFFFFFull, 0xFFFFFFFEull,
    0xFFFFFFFFFFFFFFFFull, 0x8000000000000000ull};
static const uint64_t SMALL_EDGES[] = {0, 1, 2, 3, 4, 7, 8, 15, 16, 31, 32, 63, 64, 100, 255, 256};
/* Bufer bor funksiyalarda butun son ko'pincha uzunlik/indeks bo'ladi. Uni buferga sig'adigan
   chegarada ushlab turamiz (BUF/8 — eng katta elementda ham, masalan 8 baytli, xavfsiz), aks holda
   sort/nusxalash bufer tashqarisiga yozib, asl va yangi funksiya "ekvivalent" bo'lsa ham farq qiladi. */
#define SAFE_LEN (BUF / 8)
static uint64_t pick(int small) {
    uint64_t r = rnd64();
    if (small) {
        if (r % 4 == 0) return SMALL_EDGES[(r >> 8) % (sizeof(SMALL_EDGES) / sizeof(SMALL_EDGES[0]))];
        if (r % 4 == 1) return INTERESTING[(r >> 8) % (sizeof(INTERESTING) / sizeof(INTERESTING[0]))] % (SAFE_LEN + 1);
        return (r >> 8) % (SAFE_LEN + 1);
    }
    if (r % 5 == 0) return INTERESTING[(r >> 8) % (sizeof(INTERESTING) / sizeof(INTERESTING[0]))];
    switch (r % 4) {
    case 0: return EDGES[(r >> 8) % (sizeof(EDGES) / sizeof(EDGES[0]))];
    case 1: return (r >> 8) % 64;
    default: return rnd64();
    }
}
static void fill(unsigned char *p) {
    uint64_t mode = rnd64() % 3, i;
    if (mode == 0) { for (i = 0; i < BUF; i++) p[i] = (unsigned char)rnd64(); }
    else if (mode == 1) {                       /* NUL bilan tugaydigan matn */
        uint64_t len = rnd64() % 200;
        for (i = 0; i < BUF; i++) p[i] = (unsigned char)(32 + rnd64() % 95);
        p[len] = 0;
    } else memset(p, 0, BUF);
    p[BUF - 1] = 0;
}

/* Qulash va osilib qolishdan himoya: signal kelsa, chaqiruvdan "sakrab" chiqamiz. */
static JMP_BUF jb;
static volatile int last_signal;
static void on_signal(int s) {
    last_signal = s;
#ifdef _WIN32
    signal(s, on_signal);
#endif
    LONGJMP(jb, s);
}
static void arm(void) {
#ifndef _WIN32
    struct itimerval tv = {{0, 0}, {0, 200000}};   /* bitta chaqiruv uchun 0.2 soniya */
    setitimer(ITIMER_REAL, &tv, 0);
#endif
}
static void disarm(void) {
#ifndef _WIN32
    struct itimerval tv = {{0, 0}, {0, 0}};
    setitimer(ITIMER_REAL, &tv, 0);
#endif
}
static long long where(const void *p, unsigned char (*bufs)[BUF], int n) {
    int k;
    if (!p) return -1;
    for (k = 0; k < n; k++)
        if ((const unsigned char *)p >= bufs[k] && (const unsigned char *)p < bufs[k] + BUF)
            return (long long)k * BUF + ((const unsigned char *)p - bufs[k]);
    return -2;                                      /* buferlardan tashqarida */
}
"""


def interesting_constants(code: str) -> list[int]:
    """Koddagi sonlar va ularning "qo'shnilari" (c, c+1, c-1, -c).

    `if (a1 == 0x1337BEEF)` kabi tarmoq faqat aynan shu qiymatda ishlaydi — tasodifiy son unga
    deyarli hech qachon teng chiqmaydi. Shuning uchun kirishlarning bir qismini koddan olamiz.
    """
    vals: list[int] = [0]
    for m in re.finditer(r"\b(0[xX][0-9A-Fa-f]+|\d+)[uUlL]*\b", parser.mask_code(code)):
        v = int(m.group(1), 0)
        for x in (v, v + 1, v - 1, -v):
            x &= 0xFFFFFFFFFFFFFFFF
            if x not in vals:
                vals.append(x)
        if len(vals) > 256:
            break
    return vals


def build_harness_source(ret_type: str, param_types: list[str], kinds: list[str], rkind: str,
                         n_tests: int, interesting: list[int] | None = None) -> str:
    """Ikki funksiyani taqqoslovchi main() funksiyali C dasturini yaratadi."""
    n = len(param_types)
    nbuf = max(1, sum(k != "int" for k in kinds))
    small = int(any(k != "int" for k in kinds))      # ko'rsatkich bo'lsa, butun sonlar kichik (uzunlik)
    params_decl = ", ".join(param_types) if param_types else "void"
    values = ", ".join(f"0x{v:X}ull" for v in (interesting or [0]))
    lines = [_HARNESS_PRELUDE.replace("BUFSIZE_PLACEHOLDER", str(BUF_SIZE))
             .replace("/*INTERESTING*/", f"static const uint64_t INTERESTING[] = {{{values}}};"),
             f"{ret_type} {SYMBOL_A}({params_decl});",
             f"{ret_type} {SYMBOL_B}({params_decl});",
             f"static unsigned char bufA[{nbuf}][BUF], bufB[{nbuf}][BUF];",
             "",
             "int main(void) {",
             "    int t, mism = 0, skipped = 0, k, hangs = 0;",
             "    rng_state = 12345ull ^ 0x9E3779B97F4A7C15ull;",
             "    signal(SIGSEGV, on_signal); signal(SIGFPE, on_signal); signal(SIGILL, on_signal);",
             "#ifndef _WIN32",
             "    signal(SIGBUS, on_signal); signal(SIGALRM, on_signal); signal(SIGABRT, on_signal);",
             "#endif",
             f"    for (t = 0; t < {n_tests}; t++) {{",
             "        uint64_t rs = rnd64();",
             "        volatile int ca = 0, cb = 0;",
             "        volatile unsigned long long ra = 0, rb = 0;",
             "        unsigned long long ha, hb;"]
    # parametrlarni tayyorlash
    a_args, b_args, shows = [], [], []
    bi = 0
    for i, (ptype, kind) in enumerate(zip(param_types, kinds)):
        if kind == "int":
            lines.append(f"        {ptype} p{i} = ({ptype})pick({small} || hangs > 8);")
            a_args.append(f"p{i}")
            b_args.append(f"p{i}")
            shows.append(f'printf("{", " if i else ""}0x%llx", (unsigned long long)p{i});')
        else:
            lines.append(f"        fill(bufA[{bi}]); memcpy(bufB[{bi}], bufA[{bi}], BUF);")
            a_args.append(f"({ptype})(uintptr_t)bufA[{bi}]")
            b_args.append(f"({ptype})(uintptr_t)bufB[{bi}]")
            shows.append(f'printf("{", " if i else ""}buf{bi}");')
            bi += 1

    def call(sym, args):
        c = f"{sym}({', '.join(args)})"
        if rkind == "void":
            return f"{c};"
        if rkind == "ptr":
            return f"r = (unsigned long long)where((const void *){c}, buf, {nbuf});"
        return f"r = (unsigned long long)({ret_type}){c};"

    lines += [
        "        deobf_support_reset(rs);",
        "        if (SETJMP(jb) == 0) { arm(); { unsigned long long r = 0; unsigned char (*buf)[BUF] = bufA; (void)buf; "
        + call(SYMBOL_A, a_args) + " ra = r; } disarm(); } else { disarm(); ca = last_signal; }",
        "        ha = deobf_support_hash();",
        "        if (ca == SIGALRM) hangs++;          /* tsikl juda uzoq: keyingi kirishlar kichik bo'ladi */",
        "        if (ca) { skipped++; continue; }    /* asl funksiya bu kirishda ishlamaydi — solishtirmaymiz */",
        "        deobf_support_reset(rs);",
        "        if (SETJMP(jb) == 0) { arm(); { unsigned long long r = 0; unsigned char (*buf)[BUF] = bufB; (void)buf; "
        + call(SYMBOL_B, b_args) + " rb = r; } disarm(); } else { disarm(); cb = 1; }",
        "        hb = deobf_support_hash();",
        "        {",
        "            const char *why = 0;",
        "            if (cb) why = \"yangi funksiya xato bilan to'xtadi yoki osilib qoldi\";",
        "            else if (ra != rb) why = \"qaytish qiymati\";",
        f"            else for (k = 0; k < {nbuf}; k++) if (memcmp(bufA[k], bufB[k], BUF)) {{ why = \"bufer mazmuni\"; break; }}",
        "            if (!why && ha != hb) why = \"global o'zgaruvchilar yoki tashqi chaqiruvlar\";",
        "            if (why) {",
        "                if (mism < 5) {",
        '                    printf("MISMATCH (%s) args=(", why);',
    ]
    lines += ["                    " + s for s in shows]
    lines += [
        '                    printf(") original=0x%llx candidate=0x%llx\\n", ra, rb);',
        "                }",
        "                mism++;",
        "            }",
        "        }",
        "        fflush(stdout);",
        "    }",
        f'    printf("RESULT tests=%d mismatches=%d skipped=%d\\n", {n_tests} - skipped, mism, skipped);',
        "    return 0;",
        "}",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- global o'zgaruvchilar va stublar

# IDA va Ghidra global ma'lumotlarga beradigan nomlar: dword_404010, byte_4020, unk_40A0, DAT_00104010 ...
_GLOBAL_RE = re.compile(r"\b(_?(byte|word|dword|qword|unk|off|stru|asc|xmmword|DAT|PTR)_[0-9A-Fa-f]{3,16})\b")
_ELEM = {"byte": "uint8_t", "word": "uint16_t", "dword": "uint32_t", "qword": "uint64_t",
         "off": "uint64_t", "PTR": "uint64_t", "DAT": "uint32_t"}


@dataclass
class GlobalVar:
    name: str
    ctype: str
    array: bool


def _declared(code: str, name: str, extern_counts: bool = True) -> bool:
    """Kodda `name` e'lon qilinganmi? extern_counts=False — faqat haqiqiy ta'rif (xotira ajratiladigan)."""
    prefix = r"(?:static\s+|extern\s+|const\s+)*" if extern_counts else r"(?:static\s+|const\s+)*(?!extern\b)"
    return bool(re.search(rf"^[ \t]*{prefix}[A-Za-z_][\w \t\*]*\b{re.escape(name)}\b"
                          rf"\s*(?:\[[^\]]*\])?\s*(?:=|;)", code, flags=re.M))


def find_globals(code: str, defined: set[str]) -> list[GlobalVar]:
    """Psevdokodda ishlatilgan, lekin ta'riflanmagan IDA/Ghidra global o'zgaruvchilari."""
    out: dict[str, GlobalVar] = {}
    for m in _GLOBAL_RE.finditer(code):
        name, prefix = m.group(1), m.group(2)
        if name in out or name in defined or _declared(code, name, extern_counts=False):
            continue
        array = (prefix not in _ELEM or bool(re.search(rf"\b{name}\s*\[", code))
                 or bool(re.search(rf"&\s*{name}\b", code)))
        ctype = _ELEM.get(prefix, "uint8_t")
        if prefix == "DAT" and array:
            ctype = "uint8_t"
        out[name] = GlobalVar(name, ctype, array)
    return list(out.values())


def declare_globals(code: str, gvars: list[GlobalVar]) -> str:
    """Kod boshiga `extern` e'lonlarni qo'shadi (kodda o'zi e'lon qilmagan bo'lsa)."""
    decls = [f"extern {g.ctype} {g.name}{'[]' if g.array else ''};" for g in gvars if not _declared(code, g.name)]
    return ("#include <stdint.h>\n" + "\n".join(decls) + "\n" + code) if decls else code


@dataclass
class DefinedGlobal:
    """Kirish matnining o'zida ta'riflangan global o'zgaruvchi: `int dword_404000;`, `unsigned char t[4] = {..};`"""
    name: str
    base: str          # "unsigned char", "int" ...
    stars: str         # "*" ko'rsatkich bo'lsa
    dims: str          # "[27]" yoki "[]" yoki ""
    init: str | None   # boshlang'ich qiymat matni


_GLOBAL_DEF_RE = re.compile(
    r"^(?:static\s+)?((?:(?:const|volatile|unsigned|signed)\s+)*[A-Za-z_]\w*(?:\s+[A-Za-z_]\w*)*?)"
    r"\s*(\**)\s*([A-Za-z_]\w*)\s*((?:\[[^\]]*\])*)\s*(?:=\s*([\s\S]+))?$")


def split_globals(code: str, only: set[str] | None = None) -> tuple[str, list[DefinedGlobal]]:
    """Funksiyalardan tashqaridagi global o'zgaruvchi ta'riflarini `extern` e'longa aylantiradi.

    Nima uchun: asl va yangi funksiya BIR XIL global holat bilan ishlashi kerak. Shuning uchun global
    o'zgaruvchilar yordamchi modulda bitta nusxada yaratiladi va har bir chaqiruvdan oldin boshlang'ich
    holatiga qaytariladi (ichki o'zgarishlar keyingi testga "oqib" o'tmaydi).
    only — faqat shu nomlarni aylantirish (yangi kodda asl koddagi globallarni qayta ta'riflagan bo'lsa).
    """
    masked = parser.mask_code(code)
    spans = []
    for f in parser.parse(code).functions:
        start = code.find(f.text)
        spans.append((start, start + len(f.text)))
    out, found, pos, depth, stmt_start = [], [], 0, 0, 0

    def outside(i: int) -> bool:
        return not any(a <= i < b for a, b in spans)

    i = 0
    while i < len(masked):
        if not outside(i):
            i = next(b for a, b in spans if a <= i < b)
            stmt_start = i
            continue
        ch = masked[i]
        depth += (ch == "{") - (ch == "}")
        if ch == ";" and depth == 0:
            m_text = masked[stmt_start:i].strip()
            lead = len(masked[stmt_start:i]) - len(masked[stmt_start:i].lstrip())
            s0 = stmt_start + lead
            m = _GLOBAL_DEF_RE.match(m_text)
            # const + boshlang'ich qiymatli global — faqat o'qiladigan jadval/satr (masalan MESSAGE[]).
            # Uni extern qilmaymiz: o'zgarmas holat "oqib" ketmaydi, har bir modul o'z (static) nusxasini
            # saqlasa bo'ladi. Aks holda `extern const char MESSAGE[];` to'liqsiz tur bo'lib, sizeof buziladi.
            read_only = m and "const" in m.group(1).split() and m.group(5) is not None
            skip = (not m or read_only or m_text.startswith(("typedef", "extern", "#", "struct ", "union ", "enum "))
                    or "(" in m_text.split("=")[0] or "," in parser.split_top_level(m_text.split("=")[0], ";")[0]
                    or m.group(3) in ("return",))
            if not skip and (only is None or m.group(3) in only):
                init = code[s0 + m.start(5):s0 + m.end(5)].strip() if m.group(5) else None
                g = DefinedGlobal(m.group(3), m.group(1).replace("static ", "").strip(), m.group(2), m.group(4), init)
                found.append(g)
                out.append(code[pos:s0])
                out.append(f"extern {g.base} {g.stars}{g.name}{g.dims};")
                pos = i + 1
            stmt_start = i + 1
        i += 1
    out.append(code[pos:])
    return "".join(out), found


def call_arity(code: str, name: str) -> int:
    """Kodda `name(...)` chaqiruvlaridagi argumentlar sonining eng kattasi."""
    best = 0
    for m in re.finditer(rf"\b{re.escape(name)}\s*\(", code):
        depth, i, start, args = 0, m.end() - 1, m.end(), 0
        while i < len(code):
            ch = code[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break
            elif ch == "," and depth == 1:
                args += 1
            i += 1
        inner = code[start:i].strip()
        best = max(best, args + 1 if inner else 0)
    return min(best, 8)


def build_support_source(data_blobs: dict[str, bytes], gvars: list[GlobalVar], stubs: dict[str, int],
                         defined: list[DefinedGlobal] | None = None) -> str:
    """Global ma'lumotlar, global o'zgaruvchilar va tashqi funksiya stublarini o'z ichiga olgan C fayl.

    deobf_support_reset(seed) har bir chaqiruvdan oldin hamma narsani bir xil holatga qaytaradi,
    deobf_support_hash() esa chaqiruvdan keyingi holatning "barmoq izini" (xeshini) beradi.
    """
    L = ["#include <stdint.h>", "#include <string.h>",
         "static uint64_t s_rng; static uint64_t s_trace; static uint64_t s_calls;",
         "static uint64_t s_next(void) { s_rng ^= s_rng << 13; s_rng ^= s_rng >> 7; s_rng ^= s_rng << 17; return s_rng; }",
         "static void s_fill(void *p, size_t n) { unsigned char *b = p; size_t i; for (i = 0; i < n; i++) b[i] = (unsigned char)s_next(); }",
         "static uint64_t s_mix(uint64_t h, const void *p, size_t n) { const unsigned char *b = p; size_t i;"
         " for (i = 0; i < n; i++) h = (h ^ b[i]) * 0x100000001B3ull; return h; }"]
    resets, hashes = [], []
    for name, data in data_blobs.items():
        values = ", ".join(f"0x{b:02X}" for b in data)
        L.append(f"unsigned char {name}[{len(data)}];")
        L.append(f"static const unsigned char {name}__init[{len(data)}] = {{ {values} }};")
        resets.append(f"memcpy({name}, {name}__init, sizeof {name});")
        hashes.append(f"h = s_mix(h, {name}, sizeof {name});")
    for g in defined or []:
        if g.init is not None:
            L.append(f"static {g.base} {g.stars}{g.name}__init{g.dims} = {g.init};")
            dims = g.dims if g.dims not in ("", "[]") else ("" if not g.dims else f"[sizeof {g.name}__init / sizeof {g.name}__init[0]]")
            L.append(f"{g.base} {g.stars}{g.name}{dims};")
            resets.append(f"memcpy(&{g.name}, &{g.name}__init, sizeof {g.name});")
        else:
            L.append(f"{g.base} {g.stars}{g.name}{g.dims or ''};")
            resets.append(f"s_fill(&{g.name}, sizeof {g.name});")
        hashes.append(f"h = s_mix(h, &{g.name}, sizeof {g.name});")
    for g in gvars:
        size = f"[{BUF_SIZE} / sizeof({g.ctype})]" if g.array else ""
        L.append(f"{g.ctype} {g.name}{size} __attribute__((aligned(16)));")
        resets.append(f"s_fill(&{g.name}, sizeof {g.name});")
        hashes.append(f"h = s_mix(h, &{g.name}, sizeof {g.name});")
    for name, n in stubs.items():
        params = ", ".join(f"uint64_t a{i}" for i in range(n)) or "void"
        body = [f"uint64_t h = 0x{abs(hash(name)) & 0xFFFFFFFFFFFF:X}ull ^ (s_calls++ * 0x9E37ull);"]
        body += [f"h = (h ^ (a{i} & 0xFFFFFFFFull)) * 0x100000001B3ull;" for i in range(n)]
        body += ["s_trace = s_trace * 31u + h;", "return (h >> 17) & 0x7FFFFFFFull;"]
        L.append(f"uint64_t {name}({params}) {{ " + " ".join(body) + " }")
    L.append("void deobf_support_reset(uint64_t seed) { s_rng = seed | 1u; s_trace = 0; s_calls = 0; "
             + " ".join(resets) + " }")
    L.append("uint64_t deobf_support_hash(void) { uint64_t h = 0xCBF29CE484222325ull ^ s_trace; "
             + " ".join(hashes) + " return h; }")
    return "\n".join(L) + "\n"


_UNDEF_RE = re.compile(r"undefined reference to [`'\"]_?(\w+)['\"]|undefined symbol:\s*_?(\w+)|\"_(\w+)\", referenced from")


def differential_test(code_a: str, func_a: str, code_b: str, func_b: str,
                      ret_type: str, param_types: list[str],
                      n_tests: int = 2000, data_blobs: dict[str, bytes] | None = None,
                      intptr: set[int] | None = None) -> DiffResult:
    """code_a ichidagi func_a va code_b ichidagi func_b ni solishtiradi.

    data_blobs — binar fayldan olingan global ma'lumotlar (masalan, shifrlangan satr baytlari);
    intptr     — butun son turida, lekin ko'rsatkich sifatida ishlatiladigan parametrlar indekslari.
    """
    cls = classify(ret_type, param_types, intptr or set())
    if isinstance(cls, str):
        return DiffResult("skipped", details=cls[0].upper() + cls[1:])
    kinds, rkind = cls
    if compiler.find_compiler() is None:
        return DiffResult("skipped", details="C kompilyatori topilmadi")

    blobs = {k: v for k, v in (data_blobs or {}).items()
             if re.fullmatch(r"[A-Za-z_]\w*", k) and re.search(rf"\b{k}\b", code_a + code_b)
             and not re.search(rf"\b{k}\s*\[[^\]]*\]\s*=", code_a)}
    code_a, defined = split_globals(code_a)
    names = {g.name for g in defined}
    code_b, _ = split_globals(code_b, only=names)            # yangi kod asl globalni qayta ta'riflagan bo'lsa
    gvars = find_globals(code_a + "\n" + code_b, set(blobs) | names)
    code_a, code_b = declare_globals(code_a, gvars), declare_globals(code_b, gvars)

    with tempfile.TemporaryDirectory(prefix="deobf_diff_") as tmp:
        return _run_diff(Path(tmp), code_a, func_a, code_b, func_b, ret_type, param_types, kinds, rkind,
                         n_tests, blobs, gvars, defined)


def _run_diff(wd: Path, code_a, func_a, code_b, func_b, ret_type, param_types, kinds, rkind,
              n_tests, blobs, gvars, defined) -> DiffResult:
    # -D makrosi yordamida ikkala funksiyaga turli nom beramiz, shunda ular bitta
    # dasturda birga yashay oladi (aks holda nomlar to'qnashadi).
    # Fayllarda boshqa (yordamchi) funksiyalar ham bo'lishi mumkin. Nomlar to'qnashmasligi uchun
    # ularga ham alohida nom beramiz; yangi kod asl fayldagi yordamchini chaqirsa — o'shanga ulanadi.
    names_a = {f.name for f in parser.parse(code_a).functions} - {func_a}
    names_b = {f.name for f in parser.parse(code_b).functions} - {func_b}
    defs_a = {func_a: SYMBOL_A, **{n: f"deobfA_{n}" for n in names_a}}
    defs_b = {func_b: SYMBOL_B, **{n: f"deobfB_{n}" for n in names_b}}
    defs_b.update({n: f"deobfA_{n}" for n in names_a - names_b if re.search(rf"\b{n}\s*\(", code_b)})
    res_a, obj_a = compiler.compile_object(code_a, wd, "original", defs_a)
    if not res_a.ok:
        return DiffResult("inconclusive", details="Asl kod kompilyatsiya bo'lmadi:\n" + res_a.errors,
                          failed="original")
    res_b, obj_b = compiler.compile_object(code_b, wd, "candidate", defs_b)
    if not res_b.ok:
        return DiffResult("inconclusive", details="Yangi kod kompilyatsiya bo'lmadi:\n" + res_b.errors,
                          failed="candidate")
    harness = build_harness_source(ret_type, param_types, kinds, rkind, n_tests,
                                   interesting_constants(code_a + "\n" + code_b))
    res_h, obj_h = compiler.compile_object(harness, wd, "harness")
    if not res_h.ok:
        return DiffResult("inconclusive", details="Test dasturi kompilyatsiya bo'lmadi:\n" + res_h.errors)

    exe = wd / "difftest.exe"
    stubs: dict[str, int] = {}
    for _ in range(2):            # 2-urinish: aniqlanmagan tashqi funksiyalar uchun stublar bilan
        res_s, obj_s = compiler.compile_object(build_support_source(blobs, gvars, stubs, defined), wd, "support")
        if not res_s.ok:
            return DiffResult("inconclusive", details="Yordamchi kod kompilyatsiya bo'lmadi:\n" + res_s.errors)
        res_l = compiler.link([obj_a, obj_b, obj_h, obj_s], exe)
        if res_l.ok:
            break
        missing = {next(g for g in m.groups() if g) for m in _UNDEF_RE.finditer(res_l.errors)}
        missing = {n for n in missing if not n.startswith(("deobf_fn_", "deobfA_", "deobfB_"))}
        if not missing or stubs:
            return DiffResult("inconclusive", details="Bog'lash (link) bo'lmadi:\n" + res_l.errors)
        stubs = {name: max(call_arity(code_a, name), call_arity(code_b, name)) for name in sorted(missing)}
    proc = sandbox.run([str(exe)], timeout=TEST_TIMEOUT, cpu_sec=int(TEST_TIMEOUT), mem_mb=512, cwd=str(wd))
    if proc.timed_out:
        return DiffResult("inconclusive", details=f"Test {TEST_TIMEOUT:.0f} soniyada tugamadi (cheksiz tsikl?)")
    out = proc.stdout
    m = re.search(r"RESULT tests=(\d+) mismatches=(\d+) skipped=(\d+)", out)
    if proc.returncode != 0 or not m:
        # Dasturning ixtiyoriy chiqishini qaytarmaymiz — faqat test dasturining o'z qatorlari
        lines = [ln for ln in out.splitlines() if ln.startswith(("MISMATCH", "RESULT"))][:5]
        return DiffResult("inconclusive", details=f"Test dasturi favqulodda to'xtadi (kod {proc.returncode})"
                                                  + ("\n" + "\n".join(lines) if lines else ""))
    tests, mism, skipped = int(m.group(1)), int(m.group(2)), int(m.group(3))
    notes = []
    if stubs:
        notes.append(f"tashqi funksiyalar stub bilan almashtirildi: {', '.join(stubs)}")
    if gvars or defined:
        notes.append("global o'zgaruvchilar modellashtirildi: " + ", ".join([g.name for g in defined] + [g.name for g in gvars]))
    if skipped:
        notes.append(f"{skipped} ta kirishda asl funksiyaning o'zi xato bilan to'xtadi yoki osilib qoldi (o'tkazildi)")
    note = (" (" + "; ".join(notes) + ")") if notes else ""
    examples = "\n".join(line for line in out.splitlines() if line.startswith("MISMATCH"))
    if tests == 0:
        return DiffResult("inconclusive", 0, 0, "Hech bir kirishda asl funksiya normal ishlamadi" + note)
    if mism == 0:
        return DiffResult("equivalent", tests, 0, f"{tests} ta tasodifiy test — barchasi mos keldi{note}")
    return DiffResult("mismatch", tests, mism, f"{mism}/{tests} testda farq{note}:\n{examples}")
