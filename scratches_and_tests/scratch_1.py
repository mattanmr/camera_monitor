import cv2
import numpy as np

# Initialize the video capture object (0 for webcam)
# Replace 0 with a video file path (e.g., "video.mp4") to analyze a file
cap = cv2.VideoCapture(0)

# Initialize the first frame
first_frame = None

while True:
    # Read a new frame from the video stream
    ret, frame = cap.read()
    if not ret:
        break # Break the loop if no frame is returned

    # Resize the frame for faster processing (optional)
    frame = cv2.resize(frame, (640, 480))

    # Convert to grayscale and apply Gaussian blur to reduce noise
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # If the first frame is None, initialize it and continue to the next frame
    if first_frame is None:
        first_frame = gray
        continue

    # Calculate the absolute difference between the current frame and the first frame
    frame_diff = cv2.absdiff(first_frame, gray)

    # Apply a threshold to the difference image to highlight significant changes
    # Pixels with an intensity difference > 30 become white (255)
    _, thresh = cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)

    # Dilate the thresholded image to fill in holes and improve contour detection
    thresh = cv2.dilate(thresh, None, iterations=2)

    # Find contours (outlines) of the white regions in the thresholded image
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Loop over the contours
    for contour in contours:
        # Filter out small contours caused by noise (minimum area threshold)
        if cv2.contourArea(contour) < 500:
            continue

        # Draw a green bounding rectangle around the moving object in the original frame
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, "Motion Detected", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Display the original frame with motion detection indicators
    cv2.imshow('Live Motion Detection', frame)
    # Display the thresholded frame (optional, for debugging)
    # cv2.imshow('Threshold Frame', thresh)

    # Break the loop if the 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()
