@echo off
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe agent\cli.py backup
) else (
  python agent\cli.py backup
)
pause
