"""Tashqi dasturlarni (gcc va test dasturi) cheklangan sharoitda ishga tushirish.

Vosita foydalanuvchi bergan kodni kompilyatsiya qiladi va ishga tushiradi — bu uning asosiy ishi
(differensial test). O'z kompyuteringizda bu xavfsiz, chunki kodni o'zingiz berasiz. Internetga
chiqarilganda esa kodni boshqa odamlar yuborishi mumkin, shuning uchun himoya qatlamlari kerak:

  * muhit tozalanadi — ishga tushirilgan dasturga faqat PATH/LANG kabi zarur o'zgaruvchilar beriladi,
    hech qanday kalit yoki maxfiy qiymat uzatilmaydi;
  * resurs chegaralari (Linux/macOS): protsessor vaqti, xotira, yoziladigan fayl hajmi;
    public rejimda jarayonlar soni va ochiq fayllar soni ham cheklanadi;
  * vaqt tugasa butun jarayonlar guruhi to'xtatiladi (dastur yaratgan bola jarayonlar ham);
  * ALOHIDA FOYDALANUVCHI (DEOBF_SANDBOX_UID): server root bo'lsa, tekshirilayotgan kod boshqa, huquqsiz
    foydalanuvchi nomidan ishlaydi. Shunda u serverning muhit o'zgaruvchilarini (`/proc/<pid>/environ`, ya'ni API
    kalitni) va xotirasini o'qiy olmaydi. Bu resurs chegaralaridan farqli ravishda HAQIQIY ajratish.

Public rejimda (DEOBF_PUBLIC=1) kod standart holatda umuman ishga tushirilmaydi (native_allowed). Operator uni faqat
kirish paroli (DEOBF_ACCESS_CODE) bilan birga yoqishi mumkin (configure()), server kaliti ishlatilsa — faqat alohida
foydalanuvchi ishlayotganini tekshirgandan keyin. Batafsil: docs/04_internetga_chiqarish.md.
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass


def _flag(name: str) -> bool:
    return os.environ.get(name, "") not in ("", "0", "false")


def _tri(name: str):
    """None — o'rnatilmagan (avtomatik); True/False — operator aniq aytgan."""
    v = os.environ.get(name, "").strip().lower()
    return None if v == "" else v not in ("0", "false", "no")


PUBLIC = _flag("DEOBF_PUBLIC")
# Kirish kodi (DEOBF_ACCESS_CODE) o'rnatilgan bo'lsa, quyidagi ikkisi AVTOMATIK yoqiladi (o'chirish uchun "0" yozing):
NATIVE = _tri("DEOBF_NATIVE")                  # kodni ishga tushirish (to'liq tekshiruv)
USE_SERVER_KEY = _tri("DEOBF_USE_SERVER_KEY")  # kirgan foydalanuvchi uchun serverdagi ANTHROPIC_API_KEY
SANDBOX_UID = int(os.environ.get("DEOBF_SANDBOX_UID", "0") or 0)       # 0 = ajratish yo'q


def native_allowed() -> bool:
    """Foydalanuvchi kodini kompilyatsiya qilish va ishga tushirishga ruxsat bormi?"""
    return not PUBLIC or bool(NATIVE)


def _drop_active() -> bool:
    return bool(SANDBOX_UID) and hasattr(os, "geteuid") and os.geteuid() == 0


def configure(has_access_code: bool, log=print) -> None:
    """Public rejimdagi xavfli kombinatsiyalarni o'chiradi (app ishga tushganda chaqiriladi).

    * kodni ishga tushirish faqat kirish paroli bor bo'lsa mumkin (begonalar kod yubora olmasin);
    * server kaliti ishlatilsa — kod alohida foydalanuvchi nomidan ishlashi SINALADI; sinov o'tmasa, kod ishga
      tushirilmaydi (kalit o'g'irlanmasligi uchun).
    """
    global NATIVE, USE_SERVER_KEY
    if has_access_code:                                # kirish kodi bor: o'rnatilmagan bayroqlar avtomatik yoqiladi
        USE_SERVER_KEY = True if USE_SERVER_KEY is None else USE_SERVER_KEY
        NATIVE = True if NATIVE is None else NATIVE
    NATIVE, USE_SERVER_KEY = bool(NATIVE), bool(USE_SERVER_KEY)
    if PUBLIC and NATIVE and not has_access_code:
        NATIVE = False
        log("OGOHLANTIRISH: DEOBF_NATIVE kirish parolisiz ishlamaydi — kod ishga tushirilmaydi.")
    if PUBLIC and NATIVE and USE_SERVER_KEY and not selftest_isolation():
        NATIVE = False
        log("OGOHLANTIRISH: kod alohida foydalanuvchi nomidan ishlay olmadi (DEOBF_SANDBOX_UID + root kerak) — "
            "server kaliti himoyasi uchun kod ishga tushirilmaydi.")


def selftest_isolation() -> bool:
    """Bola jarayon haqiqatan boshqa foydalanuvchi nomidan ishlaydimi va serverning muhitini o'qiy olmaydimi?"""
    if not _drop_active():
        return False
    me = run(["id", "-u"], timeout=10)
    leak = run(["sh", "-c", f"cat /proc/{os.getpid()}/environ >/dev/null 2>&1 && echo LEAK || echo SAFE"], timeout=10)
    return me.stdout.strip() == str(SANDBOX_UID) and leak.stdout.strip() == "SAFE"


@contextlib.contextmanager
def workdir(prefix: str):
    """Vaqtincha ish papkasi. Kod alohida foydalanuvchi nomidan ishlasa, papka unga ham ochiq bo'ladi."""
    with tempfile.TemporaryDirectory(prefix=prefix) as tmp:
        if _drop_active():
            os.chmod(tmp, 0o777)
        yield tmp


_KEEP_ENV = ("PATH", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT", "SystemRoot", "WINDIR", "HOME")


@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


def clean_env() -> dict[str, str]:
    """Ishga tushiriladigan dastur uchun minimal muhit (kalitlar va maxfiy qiymatlarsiz)."""
    env = {k: v for k, v in os.environ.items() if k in _KEEP_ENV}
    if _drop_active():
        env["HOME"] = "/tmp"           # huquqsiz foydalanuvchi root'ning uy papkasini o'qiy olmaydi
    return env


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
        if _drop_active():                               # eng oxirida: root huquqlarini tashlaymiz (qaytib bo'lmaydi)
            os.setgroups([])
            os.setgid(SANDBOX_UID)
            os.setuid(SANDBOX_UID)
    return apply


MAX_OUTPUT = 1_000_000          # stdout/stderr dan ko'pi bilan shuncha bayt o'qiladi


def _kill_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        proc.kill()


def run(cmd: list[str], timeout: float, cpu_sec: int = 30, mem_mb: int = 1024, cwd: str | None = None) -> RunResult:
    """cmd ni chegaralar bilan ishga tushiradi. Vaqt tugasa — butun guruh to'xtatiladi.

    Chiqish vaqtinchalik fayllarga yoziladi (RLIMIT_FSIZE ularni cheklaydi), shuning uchun cheksiz chiqaradigan
    dastur serverning xotirasini to'ldira olmaydi. Dastur tugagach, u qoldirgan bola jarayonlar ham o'ldiriladi.
    """
    posix = os.name == "posix"
    with tempfile.TemporaryFile() as fout, tempfile.TemporaryFile() as ferr:
        proc = subprocess.Popen(cmd, stdout=fout, stderr=ferr, stdin=subprocess.DEVNULL, cwd=cwd, env=clean_env(),
                                preexec_fn=_limits(cpu_sec, mem_mb) if posix else None)
        timed_out = False
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            if posix:
                _kill_group(proc)
            elif timed_out:
                proc.kill()
            proc.wait()
        fout.seek(0)
        ferr.seek(0)
        out, err = fout.read(MAX_OUTPUT), ferr.read(MAX_OUTPUT)
    return RunResult(proc.returncode, out.decode("utf-8", "replace"), err.decode("utf-8", "replace"), timed_out)
