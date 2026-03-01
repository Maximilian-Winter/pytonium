"""Pytonium Babylon.js Example — 3D Graphics

Demonstrates loading a 3D scene with Babylon.js inside Pytonium:
- Custom URL schemes for local resource loading
- MIME type registration for binary 3D model files (.glb)
- Babylon.js engine with animated character model

Requirements:
- Place babylon.js and babylonjs.loaders.js in this directory
- Place a .glb model file (e.g. HipHopDancing.glb) in the data/ subdirectory
"""

import os
import time

from Pytonium import Pytonium


def main():
    pytonium = Pytonium()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "index.html")

    # Register MIME type for glTF binary models
    pytonium.add_mime_type_mapping("glb", "model/gltf-binary")

    # Custom schemes to serve local files (Babylon.js libs + model data)
    pytonium.add_custom_scheme("pytonium", current_dir + "/")
    pytonium.add_custom_scheme("pytonium-data", os.path.join(current_dir, "data") + "/")

    pytonium.set_show_debug_context_menu(True)
    pytonium.initialize(f"file:///{html_path}", 1920, 1080)

    while pytonium.is_running():
        pytonium.update_message_loop()
        time.sleep(0.01)


if __name__ == "__main__":
    main()
