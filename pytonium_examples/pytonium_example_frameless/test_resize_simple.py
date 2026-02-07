"""
Simple test for window resize functionality.
Run this to test if the basic resize works from Python.
"""

import os
import sys
import time

from Pytonium import Pytonium


def main():
    pytonium = Pytonium()
    pytonium.set_frameless_window(True)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "test_resize.html")
    
    print("=" * 60)
    print("Pytonium Resize Test")
    print("=" * 60)
    print(f"Loading: {html_path}")
    print()
    
    pytonium.initialize(f"file://{html_path}", 1200, 800)
    
    # Wait a bit for the window to appear
    time.sleep(2)
    
    print("\nTesting window operations from Python...")
    print("-" * 40)
    
    # Test get size
    try:
        size = pytonium.get_window_size()
        print(f"Current size: {size}")
    except Exception as e:
        print(f"get_window_size FAILED: {e}")
    
    # Test get position
    try:
        pos = pytonium.get_window_position()
        print(f"Current position: {pos}")
    except Exception as e:
        print(f"get_window_position FAILED: {e}")
    
    # Test is_maximized
    try:
        maximized = pytonium.is_maximized()
        print(f"Is maximized: {maximized}")
    except Exception as e:
        print(f"is_maximized FAILED: {e}")
    
    print("\n" + "=" * 60)
    print("Resize Test Starting in 3 seconds...")
    print("Watch the window to see if it resizes!")
    print("=" * 60)
    
    time.sleep(3)
    
    # Test set_window_size
    print("\n[Test 1] Setting size to 1000x700 using set_window_size()...")
    try:
        pytonium.set_window_size(1000, 700)
        time.sleep(1)
        size = pytonium.get_window_size()
        print(f"  Result: {size}")
    except Exception as e:
        print(f"  FAILED: {e}")
    
    time.sleep(2)
    
    # Test resize_window with different anchors
    print("\n[Test 2] Resizing to 1200x800 with anchor 0 (top-left)...")
    try:
        pytonium.resize_window(1200, 800, 0)
        time.sleep(1)
        size = pytonium.get_window_size()
        pos = pytonium.get_window_position()
        print(f"  Result: size={size}, pos={pos}")
    except Exception as e:
        print(f"  FAILED: {e}")
    
    time.sleep(2)
    
    print("\n[Test 3] Resizing to 900x600 with anchor 3 (bottom-right)...")
    try:
        pytonium.resize_window(900, 600, 3)
        time.sleep(1)
        size = pytonium.get_window_size()
        pos = pytonium.get_window_position()
        print(f"  Result: size={size}, pos={pos}")
    except Exception as e:
        print(f"  FAILED: {e}")
    
    time.sleep(2)
    
    print("\n" + "=" * 60)
    print("Tests complete! Window should stay open.")
    print("Close the window to exit.")
    print("=" * 60)
    
    # Keep the window open
    while pytonium.is_running():
        time.sleep(0.01)
        pytonium.update_message_loop()


if __name__ == "__main__":
    main()
