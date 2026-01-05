@echo off
REM Motion Recorder Process Manager
REM Allows you to check status, start, and stop the headless motion recorder

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=%SCRIPT_DIR%..\.venv\Scripts\python.exe"
set "MOTION_SCRIPT=%SCRIPT_DIR%motion_recording.py"

if "%1"=="" goto show_usage
if /i "%1"=="status" goto check_status
if /i "%1"=="start" goto start_process
if /i "%1"=="stop" goto stop_process
if /i "%1"=="restart" goto restart_process
goto show_usage

:check_status
echo Checking motion recorder status...
tasklist | findstr /I "python.exe" > nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] Motion recorder process is running
    tasklist | findstr /I "python.exe"
    exit /b 0
) else (
    echo [ERROR] Motion recorder process is NOT running
    exit /b 1
)

:start_process
echo Starting motion recorder (headless)...
start /MIN "" "%PYTHON_EXE%" "%MOTION_SCRIPT%" --no-windows
echo Motion recorder started. Use "manage.bat status" to verify.
exit /b 0

:stop_process
echo Stopping motion recorder...
taskkill /IM python.exe /F 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Motion recorder stopped successfully.
    exit /b 0
) else (
    echo No motion recorder process found.
    exit /b 1
)

:restart_process
echo Restarting motion recorder...
taskkill /IM python.exe /F 2>nul
timeout /t 2 /nobreak
start /MIN "" "%PYTHON_EXE%" "%MOTION_SCRIPT%" --no-windows
echo Motion recorder restarted.
exit /b 0

:show_usage
echo.
echo Motion Recorder Process Manager
echo Usage: manage.bat [command]
echo.
echo Commands:
echo   status    - Check if motion recorder is running
echo   start     - Start motion recorder in headless mode
echo   stop      - Stop motion recorder gracefully
echo   restart   - Restart motion recorder
echo.
echo Examples:
echo   manage.bat status
echo   manage.bat start
echo   manage.bat stop
echo   manage.bat restart
echo.
exit /b 0

