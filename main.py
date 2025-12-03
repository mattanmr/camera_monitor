import cv2
import time
import datetime
import os
import psutil
import subprocess



class CameraMonitor:
    """Monitor a USB camera on Windows 11 with robust backend selection and logging."""

    def __init__(
        self,
        camera_index: int = 0,
        log_file: str = "camera_monitor_win.log",
        save_dir: str = "monitor_frames",
        check_interval: int = 5,
        frame_save_interval: int = 3600,
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
    
    def check_camera(self):
        # Check if USB device is present (Windows)
        if not self.usb_camera_connected():
            self.log("ERROR: USB camera not detected by OS")
            return False

        # DShow-first strategy, then MSMF, with index probing
        cap = None
        opened = False

        dshow = getattr(cv2, "CAP_DSHOW", None)
        if dshow is not None:
            self.log(f"INFO: Trying DirectShow (CAP_DSHOW) on index {self.camera_index}")
            cap = cv2.VideoCapture(self.camera_index, dshow)
            if not cap.isOpened():
                self.log("WARN: DShow failed; probing indices 0-5 with DShow")
                for idx in range(0, 6):
                    probe = cv2.VideoCapture(idx, dshow)
                    if probe.isOpened():
                        self.log(f"INFO: DShow found camera at index {idx}")
                        self.camera_index = idx
                        cap = probe
                        opened = True
                        break
                    probe.release()
            else:
                opened = True

        if not opened:
            msmf = getattr(cv2, "CAP_MSMF", None)
            if msmf is not None:
                self.log(f"INFO: Trying Media Foundation (CAP_MSMF) on index {self.camera_index}")
                cap = cv2.VideoCapture(self.camera_index, msmf)
                if not cap.isOpened():
                    self.log("WARN: MSMF failed; probing indices 0-5 with MSMF")
                    for idx in range(0, 6):
                        probe = cv2.VideoCapture(idx, msmf)
                        if probe.isOpened():
                            self.log(f"INFO: MSMF found camera at index {idx}")
                            self.camera_index = idx
                            cap = probe
                            opened = True
                            break
                        probe.release()
                else:
                    opened = True

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

        # Short retry loop in case the stream is busy
        frame = None
        ret = False
        for attempt in range(3):
            ret, frame = cap.read()
            if ret and frame is not None:
                break
            time.sleep(0.2)
        cap.release()

        if not ret or frame is None:
            self.log("ERROR: Failed to read frame")
            return False

        self.log("OK: Frame captured")

        # Hourly verification frame
        now = time.time()
        if now - self.last_saved >= self.frame_save_interval:
            filename = os.path.join(
                self.save_dir,
                datetime.datetime.now().strftime("%Y%m%d_%H%M%S.jpg")
            )
            cv2.imwrite(filename, frame)
            self.log(f"Saved verification frame: {filename}")
            self.last_saved = now

        return True

if __name__ == "__main__":
    monitor = CameraMonitor()
    monitor.log("=== Windows Camera Monitor Started ===")
    try:
        while True:
            ok = monitor.check_camera()
            if not ok:
                monitor.log("WARN: Check failed; will retry after interval")
            time.sleep(monitor.check_interval)
    except KeyboardInterrupt:
        monitor.log("=== Windows Camera Monitor Stopped ===")
    except Exception as e:
        monitor.log(f"FATAL ERROR: {e}")
