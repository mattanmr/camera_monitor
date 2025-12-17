#!/usr/bin/env python3
"""Test script for PTZ (Pan-Tilt-Zoom) camera controls."""

import sys
import time
from main import CameraMonitor


def test_ptz_support():
    """Test if camera supports PTZ controls."""
    print("\n" + "="*60)
    print("PTZ CAMERA CONTROL TEST")
    print("="*60 + "\n")

    monitor = CameraMonitor()

    # Test 1: Get current PTZ position
    print("[TEST 1] Getting current PTZ position...")
    position = monitor.get_ptz_position()
    print(f"Result: {position}\n")

    if "error" in position:
        print("⚠️  Camera could not be opened. Skipping remaining PTZ tests.")
        return False

    pan = position.get("pan", -1)
    tilt = position.get("tilt", -1)
    zoom = position.get("zoom", -1)

    # Check if any value is not -1 (indicates potential PTZ support)
    has_ptz = (pan != -1) or (tilt != -1) or (zoom != -1)

    if has_ptz:
        print(f"✅ Camera reports PTZ values: pan={pan}, tilt={tilt}, zoom={zoom}")
    else:
        print("ℹ️  Camera returned all -1 values (typical for non-PTZ cameras)")
        print("   Testing setters to confirm...")

    # Test 2: Try to set pan
    print("\n[TEST 2] Testing Pan control...")
    print("  Attempting to set pan to 45 degrees...")
    pan_result = monitor.set_pan(45)
    if pan_result:
        print("  ✅ Pan command accepted")
    else:
        print("  ❌ Pan command rejected or unsupported")

    # Check new position
    time.sleep(0.5)
    new_position = monitor.get_ptz_position()
    if "error" not in new_position:
        new_pan = new_position.get("pan", -1)
        print(f"  New pan value: {new_pan}\n")

    # Test 3: Try to set tilt
    print("[TEST 3] Testing Tilt control...")
    print("  Attempting to set tilt to 30 degrees...")
    tilt_result = monitor.set_tilt(30)
    if tilt_result:
        print("  ✅ Tilt command accepted")
    else:
        print("  ❌ Tilt command rejected or unsupported")

    # Check new position
    time.sleep(0.5)
    new_position = monitor.get_ptz_position()
    if "error" not in new_position:
        new_tilt = new_position.get("tilt", -1)
        print(f"  New tilt value: {new_tilt}\n")

    # Test 4: Try to set zoom
    print("[TEST 4] Testing Zoom control...")
    print("  Attempting to set zoom to 5...")
    zoom_result = monitor.set_zoom(5)
    if zoom_result:
        print("  ✅ Zoom command accepted")
    else:
        print("  ❌ Zoom command rejected or unsupported")

    # Check new position
    time.sleep(0.5)
    new_position = monitor.get_ptz_position()
    if "error" not in new_position:
        new_zoom = new_position.get("zoom", -1)
        print(f"  New zoom value: {new_zoom}\n")

    # Test 5: Reset PTZ to home position
    print("[TEST 5] Resetting PTZ to home position (0, 0, 0)...")
    reset_result = monitor.reset_ptz()
    if reset_result:
        print("  ✅ PTZ reset command accepted")
    else:
        print("  ❌ PTZ reset command rejected or unsupported")

    # Check final position
    time.sleep(0.5)
    final_position = monitor.get_ptz_position()
    if "error" not in final_position:
        print(f"  Final position: pan={final_position.get('pan')}, tilt={final_position.get('tilt')}, zoom={final_position.get('zoom')}\n")

    # Summary
    print("="*60)
    print("SUMMARY")
    print("="*60)

    if pan_result or tilt_result or zoom_result:
        print("✅ Camera supports at least one PTZ control (Pan, Tilt, or Zoom)")
        print("\nTo use PTZ controls:")
        print("  monitor = CameraMonitor()")
        print("  monitor.set_pan(45)        # Pan to 45 degrees")
        print("  monitor.set_tilt(-15)      # Tilt to -15 degrees")
        print("  monitor.set_zoom(5)        # Zoom to level 5")
        print("  position = monitor.get_ptz_position()  # Get current position")
        print("  monitor.reset_ptz()        # Reset to home (0, 0, 0)")
        return True
    else:
        print("ℹ️  Camera does not appear to support hardware PTZ controls.")
        print("\nThis is normal for most USB webcams. Only dedicated PTZ cameras")
        print("(conference cameras, IP PTZ cameras with USB interface) support these.")
        print("\nAlternative: Use digital pan/tilt by cropping frames in software.")
        return False


if __name__ == "__main__":
    try:
        supports_ptz = test_ptz_support()
        sys.exit(0 if supports_ptz else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)

