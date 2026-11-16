@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   deobf-agent: API kalitini kiritish
echo ============================================================
echo Qaysi model uchun kalit kiritasiz?
echo   1 - DeepSeek (kalit: platform.deepseek.com)  [tavsiya: arzon va tez]
echo   2 - Claude   (kalit: console.anthropic.com)
set "CHOICE="
set /p "CHOICE=Tanlang (1 yoki 2, Enter = 1): "
set "NAME=DEEPSEEK_API_KEY"
set "MODEL=deepseek"
if "%CHOICE%"=="2" (
  set "NAME=ANTHROPIC_API_KEY"
  set "MODEL=sonnet"
)
echo.
echo Kalitni shu yerga joylang. Joylash: sichqonchaning O'NG tugmasi yoki Ctrl+V. Keyin Enter bosing.
echo DIQQAT: mavjud .env fayli qayta yoziladi (u faqat tanlangan kalitni saqlaydi).
echo.
set "KEY="
set /p "KEY=Kalit: "
if "%KEY%"=="" (
  echo Kalit kiritilmadi.
  pause
  exit /b 1
)
>.env echo %NAME%=%KEY%
echo.
echo .env fayli yaratildi. Endi kalit serverda tekshiriladi (bepul)...
echo.
".venv\Scripts\python.exe" -m deobf_agent check -m %MODEL%
pause
