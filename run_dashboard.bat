@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  python -m venv .venv
  .venv\Scripts\python.exe -m pip install -r requirements-agent.txt
)
.venv\Scripts\python.exe -m streamlit run agent\dashboard\app.py --server.headless true
