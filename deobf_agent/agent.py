"""Agent: barcha qismlarni bitta jarayonga birlashtiradi.

    kirish matni -> parser -> statik tahlil -> (Claude yoki offline) -> tekshiruv
                                                    ^                      |
                                                    +---- xato bo'lsa -----+   (maks. N urinish)

Nima uchun bu "agent": oddiy chatbot javobni bir marta beradi va tamom. Bizning
vosita esa natijani o'zi tekshiradi (kompilyator + testlar) va muammo bo'lsa,
aniq xato ma'lumoti bilan modeldan tuzatishni so'raydi — ya'ni maqsadga erishish
uchun o'z harakatlarini natijaga qarab o'zgartiradi.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from . import detectors, metrics, offline, parser, prompts, verifier
from .detectors import AnalysisResult
from .llm import ClaudeSession, DiskCache, LLMError, UsageStats, resolve_model
from .models import FunctionInfo, ParsedInput
from .schema import DeobfResult


@dataclass
class AgentConfig:
    model: str | None = None          # None -> default (sonnet) yoki DEOBF_MODEL
    offline: bool = False             # True -> LLM ishlatilmaydi (bepul)
    effort: str = "medium"
    language: str = "uz"
    max_rounds: int = 3               # tekshiruvdan o'tmasa, necha marta tuzatish so'raladi
    n_tests: int = 2000               # differensial testlar soni
    max_tokens: int = 16000
    cache_dir: str | None = ".deobf_cache"   # None -> disk kesh o'chirilgan
    api_key: str | None = field(default=None, repr=False)   # tashrif buyuruvchining o'z kaliti (public rejim)
    client: object = None             # testlar uchun soxta mijoz
    max_functions: int | None = None  # bir so'rovda ko'pi bilan nechta funksiya (public demo uchun)
    time_limit_sec: float | None = None   # butun tahlil uchun umumiy vaqt chegarasi (public demo uchun)


@dataclass
class Attempt:
    round: int
    status: str
    details: str


@dataclass
class FunctionReport:
    function: FunctionInfo
    style: str
    engine: str                       # "offline" yoki model nomi
    analysis: AnalysisResult
    result: DeobfResult
    verification: verifier.VerifyReport
    attempts: list[Attempt] = field(default_factory=list)
    usage: UsageStats = field(default_factory=UsageStats)
    metrics_before: metrics.Metrics | None = None
    metrics_after: metrics.Metrics | None = None
    error: str = ""                   # LLM xatosi bo'lsa (natija offline'dan olinadi)
    elapsed_sec: float = 0.0


ProgressFn = Callable[[str], None]


def _noop(_: str) -> None:
    pass


def _run_offline(parsed: ParsedInput, func: FunctionInfo, analysis: AnalysisResult, cfg: AgentConfig,
                 progress: ProgressFn, first_round: int = 1) -> tuple[DeobfResult, verifier.VerifyReport, list[Attempt]]:
    attempts = []
    result, rep = None, None
    # Avval eng kuchli soddalashtirish, testdan o'tmasa — ehtiyotkorroq darajalar
    for level in (2, 1, 0, -1):             # -1: hech narsa o'zgartirilmaydi (noto'g'ri kod chiqmasligi uchun oxirgi himoya)
        result = offline.run_offline(func, analysis, parsed.preamble, level=level)
        progress(f"Tekshiruv (offline, {level}-daraja): kompilyatsiya va differensial test...")
        rep = verifier.verify(parsed, func, result.c_code, cfg.n_tests)
        attempts.append(Attempt(first_round + len(attempts), rep.status, f"[daraja {level}] " + rep.details))
        if rep.ok:
            break
    return result, rep, attempts


def _function_text(code: str, name: str) -> str:
    """c_code ichidan faqat funksiyaning o'zi (e'lonlar va izohlarsiz) — murakkablikni to'g'ri o'lchash uchun."""
    f = parser.parse(code).get(name)
    return f.text if f is not None else code


def _better(a: verifier.VerifyReport, b: verifier.VerifyReport) -> bool:
    """a, b dan yaxshimi? Avval holat darajasi; teng bo'lsa — kamroq farqli test."""
    ra, rb = verifier.STATUS_RANK[a.status], verifier.STATUS_RANK[b.status]
    if ra != rb:
        return ra > rb
    return a.status == "mismatch" and a.mismatches < b.mismatches


def deobfuscate_function(parsed: ParsedInput, func: FunctionInfo, cfg: AgentConfig,
                         progress: ProgressFn = _noop, callee_notes: dict[str, str] | None = None,
                         deadline: float | None = None) -> FunctionReport:
    t0 = time.time()
    progress(f"[{func.name}] Statik tahlil...")
    analysis = detectors.analyze(func, parsed.data_blobs)
    progress(f"[{func.name}] {len(analysis.findings)} ta belgi topildi: {', '.join(analysis.techniques()) or 'yo`q'}")

    attempts: list[Attempt] = []
    best: tuple[DeobfResult, verifier.VerifyReport] | None = None
    engine, error, usage = "offline", "", UsageStats()
    session = None
    if not cfg.offline:
        model = resolve_model(cfg.model)
        session = ClaudeSession(model=model, effort=cfg.effort, max_tokens=cfg.max_tokens, api_key=cfg.api_key,
                                cache=DiskCache(cfg.cache_dir) if cfg.cache_dir else None, client=cfg.client)
        usage = session.usage
        try:
            message = prompts.build_user_message(func, parsed.style, analysis, parsed.data_blobs, cfg.language,
                                                 callee_notes)
            for rnd in range(1, cfg.max_rounds + 1):
                if deadline is not None and time.monotonic() > deadline:
                    error = error or "Vaqt chegarasiga yetildi — keyingi urinishlar bajarilmadi."
                    break
                progress(f"[{func.name}] Claude ({model}) so'rovi, {rnd}-urinish...")
                result = session.ask(message)
                progress(f"[{func.name}] Tekshiruv: kompilyatsiya va differensial test...")
                rep = verifier.verify(parsed, func, result.c_code, cfg.n_tests)
                attempts.append(Attempt(rnd, rep.status, rep.details))
                progress(f"[{func.name}] Natija: {rep.label_uz}")
                if best is None or _better(rep, best[1]):
                    best, engine = (result, rep), model
                if rep.ok:
                    break
                message = prompts.build_fix_message(rep.problems, cfg.language)
        except LLMError as exc:
            error = str(exc)
            progress(f"[{func.name}] LLM xatosi: {error}")
    if session is not None and best is not None and best[1].status in ("mismatch", "compile_error"):
        session.forget()               # xato javob keshda qolib, qayta urinishda $0 ga "qaytib kelmasin"
    # Claude natijasi yo'q yoki "verified" emas -> offline natija bilan ham solishtiramiz va yaxshisini olamiz
    if best is None or best[1].status != "verified":
        if best is not None:
            progress(f"[{func.name}] Claude natijasi tasdiqlanmadi — offline natija bilan solishtirilmoqda...")
        result, rep, extra = _run_offline(parsed, func, analysis, cfg, progress, len(attempts) + 1)
        attempts += extra
        if best is None or _better(rep, best[1]):
            if best is not None:
                error = error or (f"Claude natijasi tekshiruvdan o'tmadi ({best[1].status}); "
                                  "o'rniga offline natija ishlatildi.")
            best, engine = (result, rep), "offline"

    return FunctionReport(func, parsed.style, engine, analysis, best[0], best[1], attempts, usage=usage,
                          metrics_before=metrics.measure(func.text), metrics_after=metrics.measure(_function_text(best[0].c_code, func.name)),
                          error=error, elapsed_sec=round(time.time() - t0, 2))


def _callee_first(funcs: list[FunctionInfo]) -> list[FunctionInfo]:
    """Funksiyalarni "avval chaqiriladiganlar" tartibida qaytaradi (pastdan yuqoriga tahlil uchun)."""
    by_name = {f.name: f for f in funcs}
    order: list[FunctionInfo] = []
    seen: set[str] = set()

    def visit(f: FunctionInfo) -> None:
        if f.name in seen:
            return
        seen.add(f.name)
        for callee in f.calls:
            if callee in by_name:
                visit(by_name[callee])
        order.append(f)

    for f in funcs:
        visit(f)
    return order


def deobfuscate_text(text: str, cfg: AgentConfig, function: str | None = None,
                     progress: ProgressFn = _noop) -> tuple[ParsedInput, list[FunctionReport]]:
    """Matndagi barcha (yoki tanlangan) funksiyalarni deobfuskatsiya qiladi.

    Bir nechta funksiya bo'lsa, avval chaqiriladigan (yordamchi) funksiyalar tahlil qilinadi va
    ularning qisqa tavsifi chaqiruvchi funksiya uchun LLM'ga beriladi — odam ham kodni shunday o'qiydi.
    """
    parsed = parser.parse(text)
    if not parsed.functions:
        raise ValueError("Matnda funksiya topilmadi. Psevdokodni to'liq (signatura va { } tanasi bilan) kiriting.")
    funcs = parsed.functions
    if function:
        f = parsed.get(function)
        if f is None:
            names = ", ".join(x.name for x in parsed.functions)
            raise ValueError(f"`{function}` funksiyasi topilmadi. Mavjud funksiyalar: {names}")
        funcs = [f]
    if cfg.max_functions is not None and len(funcs) > cfg.max_functions:
        raise ValueError(f"Bir martada ko'pi bilan {cfg.max_functions} ta funksiya tahlil qilinadi (kiritildi: "
                         f"{len(funcs)}). Kerakli funksiyani 'Funksiya' maydonida tanlang yoki kodni qisqartiring.")
    progress(f"Uslub: {parsed.style}; funksiyalar: {', '.join(f.name for f in funcs)}")
    deadline = time.monotonic() + cfg.time_limit_sec if cfg.time_limit_sec else None
    notes: dict[str, str] = {}
    reports: dict[str, FunctionReport] = {}
    for f in _callee_first(funcs):
        if deadline is not None and time.monotonic() > deadline:
            raise ValueError("Tahlil vaqt chegarasiga yetdi. Kamroq funksiya kiriting.")
        rep = deobfuscate_function(parsed, f, cfg, progress, {c: notes[c] for c in f.calls if c in notes}, deadline)
        reports[f.name] = rep
        # Yordamchi funksiya haqida eslatma: asl nomi saqlanadi (taklif qilingan nom chaqiruvchi kodni buzmasligi uchun)
        notes[f.name] = f"[tekshiruv: {rep.verification.status}] {rep.result.summary}"
    return parsed, [reports[f.name] for f in funcs]      # foydalanuvchiga asl tartibda
