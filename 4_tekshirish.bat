@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Avval 1_ornatish.bat faylini ishga tushiring.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m deobf_agent check
pause
