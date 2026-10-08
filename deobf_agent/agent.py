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
    model: str | None = None          # None -> default (haiku) yoki DEOBF_MODEL
    offline: bool = False             # True -> LLM ishlatilmaydi (bepul)
    effort: str = "medium"
    language: str = "uz"
    max_rounds: int = 3               # tekshiruvdan o'tmasa, necha marta tuzatish so'raladi
    n_tests: int = 2000               # differensial testlar soni
    max_tokens: int = 16000
    cache_dir: str | None = ".deobf_cache"   # None -> disk kesh o'chirilgan
    api_key: str | None = None        # tashrif buyuruvchining o'z kaliti (public rejim)
    client: object = None             # testlar uchun soxta mijoz


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
                 progress: ProgressFn) -> tuple[DeobfResult, verifier.VerifyReport, list[Attempt]]:
    attempts = []
    result, rep = None, None
    # Avval eng kuchli soddalashtirish, testdan o'tmasa — ehtiyotkorroq darajalar
    for level in (2, 1, 0):
        result = offline.run_offline(func, analysis, parsed.preamble, level=level)
        progress(f"Tekshiruv (offline, {level}-daraja): kompilyatsiya va differensial test...")
        rep = verifier.verify(parsed, func, result.c_code, cfg.n_tests)
        attempts.append(Attempt(len(attempts) + 1, rep.status, f"[daraja {level}] " + rep.details))
        if rep.ok:
            break
    return result, rep, attempts


def deobfuscate_function(parsed: ParsedInput, func: FunctionInfo, cfg: AgentConfig,
                         progress: ProgressFn = _noop, callee_notes: dict[str, str] | None = None) -> FunctionReport:
    t0 = time.time()
    progress(f"[{func.name}] Statik tahlil...")
    analysis = detectors.analyze(func, parsed.data_blobs)
    progress(f"[{func.name}] {len(analysis.findings)} ta belgi topildi: {', '.join(analysis.techniques()) or 'yo`q'}")

    attempts: list[Attempt] = []
    best: tuple[DeobfResult, verifier.VerifyReport] | None = None
    engine, error, usage = "offline", "", UsageStats()
    if not cfg.offline:
        model = resolve_model(cfg.model)
        session = ClaudeSession(model=model, effort=cfg.effort, max_tokens=cfg.max_tokens, api_key=cfg.api_key,
                                cache=DiskCache(cfg.cache_dir) if cfg.cache_dir else None, client=cfg.client)
        usage = session.usage
        try:
            message = prompts.build_user_message(func, parsed.style, analysis, parsed.data_blobs, cfg.language,
                                                 callee_notes)
            for rnd in range(1, cfg.max_rounds + 1):
                progress(f"[{func.name}] Claude ({model}) so'rovi, {rnd}-urinish...")
                result = session.ask(message)
                progress(f"[{func.name}] Tekshiruv: kompilyatsiya va differensial test...")
                rep = verifier.verify(parsed, func, result.c_code, cfg.n_tests)
                attempts.append(Attempt(rnd, rep.status, rep.details))
                progress(f"[{func.name}] Natija: {rep.label_uz}")
                if best is None or verifier.STATUS_RANK[rep.status] > verifier.STATUS_RANK[best[1].status]:
                    best, engine = (result, rep), model
                if rep.ok:
                    break
                message = prompts.build_fix_message(rep.problems, cfg.language)
        except LLMError as exc:
            error = str(exc)
            progress(f"[{func.name}] LLM xatosi: {error} — offline natijaga o'tilmoqda...")
    if best is None:
        result, rep, extra = _run_offline(parsed, func, analysis, cfg, progress)
        attempts += extra
        best = (result, rep)

    return FunctionReport(func, parsed.style, engine, analysis, best[0], best[1], attempts, usage=usage,
                          metrics_before=metrics.measure(func.text), metrics_after=metrics.measure(best[0].c_code),
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
    progress(f"Uslub: {parsed.style}; funksiyalar: {', '.join(f.name for f in funcs)}")
    notes: dict[str, str] = {}
    reports: dict[str, FunctionReport] = {}
    for f in _callee_first(funcs):
        rep = deobfuscate_function(parsed, f, cfg, progress, {c: notes[c] for c in f.calls if c in notes})
        reports[f.name] = rep
        notes[f.name] = f"{rep.result.suggested_name}: {rep.result.summary}"
    return parsed, [reports[f.name] for f in funcs]      # foydalanuvchiga asl tartibda
