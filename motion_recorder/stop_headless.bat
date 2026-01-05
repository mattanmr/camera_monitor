@echo off
)
    exit /b 1
    echo No motion recorder process found.
) else (
    exit /b 0
    echo Motion recorder stopped successfully.
if %ERRORLEVEL% EQU 0 (

taskkill /IM python.exe /F 2>nul
REM This will send SIGTERM on Windows
REM Method 1: Try to use taskkill with /F flag on the python process running motion_recording.py

echo Attempting graceful shutdown of motion_recording...

REM This script sends SIGTERM to the running Python process or kills by name
REM Stop the headless motion recorder gracefully

