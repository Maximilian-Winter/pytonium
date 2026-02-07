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

# Set a custom icon for the window.
pytonium.set_custom_icon_path(f"radioactive.ico")

# Start Pytonium and pass it the start-up URL or file and the width and height of the Window.
pytonium.initialize(f"file://{pytonium_test_path}\\index.html", 1920, 1080)

labels = []
data = []

# For random walk
previous_stock_price = 100

# For Brownian motion
mu = 0.001
sigma = 0.01
S0 = 100

last_update_time = time.time()

# Start a loop to update the Pytonium message loop and execute some javascript.
while pytonium.is_running():
    time.sleep(0.01)

    # Update the message loop.
    pytonium.update_message_loop()

    # Check if 2 seconds have passed
    current_time = time.time()
    if current_time - last_update_time >= 0.5:
        # Update last_update_time
        last_update_time = current_time

        # Get the current time and date for displaying it on the test website.
        now = datetime.now()

        # Format the date and time string.
        date_time = now.strftime("%d.%m.%Y, %H:%M:%S")
        labels.append(date_time)

        # Brownian motion
        Wt = random.gauss(0, 1)
        new_stock_price = S0 * math.exp((mu - 0.5 * sigma ** 2) + sigma * math.sqrt(1) * Wt)
        data.append(new_stock_price)

        # Set an app state to a specific value.
        pytonium.set_state("app-general", "stock_data", {"data": data, "labels": labels})

    # Example on how to execute Javascript from Python:

    # Save the needed Javascript, to call a function and update a ticker with the current date and time.
    # We created and exposed this function in Javascript on the HTML site.
    # code = f"CallFromPythonExample.setTicker('{date_time}')"

    # Execute the javascript.
    # pytonium.execute_javascript(code)
