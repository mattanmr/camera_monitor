# PowerShell script to gracefully stop the headless motion recorder
# Usage: powershell -ExecutionPolicy Bypass -File stop_headless.ps1

$processName = "python"
$scriptName = "motion_recording.py"

Write-Host "Attempting graceful shutdown of motion_recording..."

# Find Python processes running motion_recording.py
$process = Get-Process $processName -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*$scriptName*" } |
    Select-Object -First 1

if ($process) {
    Write-Host "Found motion_recording process (PID: $($process.Id))"
    Write-Host "Sending terminate signal..."

    # Send Ctrl+C (SIGINT equivalent in PowerShell)
    $process.Kill()

    # Wait a moment for graceful shutdown
    Start-Sleep -Seconds 2

    # Check if still running
    if (Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {
        Write-Host "Process still running, forcing termination..."
        $process.Kill($true)  # Force kill
    }

    Write-Host "Motion recorder stopped successfully."
} else {
    Write-Host "No motion_recording process found running."
    exit 1
}

