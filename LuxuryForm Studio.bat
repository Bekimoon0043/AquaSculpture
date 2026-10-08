@echo off
REM LuxuryForm Studio — single-process launcher.
REM Backend serves API + built UI on http://localhost:8100
cd /d "%~dp0backend"
start "" http://localhost:8100
python main.py
