import os
import time
from datetime import datetime

# Import the Pytonium class
from Pytonium import Pytonium


# This class expose three methods as an endpoint of a javascript binding, and they get called on the test website.
class MyApi:

    def __init__(self):
        self.data = []


    @staticmethod
    def TestOne():
        print("Static Python Method called from Javascript!")

    def TestTwo(self, arg1):
        print("Python Method called from Javascript!")
        self.data.append(arg1)
        print(self.data)

    def TestThree(self, arg1, arg2, arg3):
        print("Python Method called from Javascript!")
        self.data.append(arg1)
        self.data.append(arg2)
        self.data.append(arg3)
        print(self.data)


# This function is the endpoint of a javascript binding, and it's get called on the test website.
def my_js_binding(arg1, arg2, arg3, arg4):
    print("Python Function is called from Javascript!")
    data = [arg1, arg2, arg3, arg4]
    print(data)


# Create a Pytonium instance.
pytonium = Pytonium()

# Create a MyApi instance.
myApi = MyApi()

# Bind the MyApi instance and the test function to javascript.
pytonium.bind_function_to_javascript("testfunc", my_js_binding, "test_binding_python_function")
pytonium.bind_object_methods_to_javascript(myApi, "test_binding_python_object_methods")

# To load a html file, on start up from disk, we need the absolute path to it, so we get it here.
pytonium_test_path = os.path.abspath(__file__)
pytonium_test_path = os.path.dirname(pytonium_test_path)

# Set a custom icon for the window.
pytonium.set_custom_icon_path(f"radioactive.ico")

# Start Pytonium and pass it the start-up URL or file and the width and height of the Window.
pytonium.initialize(f"{pytonium_test_path}\\index.html", 1920, 1080)

# Start a loop to update the Pytonium message loop and execute some javascript.

while pytonium.is_running():
    time.sleep(0.01)

    # Update the message loop.
    pytonium.update_message_loop()

    # Get the current time and date
    now = datetime.now()

    # Format the date and time string.
    date_time = now.strftime("%d.%m.%Y, %H:%M:%S")

    # Save the needed Javascript, to call a function and update a ticker with the current date and time.
    # We created and exposed this function in Javascript on the HTML site.
    code = f"window.state.setTicker('{date_time}')"

    # Execute the javascript.
    pytonium.execute_javascript(code)

