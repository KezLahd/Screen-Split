@echo off
cd /d "%~dp0"
start /b /wait "" pythonw screen_app_debug.pyw >nul 2>&1
exit 