"""Multi-window smoke test for the multi-instance refactor.

Run this after building to verify that two independent browser windows
can be created and run in the same process.

Usage:
    python tests/test_multi_window.py
"""

import sys
import os
import time

from Pytonium import Pytonium


def main():
    print("=== Multi-Window Smoke Test ===\n")

    # Create first instance
    p1 = Pytonium()
    print(f"[p1] Created. Browser ID: {p1.get_browser_id()}")
    print(f"[p1] CEF initialized: {Pytonium.is_cef_initialized()}")

    p1.initialize("https://example.com", 800, 600)
    print(f"[p1] Initialized. Browser ID: {p1.get_browser_id()}")
    print(f"[p1] Running: {p1.is_running()}")
    print(f"     CEF initialized: {Pytonium.is_cef_initialized()}")

    # Create second instance
    p2 = Pytonium()
    print(f"\n[p2] Created. Browser ID: {p2.get_browser_id()}")

    p2.initialize("https://example.org", 600, 400)
    print(f"[p2] Initialized. Browser ID: {p2.get_browser_id()}")
    print(f"[p2] Running: {p2.is_running()}")

    print(f"\nBoth windows open. Close them to exit.")
    print(f"  p1 browser ID: {p1.get_browser_id()}")
    print(f"  p2 browser ID: {p2.get_browser_id()}")

    # Pump message loop while any window is open
    while p1.is_running() or p2.is_running():
        p1.update_message_loop()
        time.sleep(0.016)

    print("\nAll windows closed.")
    p1.shutdown()
    print("CEF shut down. Test passed!")


if __name__ == "__main__":
    main()
