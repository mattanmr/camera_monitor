import cv2
import time
import datetime
import os
import subprocess
import numpy as np


class CameraMonitor:
    """Monitor a USB camera on Windows 11 with robust backend selection and logging."""

    def __init__(
        self,
        camera_index: int = 0,
        log_file: str = "camera_monitor_win.log",
        save_dir: str = "monitor_frames",
        check_interval: int = 5,
        frame_save_interval: int = 900,#3600,
        width: int = 1280,
        height: int = 720,
        use_mjpg: bool = True,
    ) -> None:
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.camera_index = camera_index
        self.log_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, log_file)
        self.save_dir = os.path.join(self.base_dir, save_dir)
        self.check_interval = check_interval
        self.frame_save_interval = frame_save_interval
        self.width = width
        self.height = height
        self.use_mjpg = use_mjpg
        self.last_saved = 0

        os.makedirs(self.save_dir, exist_ok=True)

    def log(self, msg):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        with open(self.log_file, "a") as f:
            f.write(line + "\n")

    def write_status(self, ok: bool, last_frame_path: str | None = None, backend: str | None = None) -> None:
        # Load existing status (preserve last_frame_path if caller doesn't provide one)
        try:
            import json
            status_path = os.path.join(self.log_dir, "status.json")
            status = {}
            if os.path.exists(status_path):
                try:
                    with open(status_path, "r", encoding="utf-8") as fp:
                        status = json.load(fp)
                except Exception:
                    status = {}

            # Update fields
            status["timestamp"] = datetime.datetime.now().isoformat(timespec="seconds")
            status["ok"] = bool(ok)
            status["camera_index"] = self.camera_index
            status["resolution"] = {"width": self.width, "height": self.height}
            # Only overwrite backend if provided; else preserve existing or set default
            if backend is not None:
                status["backend"] = backend
            else:
                status.setdefault("backend", "DSHOW/MSMF")

            # Preserve last_frame_path unless a non-None value is explicitly provided
            if last_frame_path is not None:
                status["last_frame_path"] = last_frame_path
            else:
                status.setdefault("last_frame_path", "")

            with open(status_path, "w", encoding="utf-8") as fp:
                json.dump(status, fp, indent=2)
        except Exception:
            # Don't let status write failures crash monitoring
            pass
    
    def usb_camera_connected(self) -> bool:
        """Return True if Windows reports any imaging device attached.

        Uses PowerShell CIM (reliable on Windows 11) and falls back to WMIC if needed.
        """
        ps_cmd = (
            "Get-CimInstance Win32_PnPEntity | "
            "Where-Object { $_.PNPClass -eq 'Image' -or $_.Name -match 'Camera|USB' } | "
            "Select-Object -ExpandProperty Name"
        )
        try:
            output = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                stderr=subprocess.DEVNULL,
            ).decode(errors="ignore")
            if any(len(line.strip()) > 0 for line in output.splitlines()):
                return True
        except Exception:
            # Fallback to WMIC for older environments
            try:
                output = subprocess.check_output(
                    "wmic path Win32_PnPEntity get Name", shell=True, stderr=subprocess.DEVNULL
                ).decode(errors="ignore")
                for line in output.splitlines():
                    if "Camera" in line or "USB" in line:
                        return True
            except Exception:
                pass
        # Fail-open so monitoring continues; capture attempt will confirm
        return True
    
    def is_black_frame(self, frame, *, mean_thresh=12.0, pct_dark_thresh=0.98, std_thresh=3.0, edge_thresh=20):
        """Return (is_black, reasons) where reasons explains which checks failed.

        Heuristics used (combination improves robustness):
        - mean pixel intensity below mean_thresh
        - fraction of pixels with value <= mean_thresh is above pct_dark_thresh
        - standard deviation across pixels below std_thresh (nearly constant image)
        - edge pixel count (Canny) below edge_thresh
        """
        reasons = {}
        if frame is None:
            reasons['none'] = True
            return True, reasons

        # Ensure numpy array
        try:
            arr = np.asarray(frame)
        except Exception:
            reasons['not_array'] = True
            return True, reasons

        if arr.size == 0:
            reasons['empty'] = True
            return True, reasons

        # Compute mean on grayscale equivalent
        if arr.ndim == 3 and arr.shape[2] == 3:
            gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        else:
            gray = arr if arr.ndim == 2 else cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)

        mean = float(np.mean(gray))
        reasons['mean'] = mean

        pct_dark = float(np.count_nonzero(gray <= mean_thresh)) / gray.size
        reasons['pct_dark'] = pct_dark

        std = float(np.std(gray))
        reasons['std'] = std

        # Edge-based check: if very few edges, likely black/blank
        try:
            edges = cv2.Canny(gray, 50, 150)
            edge_count = int(np.count_nonzero(edges))
        except Exception:
            edge_count = 9999
        reasons['edge_count'] = edge_count

        is_black = (
            mean < mean_thresh
            or pct_dark >= pct_dark_thresh
            or std < std_thresh
            or edge_count <= edge_thresh
        )

        return bool(is_black), reasons

    def check_camera(self):
        # Check if USB device is present (Windows)
        if not self.usb_camera_connected():
            self.log("ERROR: USB camera not detected by OS")
            return False

        # DShow-first strategy, then MSMF, with index probing
        # Use a local working_index to avoid permanently switching on transient failures
        cap = None
        opened = False
        used_backend = "UNKNOWN"
        working_index = self.camera_index

        dshow = getattr(cv2, "CAP_DSHOW", None)
        if dshow is not None:
            self.log(f"INFO: Trying DirectShow (CAP_DSHOW) on index {working_index}")
            cap = cv2.VideoCapture(working_index, dshow)
            if not cap.isOpened():
                self.log(f"WARN: DShow failed on index {working_index}; probing indices 0-5 with DShow")
                probe_idx = None
                for idx in range(0, 6):
                    # Skip the original index since we just tried it
                    if idx == self.camera_index:
                        continue
                    probe = cv2.VideoCapture(idx, dshow)
                    if probe.isOpened():
                        self.log(f"INFO: DShow found camera at index {idx} (but preferring configured index {self.camera_index})")
                        probe_idx = idx
                        probe.release()
                        break
                    probe.release()
                # Only use probe_idx if original index failed; don't permanently switch
                if probe_idx is not None:
                    self.log(f"WARN: Using fallback index {probe_idx} since configured index {self.camera_index} unavailable")
                    working_index = probe_idx
                    cap = cv2.VideoCapture(working_index, dshow)
            if cap.isOpened():
                opened = True
                used_backend = "DSHOW"

        if not opened:
            msmf = getattr(cv2, "CAP_MSMF", None)
            if msmf is not None:
                self.log(f"INFO: Trying Media Foundation (CAP_MSMF) on index {working_index}")
                cap = cv2.VideoCapture(working_index, msmf)
                if not cap.isOpened():
                    self.log(f"WARN: MSMF failed on index {working_index}; probing indices 0-5 with MSMF")
                    probe_idx = None
                    for idx in range(0, 6):
                        # Skip the original index since we just tried it
                        if idx == self.camera_index:
                            continue
                        probe = cv2.VideoCapture(idx, msmf)
                        if probe.isOpened():
                            self.log(f"INFO: MSMF found camera at index {idx} (but preferring configured index {self.camera_index})")
                            probe_idx = idx
                            probe.release()
                            break
                        probe.release()
                    # Only use probe_idx if original index failed; don't permanently switch
                    if probe_idx is not None:
                        self.log(f"WARN: Using fallback index {probe_idx} since configured index {self.camera_index} unavailable")
                        working_index = probe_idx
                        cap = cv2.VideoCapture(working_index, msmf)
                if cap.isOpened():
                    opened = True
                    used_backend = "MSMF"

        if not opened or cap is None:
            self.log("ERROR: Could not open camera via DShow or MSMF")
            return False

        # Set properties to avoid bad auto-negotiation
        try:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            if self.use_mjpg:
                fourcc = cv2.VideoWriter_fourcc(*"MJPG")
                cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        except Exception:
            pass

        # Warmup and read loop: allow camera auto-exposure to settle and avoid black frames
        frame = None
        ret = False
        # short warmup reads
        try:
            for _ in range(15):
                cap.read()
                time.sleep(0.01)
        except Exception:
            pass

        # Try multiple attempts and verify frame is not black using several heuristics
        for attempt in range(6):
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.2)
                continue
            try:
                is_black, reasons = self.is_black_frame(frame)
            except Exception:
                is_black, reasons = False, {'error': 'is_black_check_failed'}
            if is_black:
                # Too dark/blank; let camera adjust and retry
                self.log(f"WARN: Captured frame considered black; reasons={reasons}; retrying ({attempt+1}/6)")
                time.sleep(0.3)
                continue
            # good frame
            break

        cap.release()

        if not ret or frame is None:
            self.log("ERROR: Failed to read frame")
            # preserve backend info in status; report configured index (self.camera_index)
            self.write_status(False, None, backend=used_backend)
            return False

        self.log(f"OK: Frame captured from index {working_index}")

        # Hourly verification frame (or configured interval)
        now = time.time()
        if now - self.last_saved >= self.frame_save_interval:
            filename = os.path.join(
                self.save_dir,
                datetime.datetime.now().strftime("%Y%m%d_%H%M%S.jpg")
            )
            try:
                cv2.imwrite(filename, frame)
                self.log(f"Saved verification frame from index {working_index}: {filename}")
                self.last_saved = now
                self.write_status(True, filename, backend=used_backend)
            except Exception:
                self.log("WARN: Failed to save verification frame")
                # write status but keep prior saved frame path
                self.write_status(True, None, backend=used_backend)
        else:
            # don't overwrite last_frame_path with empty value; preserve prior
            self.write_status(True, None, backend=used_backend)

        return True

    def set_pan(self, value: int) -> bool:
        """Set pan position (-180 to 180 degrees, camera-dependent).

        Args:
            value: Pan angle in degrees (camera-specific range may vary)

        Returns:
            True if property was set successfully, False otherwise.
        """
        try:
            cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(self.camera_index, cv2.CAP_MSMF)

            if not cap.isOpened():
                self.log("WARN: Could not open camera to set pan")
                return False

            result = cap.set(cv2.CAP_PROP_PAN, float(value))
            actual = cap.get(cv2.CAP_PROP_PAN)
            cap.release()

            if result or actual != -1:
                self.log(f"Pan set to {value} (actual: {actual})")
                return True
            else:
                self.log(f"WARN: Could not set pan to {value} (camera may not support PTZ)")
                return False
        except Exception as e:
            self.log(f"ERROR: Failed to set pan: {e}")
            return False

    def set_tilt(self, value: int) -> bool:
        """Set tilt position (-180 to 180 degrees, camera-dependent).

        Args:
            value: Tilt angle in degrees (camera-specific range may vary)

        Returns:
            True if property was set successfully, False otherwise.
        """
        try:
            cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(self.camera_index, cv2.CAP_MSMF)

            if not cap.isOpened():
                self.log("WARN: Could not open camera to set tilt")
                return False

            result = cap.set(cv2.CAP_PROP_TILT, float(value))
            actual = cap.get(cv2.CAP_PROP_TILT)
            cap.release()

            if result or actual != -1:
                self.log(f"Tilt set to {value} (actual: {actual})")
                return True
            else:
                self.log(f"WARN: Could not set tilt to {value} (camera may not support PTZ)")
                return False
        except Exception as e:
            self.log(f"ERROR: Failed to set tilt: {e}")
            return False

    def set_zoom(self, value: int) -> bool:
        """Set zoom level (typically 0-10 or 100-400, camera-dependent).

        Args:
            value: Zoom value (camera-specific range may vary)

        Returns:
            True if property was set successfully, False otherwise.
        """
        try:
            cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(self.camera_index, cv2.CAP_MSMF)

            if not cap.isOpened():
                self.log("WARN: Could not open camera to set zoom")
                return False

            result = cap.set(cv2.CAP_PROP_ZOOM, float(value))
            actual = cap.get(cv2.CAP_PROP_ZOOM)
            cap.release()

            if result or actual != -1:
                self.log(f"Zoom set to {value} (actual: {actual})")
                return True
            else:
                self.log(f"WARN: Could not set zoom to {value} (camera may not support PTZ)")
                return False
        except Exception as e:
            self.log(f"ERROR: Failed to set zoom: {e}")
            return False

    def get_ptz_position(self) -> dict:
        """Get current PTZ position if supported by camera.

        Returns:
            Dictionary with keys 'pan', 'tilt', 'zoom' and their current values,
            or 'error' key if camera cannot be opened.
        """
        try:
            cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(self.camera_index, cv2.CAP_MSMF)

            if not cap.isOpened():
                return {"error": "Could not open camera"}

            position = {
                "pan": float(cap.get(cv2.CAP_PROP_PAN)),
                "tilt": float(cap.get(cv2.CAP_PROP_TILT)),
                "zoom": float(cap.get(cv2.CAP_PROP_ZOOM)),
            }
            cap.release()

            self.log(f"PTZ Position: pan={position['pan']}, tilt={position['tilt']}, zoom={position['zoom']}")
            return position
        except Exception as e:
            self.log(f"ERROR: Failed to get PTZ position: {e}")
            return {"error": str(e)}

    def reset_ptz(self) -> bool:
        """Reset PTZ to home/center position (0, 0, 0).

        Returns:
            True if reset was successful, False otherwise.
        """
        try:
            cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(self.camera_index, cv2.CAP_MSMF)

            if not cap.isOpened():
                self.log("WARN: Could not open camera to reset PTZ")
                return False

            success = True
            success &= bool(cap.set(cv2.CAP_PROP_PAN, 0.0))
            success &= bool(cap.set(cv2.CAP_PROP_TILT, 0.0))
            success &= bool(cap.set(cv2.CAP_PROP_ZOOM, 0.0))

            cap.release()

            if success:
                self.log("PTZ reset to home position (0, 0, 0)")
            else:
                self.log("WARN: Could not reset PTZ (camera may not support PTZ or partial support)")

            return bool(success)
        except Exception as e:
            self.log(f"ERROR: Failed to reset PTZ: {e}")
            return False

if __name__ == "__main__":
    monitor = CameraMonitor()
    monitor.log("=== Windows Camera Monitor Started ===")
    try:
        while True:
            ok = monitor.check_camera()
            if not ok:
                monitor.write_status(False, None)
                monitor.log("WARN: Check failed; will retry after interval")
            time.sleep(monitor.check_interval)
    except KeyboardInterrupt:
        monitor.log("=== Windows Camera Monitor Stopped ===")
    except Exception as e:
        monitor.log(f"FATAL ERROR: {e}")
