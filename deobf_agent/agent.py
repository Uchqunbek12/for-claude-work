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
from .verifier import STATUS_RANK, VerifyReport


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
    verification: VerifyReport
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
                 progress: ProgressFn) -> tuple[DeobfResult, VerifyReport, list[Attempt]]:
    attempts = []
    result = offline.run_offline(func, analysis, parsed.preamble, aggressive=True)
    progress("Tekshiruv: kompilyatsiya va differensial test...")
    rep = verifier.verify(parsed, func, result.c_code, cfg.n_tests)
    attempts.append(Attempt(1, rep.status, rep.details))
    if not rep.ok:
        # Xavfsizroq variant: faqat ifodalarni soddalashtiramiz, tarmoqlarni kesmaymiz
        progress("Natija mos kelmadi — ehtiyotkor (faqat ifodalar) rejimida qayta urinilmoqda...")
        result = offline.run_offline(func, analysis, parsed.preamble, aggressive=False)
        rep = verifier.verify(parsed, func, result.c_code, cfg.n_tests)
        attempts.append(Attempt(2, rep.status, rep.details))
    return result, rep, attempts


def deobfuscate_function(parsed: ParsedInput, func: FunctionInfo, cfg: AgentConfig,
                         progress: ProgressFn = _noop) -> FunctionReport:
    t0 = time.time()
    progress(f"[{func.name}] Statik tahlil...")
    analysis = detectors.analyze(func, parsed.data_blobs)
    progress(f"[{func.name}] {len(analysis.findings)} ta belgi topildi: {', '.join(analysis.techniques()) or 'yo`q'}")

    if cfg.offline:
        result, rep, attempts = _run_offline(parsed, func, analysis, cfg, progress)
        report = FunctionReport(func, parsed.style, "offline", analysis, result, rep, attempts)
    else:
        model = resolve_model(cfg.model)
        session = ClaudeSession(model=model, effort=cfg.effort, max_tokens=cfg.max_tokens,
                                cache=DiskCache(cfg.cache_dir) if cfg.cache_dir else None, client=cfg.client)
        attempts: list[Attempt] = []
        best: tuple[DeobfResult, VerifyReport] | None = None
        error = ""
        try:
            message = prompts.build_user_message(func, parsed.style, analysis, parsed.data_blobs, cfg.language)
            for rnd in range(1, cfg.max_rounds + 1):
                progress(f"[{func.name}] Claude ({model}) so'rovi, {rnd}-urinish...")
                result = session.ask(message)
                progress(f"[{func.name}] Tekshiruv: kompilyatsiya va differensial test...")
                rep = verifier.verify(parsed, func, result.c_code, cfg.n_tests)
                attempts.append(Attempt(rnd, rep.status, rep.details))
                progress(f"[{func.name}] Natija: {rep.label_uz}")
                if best is None or STATUS_RANK[rep.status] > STATUS_RANK[best[1].status]:
                    best = (result, rep)
                if rep.ok:
                    break
                message = prompts.build_fix_message(rep.problems, cfg.language)
        except LLMError as exc:
            error = str(exc)
            progress(f"[{func.name}] LLM xatosi: {error}")
        if best is None:
            progress(f"[{func.name}] Offline natijaga o'tilmoqda...")
            result, rep, off_attempts = _run_offline(parsed, func, analysis, cfg, progress)
            attempts += off_attempts
            best = (result, rep)
            engine = "offline"
        else:
            engine = model
        report = FunctionReport(func, parsed.style, engine, analysis, best[0], best[1], attempts,
                                usage=session.usage, error=error)

    report.metrics_before = metrics.measure(func.text)
    report.metrics_after = metrics.measure(report.result.c_code)
    report.elapsed_sec = round(time.time() - t0, 2)
    return report


def deobfuscate_text(text: str, cfg: AgentConfig, function: str | None = None,
                     progress: ProgressFn = _noop) -> tuple[ParsedInput, list[FunctionReport]]:
    """Matndagi barcha (yoki tanlangan) funksiyalarni deobfuskatsiya qiladi."""
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
    return parsed, [deobfuscate_function(parsed, f, cfg, progress) for f in funcs]
