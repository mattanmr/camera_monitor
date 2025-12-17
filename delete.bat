REM simple batch file to delete __pycache__, logs, monitor_frames and monitor_videos folders

@echo off
echo Deleting __pycache__, logs, monitor_frames and monitor_videos folders...

REM verify that user wants to proceed
set /p confirm="Are you sure you want to delete these folders? (y/n): "
if /i not "%confirm%"=="y" (
    echo Deletion cancelled.
    goto end
)
REM make sure to delete the folder only in the current directory
if exist "__pycache__" (
    rmdir /s /q "__pycache__"
    echo Deleted __pycache__ folder.
) else (
    echo __pycache__ folder not found.
)
if exist "logs" (
    rmdir /s /q "logs"
    echo Deleted logs folder.
) else (
    echo logs folder not found.
)
if exist "monitor_frames" (
    rmdir /s /q "monitor_frames"
    echo Deleted monitor_frames folder.
) else (
    echo monitor_frames folder not found.
)
if exist "monitor_videos" (
    rmdir /s /q "monitor_videos"
    echo Deleted monitor_videos folder.
) else (
    echo monitor_videos folder not found.
)
:end
echo Done.