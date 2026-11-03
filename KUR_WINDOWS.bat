@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto install
where py >nul 2>nul
if not errorlevel 1 (
  py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"
  if errorlevel 1 goto python_missing
  py -3 -m venv .venv
) else (
  where python >nul 2>nul
  if errorlevel 1 goto python_missing
  python -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"
  if errorlevel 1 goto python_missing
  python -m venv .venv
)
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install -r requirements-platforms.txt
if errorlevel 1 goto failed
echo Kurulum tamamlandi. Uygulama aciliyor...
call BASLAT_WINDOWS.bat
exit /b 0
:python_missing
echo Python 3.11 veya uzeri bulunamadi.
echo Python gerektirmeyen Setup.exe paketini kullanabilir veya python.org adresinden Python kurabilirsin.
pause
exit /b 1
:failed
echo Kurulum tamamlanamadi. Yukaridaki hata mesajini ve internet baglantini kontrol et.
pause
exit /b 1
