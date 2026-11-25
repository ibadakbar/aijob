@echo off
cd /d "%~dp0"
call start_agent.bat
start "OpportunityDashboard" cmd /c run_dashboard.bat
