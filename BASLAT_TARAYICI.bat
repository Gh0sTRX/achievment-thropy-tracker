@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
 py -3 run.py --browser
) else (
 python run.py --browser
)
if errorlevel 1 pause