@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   deobf-agent: Claude API kalitini kiritish
echo ============================================================
echo console.anthropic.com saytidan olingan kalitni shu yerga joylang.
echo Joylash: sichqonchaning O'NG tugmasi yoki Ctrl+V. Keyin Enter bosing.
echo DIQQAT: mavjud .env fayli qayta yoziladi.
echo.
set "KEY="
set /p "KEY=Kalit: "
if "%KEY%"=="" (
  echo Kalit kiritilmadi.
  pause
  exit /b 1
)
>.env echo ANTHROPIC_API_KEY=%KEY%
echo.
echo .env fayli yaratildi. Endi kalit Claude serverida tekshiriladi (bepul)...
echo.
".venv\Scripts\python.exe" -m deobf_agent check -m haiku
pause
