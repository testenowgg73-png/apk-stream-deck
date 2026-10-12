@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 ultron_pc.py
) else (
  python ultron_pc.py
)
if errorlevel 1 pause
