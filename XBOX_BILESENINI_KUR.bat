@echo off
cd /d "%~dp0"
py -3 -m pip install -r requirements-xbox.txt
if errorlevel 1 pause