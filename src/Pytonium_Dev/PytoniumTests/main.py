import os
import time
from datetime import datetime
from Pytonium import Pytonium, pytonium_cefsubprocess_path


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


pytonium = Pytonium()
myApi = MyApi()

pytonium.set_cefsub_path(pytonium_cefsubprocess_path)

pytonium.add_javascript_python_binding("testfunc", my_js_binding, "test_binding_python_function")
pytonium.add_javascript_python_binding_object(myApi, "test_binding_python_object_methods")

# To load a html file, on start up from disk, we need the absolute path to it, so we get it here.
pytonium_test_path = os.path.abspath(__file__)
pytonium_test_path = os.path.dirname(pytonium_test_path)
pytonium.set_custom_icon_path(f"{pytonium_test_path}\\radioactive.ico")
pytonium.init_cef(f"{pytonium_test_path}\\index.html", 1920, 1080)

while pytonium.is_running():
    time.sleep(0.01)
    pytonium.do_cef_message_loop_work()
    now = datetime.now()
    date_time = now.strftime("%d.%m.%Y, %H:%M:%S")
    code = f"window.state.setTicker('{date_time}')"
    pytonium.execute_javascript(code)

