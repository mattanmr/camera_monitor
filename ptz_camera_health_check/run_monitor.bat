@echo off
setlocal

REM Change to script directory
cd /d "%~dp0"

REM Activate venv if present
IF EXIST .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) ELSE (
    echo [INFO] Creating venv...
    py -m venv .venv
    call .venv\Scripts\activate.bat
)

REM Ensure dependencies
python -m pip install --upgrade pip >nul 2>&1
IF EXIST requirements.txt (
    pip install -r requirements.txt
) ELSE (
    pip install opencv-python psutil
)

REM Run the monitor
python main.py

endlocal
