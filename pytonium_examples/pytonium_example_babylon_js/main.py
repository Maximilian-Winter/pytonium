"""Pytonium Babylon.js Example — Transparent 3D Scene

Demonstrates a 3D animated character floating over the desktop using:
- OSR (Off-Screen Rendering) mode for per-pixel transparency
- Frameless window with no chrome
- Babylon.js with transparent background
- Custom URL schemes for local resource loading
- MIME type registration for binary 3D model files (.glb)
- Window drag (left-click + drag) and camera orbit (right-click + drag)
- Close via Escape key or floating close button

The character dances directly on your desktop with no background!

Requirements:
- Place babylon.js and babylonjs.loaders.js in this directory
- Place a .glb model file (e.g. HipHopDancing.glb) in the data/ subdirectory
"""

import os
import time

from Pytonium import Pytonium, returns_value_to_javascript


# ============================================================================
# Window Control Functions
# ============================================================================

def window_start_drag():
    """Initiate native OS window drag — smooth, zero-latency."""
    pytonium.start_window_drag()


def window_close():
    """Close the application."""
    pytonium.close_window()


@returns_value_to_javascript("object")
def window_get_position():
    """Get window position as {x, y}."""
    x, y = pytonium.get_window_position()
    return {"x": x, "y": y}


def window_set_position(x: int, y: int):
    """Set window position."""
    pytonium.set_window_position(x, y)


# ============================================================================
# Main
# ============================================================================

def main():
    global pytonium

    pytonium = Pytonium()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "index.html")

    # Register MIME type for glTF binary models
    pytonium.add_mime_type_mapping("glb", "model/gltf-binary")

    # Custom schemes to serve local files (Babylon.js libs + model data)
    pytonium.add_custom_scheme("pytonium", current_dir + "/")
    pytonium.add_custom_scheme("pytonium-data", os.path.join(current_dir, "data") + "/")

    # Window controls — native drag, close, position for the transparent window
    pytonium.bind_function_to_javascript(window_start_drag, "startDrag", "window")
    pytonium.bind_function_to_javascript(window_close, "close", "window")
    pytonium.bind_function_to_javascript(window_get_position, "getPosition", "window")
    pytonium.bind_function_to_javascript(window_set_position, "setPosition", "window")

    # Enable transparency: frameless window + OSR mode + taskbar presence
    pytonium.set_frameless_window(True)
    pytonium.set_osr_mode(True)
    pytonium.set_show_in_taskbar(True)

    # Window icon — shown in the taskbar
    pytonium.set_custom_icon_path(os.path.join(current_dir, "radioactive.ico"))

    pytonium.set_show_debug_context_menu(True)
    pytonium.initialize(f"file:///{html_path}", 1920, 1080)
    pytonium.center_window()
    while pytonium.is_running():
        pytonium.update_message_loop()
        time.sleep(0.01)


if __name__ == "__main__":
    main()
