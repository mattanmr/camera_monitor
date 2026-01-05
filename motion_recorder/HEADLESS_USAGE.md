# Headless Motion Recorder - Usage Guide

This guide explains how to run and manage the motion recorder in headless mode (without GUI windows).

## Starting the Headless Motion Recorder

### Method 1: Batch File (Recommended for Windows Task Scheduler)
```cmd
run_headless.bat
```

This will start the motion recorder without any OpenCV windows displayed.

### Method 2: Command Line
```cmd
C:\Users\mattan\Documents\python_projects\camera_monitor\.venv\Scripts\python.exe ^
  C:\Users\mattan\Documents\python_projects\camera_monitor\motion_recorder\motion_recording.py ^
  --no-windows
```

## Stopping the Headless Motion Recorder

### Method 1: Batch File (Recommended)
```cmd
stop_headless.bat
```

This sends a termination signal to gracefully shut down the recorder.

### Method 2: PowerShell Script
```powershell
powershell -ExecutionPolicy Bypass -File stop_headless.ps1
```

### Method 3: Windows Task Manager
1. Press `Ctrl + Shift + Esc` to open Task Manager
2. Find "python.exe" in the list
3. Right-click and select "End Task"

### Method 4: Command Line (taskkill)
```cmd
taskkill /IM python.exe /F
```

## Shutdown Mechanisms

The motion recorder supports three graceful shutdown methods:

### 1. **Ctrl+C (SIGINT)**
When running in a terminal, press `Ctrl+C` to stop.

### 2. **SIGTERM Signal**
External processes can send SIGTERM to the Python process:
```cmd
taskkill /PID <pid> /T
```

### 3. **Duration Parameter**
Run for a specific duration and auto-exit:
```cmd
python motion_recording.py --no-windows --duration 3600
```
(runs for 3600 seconds = 1 hour, then auto-stops)

## Logging

All activity is logged to stdout and can be redirected:

```cmd
run_headless.bat > motion_recorder.log 2>&1
```

This creates a log file with all output from the motion recorder.

## Windows Task Scheduler Integration

To run the motion recorder automatically on system startup:

1. Open **Task Scheduler** (taskschd.msc)
2. Create a new **Basic Task**
3. Set **Trigger** to "At startup"
4. Set **Action** to "Start a program"
   - Program: `C:\Users\mattan\Documents\python_projects\camera_monitor\motion_recorder\run_headless.bat`
5. Click **Finish**

To stop the task:
- Open Task Scheduler
- Right-click the motion recorder task
- Click **End** (or run stop_headless.bat)

## Advanced Options

Run with custom parameters:

```cmd
python motion_recording.py --no-windows --min-area 300 --thresh 20 --duration 7200
```

**Available parameters:**
- `--source 0`: Video source index (default 0)
- `--duration N`: Run for N seconds (default: run until stopped)
- `--min-area N`: Minimum contour area for motion (default 500)
- `--width N`: Resize frames for processing (e.g., 640)
- `--thresh N`: Motion detection threshold (default 15)
- `--min-frames N`: Consecutive frames needed for motion detection (default 2)
- `--no-windows`: Don't show OpenCV windows (for headless mode)

## Troubleshooting

### Application won't start
- Check that the virtual environment is activated
- Verify camera is connected and working
- Check log files in the `logs/` directory

### Application won't stop
- Use Task Manager (Ctrl+Shift+Esc) to force terminate
- Or run: `taskkill /IM python.exe /F`

### No video files created
- Check the `D:/motion_captures` directory has write permissions
- Verify camera is detecting motion (minimum area threshold is met)
- Check `logs/` directory for error messages

### Camera not found
- Verify USB camera is plugged in
- Try different `--source` values: 0, 1, 2, etc.
- Check Device Manager to confirm camera is detected


