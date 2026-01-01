import cv2
import numpy as np

# Capture video from webcam (0) or a file ('video.mp4')
cap = cv2.VideoCapture(0)

# Initialize the first frame
first_frame = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 1. Pre-processing: Convert to grayscale and blur
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)  # Apply Gaussian blur

    # Initialize the first frame once
    if first_frame is None:
        first_frame = gray
        continue

    # 2. Calculate the absolute difference between the current frame and first frame
    frame_delta = cv2.absdiff(first_frame, gray)

    # 3. Thresholding: Isolate significant changes
    # Pixels with a difference > 30 become white (255), otherwise black (0)
    thresh = cv2.threshold(frame_delta, 30, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)  # Dilate to fill holes

    # 4. Find contours of the moving objects
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 5. Draw bounding rectangles around large enough contours
    for contour in contours:
        # Ignore contours that are too small (noise)
        if cv2.contourArea(contour) < 500:  # Minimum area size can be adjusted
            continue

        # Draw a bounding box around the moving object
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, "Motion Detected", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Display the results
    cv2.imshow('Motion Detection Feed', frame)
    cv2.imshow('Threshold Frame', thresh)  # Shows binary mask

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
