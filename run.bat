@echo off
chcp 65001 >nul
cd /d %~dp0

if not exist venv (
    echo venv not found. Please run initial_setting.bat first.
    pause
    exit /b
)

call venv\Scripts\activate.bat
python main.py
pause
