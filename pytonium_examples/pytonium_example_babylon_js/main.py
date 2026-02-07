import math
import os
import time
import random
from datetime import datetime

# Import the Pytonium class
from Pytonium import Pytonium, returns_value_to_javascript

# Create a Pytonium instance.
pytonium = Pytonium()

# To load a html file, on start up from disk, we need the absolute path to it, so we get it here.
pytonium_test_path = os.path.abspath(__file__)
pytonium_test_path = os.path.dirname(pytonium_test_path)

pytonium.add_mime_type_mapping("glb", "model/gltf-binary")
pytonium.add_custom_scheme("pytonium", f"{pytonium_test_path}\\")
pytonium.add_custom_scheme("pytonium-data", f"{pytonium_test_path}\\data\\")
# Set a custom icon for the window.
pytonium.set_custom_icon_path(f"radioactive.ico")

# Start Pytonium and pass it the start-up URL or file and the width and height of the Window.
pytonium.initialize(f"file://{pytonium_test_path}\\index.html", 1920, 1080)

pytonium.set_show_debug_context_menu(True)

# Start a loop to update the Pytonium message loop and execute some javascript.
while pytonium.is_running():
    time.sleep(0.01)

    # Update the message loop.
    pytonium.update_message_loop()

