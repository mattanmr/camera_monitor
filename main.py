import cv2
import time
import datetime
import os
import psutil



class CameraMonitor():
    """ Main class for monitoring a USB camera on Windows. """
    def __init__(self, camera_index=0, vendor_hint="USB", log_file="camera_monitor_win.log",
                 save_dir="monitor_frames", check_interval=5, frame_save_interval=3600):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.camera_index = camera_index
        self.vendor_hint = vendor_hint
        self.log_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, log_file)
        self.save_dir = os.path.join(self.base_dir, save_dir)
        self.check_interval = check_interval
        self.frame_save_interval = frame_save_interval
        self.last_saved = 0

        os.makedirs(self.save_dir, exist_ok=True)

    def log(self, msg):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        with open(self.log_file, "a") as f:
            f.write(line + "\n")
    
    def usb_camera_connected(self):
        """Check if a USB imaging device is present."""
        for dev in psutil.disk_partitions(all=True):  # Not enough: USB cameras don't mount as disks
            pass

        # Better method: use Win32 device query
        try:
            import subprocess
            output = subprocess.check_output(
                "wmic path Win32_PnPEntity get Name", shell=True).decode(errors="ignore")
            for line in output.split("\n"):
                if "Camera" in line or "USB" in line:
                    return True
        except Exception:
            pass
        return True  # fail-open so script still works if WMIC missing
    
    def check_camera(self):
        # Check if USB device is present (Windows)
        if not self.usb_camera_connected():
            self.log("ERROR: USB camera not detected by OS")
            return False

        # Try opening camera
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)  # Use DirectShow for stability

        if not cap.isOpened():
            self.log("ERROR: Could not open camera")
            return False

        ret, frame = cap.read()
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
            monitor.check_camera()
            time.sleep(monitor.check_interval)
    except KeyboardInterrupt:
        monitor.log("=== Windows Camera Monitor Stopped ===")   
    except Exception as e:
        monitor.log(f"FATAL ERROR: {e}")
        