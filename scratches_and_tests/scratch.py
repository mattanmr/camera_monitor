import cv2
import numpy as np

def find_diff(frame1, frame2):
    # find the absolute difference between two frames and return true if difference is found
    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
    non_zero_count = cv2.countNonZero(thresh)
    return non_zero_count > 0

def capture_video():
    cap = cv2.VideoCapture(0)
    current_time = cv2.getTickCount()
    print(f"Video capture started at time: {current_time} and time passed since start: {(current_time - start_time)/cv2.getTickFrequency()} seconds")
    red_dot = (0, 0, 255)  # BGR format for red color
    blue_dot = (255, 0, 0)  # BGR format for blue color
    while True:
        ret, frame = cap.read()
        if not ret:
            break  # Break the loop if no frame is returned

        height, width, _ = frame.shape
        center = (width - 60, 60)
        color = red_dot if find_diff(frame, np.zeros_like(frame)) else blue_dot
        cv2.circle(frame, center, 10, color, -1)

        cv2.imshow('Live Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # start time count and show when the video capture starts
    start_time = cv2.getTickCount()
    capture_video()