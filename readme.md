## Pytonium
### Pytonium is a framework for building python apps, with a GUI based on the web-technologies HTML, CSS and Javascript.

It uses the Chromium Embedded Framework for rendering and execution of javascript.

At the moment the framework has basic functionality for loading an url and add
Javascript bindings, so a python function can be called from Javascript.
And also Javascript can be executed, on the website, from python.

To start Pytonium and load a website, you have to first import Pytonium

```python
from Pytonium import Pytonium, pytonium_subprocess_path
```

This imports the Pytonium class and the path to the sub-process executable, which Pytonium
will need to render the browser in a window.
After we have created an instance of Pytonium, we need to call "set_subprocess_path" on this instance.

```python
from Pytonium import Pytonium, pytonium_subprocess_path

pytonium = Pytonium()
pytonium.set_subprocess_path(pytonium_subprocess_path)
```

Once we have set the sub-process path, we can initialize Pytonium, with an initial window width and height and
a URL or filepath. Now the App starts the browser on the URL or filepath, we provided.

```python
from Pytonium import Pytonium, pytonium_subprocess_path

pytonium = Pytonium()
pytonium.set_subprocess_path(pytonium_subprocess_path)

pytonium.initialize("C:\TestSite\index.html", 1920, 1080)
```
After the initialization, we need to call the method "update_message_loop" on the Pytonium instance. We need to do
this in a regular interval, so the chromium embedded framework can update.
The easiest way to do this, is with a while loop, that runs as long the browser is open.

```python
import time
from Pytonium import Pytonium, pytonium_subprocess_path

pytonium = Pytonium()
pytonium.set_subprocess_path(pytonium_subprocess_path)

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
from Pytonium import Pytonium, pytonium_subprocess_path

# Let's define a function and bind it to name testfunc in javascript
def testfunc(args):
    print(args)

pytonium = Pytonium()
pytonium.set_subprocess_path(pytonium_subprocess_path)

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
myApi = MyApi()

pytonium.pytonium.bind_object_methods_to_javascript(myApi, "test_binding_python_object_methods")
```
Here the first parameter is the object to bind and the second is the optional javascript object name.

It would be called like this in Javascript:
```javascript
window.test_binding_python_object_methods.TestOne(42, 24.42, true, 'Hello World!')
window.test_binding_python_object_methods.TestTwo(42, 24.42, true, 'Hello World!')
window.test_binding_python_object_methods.TestThree(42, 24.42, true, 'Hello World!')
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
