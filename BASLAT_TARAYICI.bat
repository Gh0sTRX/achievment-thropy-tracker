@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" run.py --browser
) else (
  echo Ilk kurulum gerekiyor. KUR_WINDOWS.bat dosyasini calistir.
  pause
  exit /b 1
)
if errorlevel 1 pause
