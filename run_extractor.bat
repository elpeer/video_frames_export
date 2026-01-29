@echo off
echo Video Frame Extractor
echo =====================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if opencv-python is installed, if not install it
python -c "import cv2" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing opencv-python...
    pip install opencv-python
    if %errorlevel% neq 0 (
        echo Error: Failed to install opencv-python.
        pause
        exit /b 1
    )
)

echo Starting Video Frame Extractor...
python "%~dp0video_frame_extractor.py"

pause
