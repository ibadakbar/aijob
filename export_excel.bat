@echo off
cd /d "%~dp0"
echo Workbook is already the live store:
echo   data\opportunities.xlsx
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe agent\cli.py status
) else (
  python agent\cli.py status
)
explorer data
pause
