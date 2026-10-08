"""Tashqi dasturlarni (gcc va test dasturi) cheklangan sharoitda ishga tushirish.

Vosita foydalanuvchi bergan kodni kompilyatsiya qiladi va ishga tushiradi — bu uning asosiy ishi
(differensial test). O'z kompyuteringizda bu xavfsiz, chunki kodni o'zingiz berasiz. Internetga
chiqarilganda esa kodni begona odamlar beradi, shuning uchun himoya qatlamlari kerak:

  * muhit tozalanadi — ishga tushirilgan dasturga faqat PATH/LANG kabi zarur o'zgaruvchilar beriladi,
    hech qanday kalit yoki maxfiy qiymat uzatilmaydi;
  * resurs chegaralari (Linux/macOS): protsessor vaqti, xotira, yoziladigan fayl hajmi;
    public rejimda jarayonlar soni va ochiq fayllar soni ham cheklanadi;
  * vaqt tugasa butun jarayonlar guruhi to'xtatiladi (dastur yaratgan bola jarayonlar ham).

Eng muhim himoya baribir tashqarida: server konteynerda, oddiy (root bo'lmagan) foydalanuvchi
nomidan ishlaydi va serverda hech qanday maxfiy kalit saqlanmaydi (docs/04_internetga_chiqarish.md).
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from dataclasses import dataclass

PUBLIC = os.environ.get("DEOBF_PUBLIC", "") not in ("", "0", "false")
_KEEP_ENV = ("PATH", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT", "SystemRoot", "WINDIR", "HOME")


@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


def clean_env() -> dict[str, str]:
    """Ishga tushiriladigan dastur uchun minimal muhit (kalitlar va maxfiy qiymatlarsiz)."""
    return {k: v for k, v in os.environ.items() if k in _KEEP_ENV}


def _limits(cpu_sec: int, mem_mb: int):
    def apply() -> None:
        import resource

        os.setsid()                                      # alohida jarayonlar guruhi
        limits = [(resource.RLIMIT_CPU, cpu_sec), (resource.RLIMIT_FSIZE, 16 * 1024 * 1024)]
        if hasattr(resource, "RLIMIT_AS") and sys.platform.startswith("linux"):
            limits.append((resource.RLIMIT_AS, mem_mb * 1024 * 1024))
        if PUBLIC:
            limits += [(resource.RLIMIT_NPROC, 64), (resource.RLIMIT_NOFILE, 64)]
        for res, value in limits:
            try:
                resource.setrlimit(res, (value, value))
            except (ValueError, OSError):
                pass
    return apply


def run(cmd: list[str], timeout: float, cpu_sec: int = 30, mem_mb: int = 1024, cwd: str | None = None) -> RunResult:
    """cmd ni chegaralar bilan ishga tushiradi. Vaqt tugasa — butun guruh to'xtatiladi."""
    posix = os.name == "posix"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=clean_env(),
                            preexec_fn=_limits(cpu_sec, mem_mb) if posix else None)
    try:
        out, err = proc.communicate(timeout=timeout)
        timed_out = False
    except subprocess.TimeoutExpired:
        if posix:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                proc.kill()
        else:
            proc.kill()
        out, err = proc.communicate()
        timed_out = True
    return RunResult(proc.returncode, out.decode("utf-8", "replace"), err.decode("utf-8", "replace"), timed_out)
