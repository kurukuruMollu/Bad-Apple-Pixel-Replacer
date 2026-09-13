@echo off
chcp 65001 >nul
cd /d %~dp0

echo ===============================
echo  Creating venv and installing packages
echo ===============================

if exist venv (
    echo venv folder already exists.
    echo If you want to reinstall, delete the venv folder first and run this again.
    pause
    exit /b
)

python -m venv venv
if errorlevel 1 (
    echo Failed to create venv.
    echo Check that Python is installed and added to PATH.
    pause
    exit /b
)

call venv\Scripts\activate.bat

python -m pip install --upgrade pip
pip install PySide6 opencv-python pillow imageio imageio-ffmpeg numpy

echo.
echo ===============================
echo  Setup complete. You can now run run.bat
echo ===============================
pause
