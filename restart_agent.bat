@echo off
cd /d "%~dp0"
call stop_agent.bat
timeout /t 3 >nul
call start_agent.bat
