@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   deobf-agent: o'rnatish (bir marta bajariladi)
echo ============================================================
where python >nul 2>nul
if errorlevel 1 (
  echo XATO: Python topilmadi. python.org dan o'rnating va o'rnatishda
  echo "Add python.exe to PATH" belgisini qo'ying. Keyin bu faylni qayta ishga tushiring.
  pause
  exit /b 1
)
python --version
if not exist ".venv\Scripts\python.exe" (
  echo Virtual muhit yaratilmoqda...
  python -m venv .venv
  if errorlevel 1 (
    echo XATO: virtual muhit yaratilmadi.
    pause
    exit /b 1
  )
)
echo Kutubxonalar o'rnatilmoqda, 1-3 daqiqa kuting...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -e ".[dev]"
if errorlevel 1 (
  echo XATO: kutubxonalarni o'rnatishda muammo. Internet aloqasini tekshiring.
  pause
  exit /b 1
)
echo.
echo O'rnatish tugadi. Keyingi qadam: 2_kalit_kiritish.bat
pause
