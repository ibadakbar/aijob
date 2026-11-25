@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe agent\cli.py stop
) else (
  python agent\cli.py stop
)
echo Stop signal sent.
timeout /t 2 >nul
