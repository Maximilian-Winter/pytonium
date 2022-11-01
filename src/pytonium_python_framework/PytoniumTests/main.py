import os
import time
from datetime import datetime

# Import the Pytonium class and the path for the sub-process executable.
from Pytonium import Pytonium, pytonium_subprocess_path


# This class expose three methods as an endpoint of a javascript binding, and they get called on the test website.
class MyApi:

    def __init__(self):
        self.data = []

    @staticmethod
    def TestOne(args):
        print("Static Python Method called from Javascript!")
        print(args)

    def TestTwo(self, args):
        print("Python Method called from Javascript!")
        self.data.append(args[0])
        print(self.data)

    def TestThree(self, args):
        print("Python Method called from Javascript!")
        self.data[0] += args[1]
        print(self.data)


# This function is the endpoint of a javascript binding, and it's get called on the test website.
def my_js_binding(args):
    print("Python Function is called from Javascript!")
    print(args)


# Create a Pytonium instance
pytonium = Pytonium()
myApi = MyApi()

#
pytonium.set_subprocess_path(pytonium_subprocess_path)

pytonium.bind_function_to_javascript("testfunc", my_js_binding, "test_binding_python_function")
pytonium.bind_object_methods_to_javascript(myApi, "test_binding_python_object_methods")

# To load a html file, on start up from disk, we need the absolute path to it, so we get it here.
pytonium_test_path = os.path.abspath(__file__)
pytonium_test_path = os.path.dirname(pytonium_test_path)
pytonium.set_custom_icon_path(f"{pytonium_test_path}\\radioactive.ico")
pytonium.initialize(f"{pytonium_test_path}\\index.html", 1920, 1080)

while pytonium.is_running():
    time.sleep(0.01)
    pytonium.update_message_loop()
    now = datetime.now()
    date_time = now.strftime("%d.%m.%Y, %H:%M:%S")
    code = f"window.state.setTicker('{date_time}')"
    pytonium.execute_javascript(code)

