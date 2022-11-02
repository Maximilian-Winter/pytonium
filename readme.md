## Pytonium
### Pytonium is a framework for building python apps, with a GUI based on the web-technologies HTML, CSS and Javascript.

It uses the Chromium Embedded Framework for rendering and execution of javascript.

At the moment the framework has basic functionality for loading an url and add
Javascript bindings, so a python function can be called from Javascript.
And also Javascript can be executed, on the website, from python.

The package is avaible via pip.

So just type the following in the console to install it.
```
pip install Pytonium
```

To start Pytonium and load a website, you have to first import Pytonium

```python
from Pytonium import Pytonium
```
This imports the Pytonium class.

After we have created an instance of Pytonium, we can initialize Pytonium, with an initial window width and height and
a URL or filepath. 

```python
from Pytonium import Pytonium

pytonium = Pytonium()
pytonium.initialize("C:\TestSite\index.html", 1920, 1080)
```
Now the App starts the browser on the URL or filepath, we provided.

After the initialization, we need to call the method "update_message_loop" on the Pytonium instance. We need to do
this in a regular interval, so the chromium embedded framework can update.
The easiest way to do this, is with a while loop, that runs as long the browser is open.

```python
import time
from Pytonium import Pytonium

pytonium = Pytonium()

pytonium.initialize("C:\TestSite\index.html", 1920, 1080)

while pytonium.is_running():
    time.sleep(0.01)
    pytonium.update_message_loop()
```

This are the basics to load an HTML file, with CSS and Javascript. 

We have the option to register python functions and methods in Javascript. And make them callable from there.

To do this we just have to call the method "bind_function_to_javascript" on the Pytonium instance, before we call "initialize".


```python
import time
from Pytonium import Pytonium

# Let's define a function and bind it to name testfunc in javascript
def testfunc(arg1, arg2, arg3, arg4):
    print([arg1, arg2, arg3, arg4])

pytonium = Pytonium()
# Here we add the actual binding.
pytonium.bind_function_to_javascript("testfunc", testfunc)

pytonium.initialize("C:\TestSite\index.html", 1920, 1080)

while pytonium.is_running():
    time.sleep(0.01)
    pytonium.update_message_loop()
```

The method "bind_function_to_javascript" takes two required parameters and one optional, the first parameter is
the name which the function is bind to in javascript. The second one is the actual function object. And the third optional
parameter is an optional name for a Javascript object, on which the function will be bind.

The example from above would be called like this in javascript:

```javascript
window.testfunc(42, 24.42, true, 'Hello World!')
```

When I use the optional third parameter like this:

```python
pytonium.bind_function_to_javascript("testfunc", testfunc, "python_api")
```

It would be called like this in javascript:
```javascript
window.python_api.testfunc(42, 24.42, true, 'Hello World!')
```

You can also bind a python object with its method to javascript like this:
```python
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



pytonium.bind_object_methods_to_javascript(myApi, "test_binding_python_object_methods")
```
Here the first parameter is the object to bind and the second is the optional javascript object name.

It would be called like this in Javascript:
```javascript
 // Call function in python without arguments.
window.test_binding_python_object_methods.TestOne()
// Call function in python with arguments.
window.test_binding_python_object_methods.TestTwo(42)
window.test_binding_python_object_methods.TestThree(24.42, true, 'olleH dlroW!')
```

There is also an option to execute javascript from python, like this:

```python
# Get the current time and date to display it on our website.
now = datetime.now()
date_time = now.strftime("%d.%m.%Y, %H:%M:%S")
# Write javascript code to call a function and pass it the date and time.
code = f"window.state.setTicker('{date_time}')"
# Execute the javascript on the current site.
pytonium.execute_javascript(code)
```

The framework is still at an early stage. So things will change over time.

Based on cef version: 106.1.1+g5891c70+chromium-106.0.5249.119

To Build from source, you would have to copy the content of minimal 
distribution of the Chromium Embedded Framework into the folder called 'cef-binaries' and run cmake.


Here is an example main.py, with all current features used, you can find the complete source code in the PytoniumTest Package, which is installed with Pytonium.

```python
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


```