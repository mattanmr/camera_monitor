import cv2
import sys

# Quick health check: attempts to open index 0 with DirectShow, then MSMF

def try_open(index):
    backends = [getattr(cv2, "CAP_DSHOW", None), getattr(cv2, "CAP_MSMF", None)]
    for be in backends:
        if be is None:
            continue
        cap = cv2.VideoCapture(index, be)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                print(f"OK: camera index {index} via backend {be}")
                return True
            else:
                print(f"ERROR: open ok but read failed at index {index}, backend {be}")
    return False

if __name__ == "__main__":
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    ok = try_open(idx)
    sys.exit(0 if ok else 1)
