import time
import argparse
import logging

import cv2

logger = logging.getLogger(__name__)


def preprocess(frame, width=None, blur_ksize=(5, 5)):
    """Resize (optional), convert to gray and blur to reduce noise."""
    if width is not None:
        h, w = frame.shape[:2]
        scale = float(width) / float(w)
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, blur_ksize, 0)
    return blurred


def detect_motion(prev_frame, curr_frame, thresh_val=15, min_area=500):
    """Return (motion_detected: bool, diff, thresh, large_contours).

    Uses absolute difference, thresholding, morphological filtering and contour area
    filtering to suppress camera noise.
    """
    diff = cv2.absdiff(prev_frame, curr_frame)
    _, thresh = cv2.threshold(diff, thresh_val, 255, cv2.THRESH_BINARY)

    # Remove small noise and close gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    thresh = cv2.dilate(thresh, kernel, iterations=2)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    large_contours = [c for c in contours if cv2.contourArea(c) >= min_area]

    return len(large_contours) > 0, diff, thresh, large_contours


def capture_video(source=0, duration=None, show_windows=True, min_area=500, width=None, thresh=15, min_frames=2):
    """Capture from `source` for `duration` seconds (None = until 'q').

    Draws a red dot when motion is detected, blue otherwise. Returns True on normal exit.
    """
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        logger.error("Failed to open video source: %s", source)
        return False

    motion_recording_dealy = 20  # seconds to keep recording after motion stops

    # Get the default frame width and height
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_export_folder = "D:/motion_captures"

    # Initialize previous frame
    ret, frame = cap.read()
    if not ret or frame is None:
        logger.error("No frames available from source %s", source)
        cap.release()
        return False

    prev = preprocess(frame, width=width)

    start_time = time.time()
    if duration is None:
        logger.info("Video capture started (run until 'q') at unix time: %.3f", start_time)
    else:
        logger.info("Video capture started at unix time: %.3f", start_time)

    red_dot = (0, 0, 255)
    blue_dot = (255, 0, 0)
    motion_streak = 0
    motion_counter = 0
    out = None
    file_time = None

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            logger.warning("Frame read failed; stopping capture")
            break

        proc = preprocess(frame, width=width)
        motion, diff, thresh_img, contours = detect_motion(prev, proc, thresh_val=thresh, min_area=min_area)

        # temporal debounce to stabilize jittery contours
        motion_streak = motion_streak + 1 if motion else 0
        motion_active = motion_streak >= min_frames

        # choose dot color
        h, w = frame.shape[:2]
        center = (w - 60, 60)
        color = red_dot if motion_active or (motion_counter > 0) else blue_dot
        cv2.circle(frame, center, 7, color, -1)

        if motion_active:
            motion_counter = time.time()
            file_time = time.strftime("%H-%M-%S") if file_time is None else file_time
            if out is None:
                todays_folder = time.strftime("%d_%m_%Y")
                video_export_folder = f'D:/motion_captures/{todays_folder}'
                import os
                os.makedirs(video_export_folder, exist_ok=True)
                export_file_path = f'{video_export_folder}/{file_time}.mp4'
                out = cv2.VideoWriter(export_file_path, fourcc, 20.0, (frame_width, frame_height))
                logger.info(f"Motion detected, started recording to {export_file_path}")

            # Draw bounding boxes
            for c in contours:
                x, y, cw, ch = cv2.boundingRect(c)
                cv2.rectangle(frame, (int(x * (frame.shape[1] / float(proc.shape[1]))), int(y * (frame.shape[0] / float(proc.shape[0])))),
                              (int((x + cw) * (frame.shape[1] / float(proc.shape[1]))), int((y + ch) * (frame.shape[0] / float(proc.shape[0])))),
                              (0, 255, 0), 2)

        # if no motion for a while, stop recording
        if time.time() - motion_counter > motion_recording_dealy:
            motion_counter = 0
            if out is not None:
                out.release()
                logger.info(
                f"No motion for {str(motion_recording_dealy)}s, stopped recording, file saved at: {export_file_path if 'export_file_path' in locals() else 'unknown'}")
            file_time = None

            out = None
        else:
            # Show current time code
            time_code = time.strftime("%H:%M:%S")
            date_code = time.strftime("%d-%m-%Y")
            text_string = f"{date_code} {time_code}"
            cv2.putText(frame, text_string, (frame.shape[1] - 125, frame.shape[0] - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
            out.write(frame)

        if show_windows:
            cv2.imshow('Live Video', frame)
            cv2.imshow('DIFF', diff)
            cv2.imshow('THRESH', thresh_img)

        prev = proc

        if (cv2.waitKey(1) & 0xFF) == ord('q'):
            logger.info('User requested exit (q)')
            break

        if duration is not None and (time.time() - start_time) >= duration:
            logger.info('Specified duration reached: %.1fs', duration)
            break

    cap.release()
    if show_windows:
        cv2.destroyAllWindows()
    return True


def build_arg_parser():
    p = argparse.ArgumentParser(description='Simple motion detector test harness')
    p.add_argument('--source', type=int, default=0, help='Video source index (default 0)')
    p.add_argument('--duration', type=float, default=None, help="Seconds to run; omit for run-until-'q'")
    p.add_argument('--min-area', type=int, default=500, help='Minimum contour area to count as motion')
    p.add_argument('--width', type=int, default=None, help='Optional width to resize frames for processing')
    p.add_argument('--thresh', type=int, default=15, help='Threshold value for diff->binary')
    p.add_argument('--min-frames', type=int, default=2, help='Consecutive frames required to treat motion as active')
    p.add_argument('--no-windows', action='store_true', help='Do not show OpenCV GUI windows')
    return p


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    args = build_arg_parser().parse_args()

    show_windows = not args.no_windows

    success = capture_video(source=args.source, duration=args.duration, show_windows=show_windows,
                            min_area=args.min_area, width=args.width, thresh=args.thresh, min_frames=args.min_frames)
    if not success:
        logger.error('capture_video returned False')
    else:
        logger.info('capture_video finished successfully')
