# Camera Monitor (Windows 11)

Monitors a USB camera on Windows 11, periodically verifying that frames can be captured. Prioritizes the DirectShow backend for stability and falls back to Media Foundation if needed.

## Setup

```powershell
# From the project folder
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If you don't have `requirements.txt` yet:
```powershell
pip install opencv-python psutil
pip freeze | Out-File -Encoding UTF8 -FilePath requirements.txt
```

## Run

```powershell
.\.venv\Scripts\Activate.ps1
python .\main.py
```

Verification frames are saved in `monitor_frames`. Logs go to `logs/camera_monitor_win.log`.

## Status JSON

After each check, the app writes `logs/status.json` with:
- `timestamp`: ISO time of the last check
- `ok`: whether the last check succeeded
- `camera_index`: index used for capture
- `resolution`: width/height configuration
- `last_frame_path`: path to the last saved verification frame (if any)

This file is useful for external monitoring or dashboards.

## Tips for Windows 11
- Privacy: Settings → Privacy & security → Camera → allow desktop apps.
- Close apps that may hold the camera (Teams/Zoom/OBS/Camera app).
- Update camera drivers via Device Manager (Imaging devices).
- USB ports: prefer USB 3.0 ports; avoid hubs for large cameras.

## Configuration
Edit `CameraMonitor` parameters in `main.py`:
- `camera_index`: default `0`
- `width`/`height`: default `1280x720`
- `use_mjpg`: default `True` (MJPG often more reliable)
- `check_interval`: seconds between checks (default `5`)
- `frame_save_interval`: seconds between saved frames (default `3600`)

## Troubleshooting
- DShow warning "cannot capture by index": we probe indices automatically.
- MSMF errors `-1072875772`: typically unsupported media type; DShow usually works.
- If frames fail intermittently, increase retry count or interval.
- Ensure no other process holds the camera, and privacy settings permit access.
