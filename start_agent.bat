@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Creating venv...
  python -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements-agent.txt
  .venv\Scripts\python.exe -m pip install -r job_scraper\requirements-volume.txt
)
if not exist logs mkdir logs
if not exist data mkdir data
if not exist backups mkdir backups
echo Starting opportunity agent (background loop). Keep PC awake for 24/7.
start "OpportunityAgent" /MIN .venv\Scripts\python.exe agent\cli.py start
echo Agent started. Logs: logs\agent.log
echo Dashboard: run_dashboard.bat
pause
