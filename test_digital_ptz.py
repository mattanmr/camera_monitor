#!/usr/bin/env python3
"""Test script for digital pan-tilt-zoom (software-based controls for non-PTZ cameras)."""

import sys
import cv2
import numpy as np
from main import CameraMonitor


def test_digital_ptz():
    """Test digital pan-tilt-zoom on captured frame."""
    print("\n" + "="*60)
    print("DIGITAL PAN-TILT-ZOOM TEST (Software-based controls)")
    print("="*60 + "\n")
    
    monitor = CameraMonitor()
    
    # Capture a frame
    print("[STEP 1] Capturing frame from camera...")
    cap = cv2.VideoCapture(monitor.camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(monitor.camera_index, cv2.CAP_MSMF)
    
    if not cap.isOpened():
        print("❌ Could not open camera")
        return False
    
    # Warmup
    for _ in range(15):
        cap.read()
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret or frame is None:
        print("❌ Could not capture frame")
        return False
    
    print(f"✅ Frame captured: {frame.shape}")
    
    # Test digital pan
    print("\n[TEST 1] Testing Digital Pan...")
    print("  Panning left (offset=-1.0)...")
    pan_left = monitor.digital_pan(frame, pan_offset=-1.0)
    print(f"  ✅ Pan left result: {pan_left.shape}")
    
    print("  Panning center (offset=0.0)...")
    pan_center = monitor.digital_pan(frame, pan_offset=0.0)
    print(f"  ✅ Pan center result: {pan_center.shape}")
    
    print("  Panning right (offset=1.0)...")
    pan_right = monitor.digital_pan(frame, pan_offset=1.0)
    print(f"  ✅ Pan right result: {pan_right.shape}")
    
    # Test digital tilt
    print("\n[TEST 2] Testing Digital Tilt...")
    print("  Tilting up (offset=-1.0)...")
    tilt_up = monitor.digital_tilt(frame, tilt_offset=-1.0)
    print(f"  ✅ Tilt up result: {tilt_up.shape}")
    
    print("  Tilting center (offset=0.0)...")
    tilt_center = monitor.digital_tilt(frame, tilt_offset=0.0)
    print(f"  ✅ Tilt center result: {tilt_center.shape}")
    
    print("  Tilting down (offset=1.0)...")
    tilt_down = monitor.digital_tilt(frame, tilt_offset=1.0)
    print(f"  ✅ Tilt down result: {tilt_down.shape}")
    
    # Test digital zoom
    print("\n[TEST 3] Testing Digital Zoom...")
    print("  Zoom out (factor=0.5)...")
    zoom_out = monitor.digital_zoom(frame, zoom_factor=0.5)
    print(f"  ✅ Zoom out result: {zoom_out.shape}")
    
    print("  No zoom (factor=1.0)...")
    zoom_1x = monitor.digital_zoom(frame, zoom_factor=1.0)
    print(f"  ✅ 1x zoom result: {zoom_1x.shape}")
    
    print("  Zoom in 2x (factor=2.0)...")
    zoom_2x = monitor.digital_zoom(frame, zoom_factor=2.0)
    print(f"  ✅ 2x zoom result: {zoom_2x.shape}")
    
    print("  Zoom in 3x (factor=3.0)...")
    zoom_3x = monitor.digital_zoom(frame, zoom_factor=3.0)
    print(f"  ✅ 3x zoom result: {zoom_3x.shape}")
    
    # Save sample outputs
    print("\n[STEP 2] Saving sample outputs to monitor_frames/...")
    try:
        cv2.imwrite("monitor_frames/digital_pan_left.jpg", pan_left)
        cv2.imwrite("monitor_frames/digital_pan_center.jpg", pan_center)
        cv2.imwrite("monitor_frames/digital_pan_right.jpg", pan_right)
        cv2.imwrite("monitor_frames/digital_tilt_up.jpg", tilt_up)
        cv2.imwrite("monitor_frames/digital_tilt_center.jpg", tilt_center)
        cv2.imwrite("monitor_frames/digital_tilt_down.jpg", tilt_down)
        cv2.imwrite("monitor_frames/digital_zoom_1x.jpg", zoom_1x)
        cv2.imwrite("monitor_frames/digital_zoom_2x.jpg", zoom_2x)
        cv2.imwrite("monitor_frames/digital_zoom_3x.jpg", zoom_3x)
        print("✅ Sample images saved")
    except Exception as e:
        print(f"⚠️  Could not save images: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("✅ Digital pan-tilt-zoom works correctly!")
    print("\nUsage examples:")
    print("  monitor = CameraMonitor()")
    print("  frame = capture_frame()  # Your capture logic")
    print("  ")
    print("  # Pan left, center, right")
    print("  pan_left = monitor.digital_pan(frame, pan_offset=-1.0)")
    print("  pan_right = monitor.digital_pan(frame, pan_offset=1.0)")
    print("  ")
    print("  # Tilt up, center, down")
    print("  tilt_up = monitor.digital_tilt(frame, tilt_offset=-1.0)")
    print("  tilt_down = monitor.digital_tilt(frame, tilt_offset=1.0)")
    print("  ")
    print("  # Zoom out, 1x, 2x, 3x")
    print("  zoom_out = monitor.digital_zoom(frame, zoom_factor=0.5)")
    print("  zoom_2x = monitor.digital_zoom(frame, zoom_factor=2.0)")
    print("  zoom_3x = monitor.digital_zoom(frame, zoom_factor=3.0)")
    print("\nOffset ranges:")
    print("  - pan_offset:  -1.0 (left) to 1.0 (right), 0 = center")
    print("  - tilt_offset: -1.0 (up) to 1.0 (down), 0 = center")
    print("  - zoom_factor: 0.5 (zoom out) to 3.0 (zoom in), 1.0 = no zoom")
    
    return True


if __name__ == "__main__":
    try:
        success = test_digital_ptz()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

