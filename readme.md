## Pytonium
### Pytonium is a framework for building python apps, with a GUI based on the web-technologies HTML, CSS and Javascript.

It uses the Chromium Embedded Framework for rendering and execution of javascript.

### Features:

- Create appealing UIs for Python Apps through the web-technologies HTML, CSS and Javascript, using frameworks like React, Preact and Tailwind CSS for styling.
- Call Python function and methods from Javascript and return values from Python to Javascript.
- Handle the application state through simple methods and event based interfaces in Javascript and Python.
- Execute Javascript from Python on the UI.

The package is available via pip.

So just type the following in the console to install it.
```
pip install Pytonium
```

To start Pytonium and load a website or local site, you have to first import Pytonium

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

```python
import time
from Pytonium import Pytonium

pytonium = Pytonium()

# This function is the endpoint of a javascript binding, and it's get called on the test website and returns an object to Javascript.
@returns_value_to_javascript("any")
def my_js_binding():
    return {"Answer": 42}

# Bind the test function to javascript, we have to provide a name under which the function will be found and the actual function, we can pass an optional object name in Javascript.
pytonium.bind_function_to_javascript("testfunc", my_js_binding, "test_function_binding")


pytonium.initialize("C:\TestSite\index.html", 1920, 1080)

while pytonium.is_running():
    time.sleep(0.01)
    pytonium.update_message_loop()
```

To bind a Python function to Javascript, we have to provide a name under which the function will be found and the actual function, we can pass an optional object name in Javascript. After that we can call the function in Javascript like that:
````javascript
Pytonium.test_function_binding.testfunc();
````

We can also return values from Python to Javascript by using a Promise in Javascript, to get the return value of testfunc, we have to use Promise returned by Pytonium like that:

````javascript
 let myPromise = Pytonium.test_function_binding.testfunc();
 myPromise.then((resolvedValue) => {
    console.log("The answer to the Ultimate Question of Life, the Universe and Everything:", resolvedValue.Answer);
});
````
We also have the option to handle and manage the application state with the help of Pytonium. The application state is divided into namespaces, to add or set a namespace and value, we have to simply call 'setState' on the 'Pytonium.appState' object. The following code shows different ways to create and access a state or all states in a namespace:

````javascript
// Register to app state updates from Python and Javascript. You can pass a custom event name and a list of namespaces to subscribe to.
Pytonium.appState.registerForStateUpdates("ChangeDate", ["app-general"]);

// Add a listener for the custom event and retrieve information.
document.addEventListener('ChangeDate', function(event) {
    const detail = event.detail;
    const namespace = detail.namespace;
    const key = detail.key;
    const value = detail.value;

    // console.log("State Updated:", namespace, key, value);
    document.getElementById('date').innerHTML = '<p>' + value + '</p>';
});

// Set some app state, synced to Python and Javascript.
Pytonium.appState.setState("user", "age", 64)
console.log(Pytonium.appState.getState("user", "age"));
````

To get the updates to the state in Python, we have to implement a state handler, it basically looks like that in the simplest form:
```python
# An example class to handle app state updates from Javascript.
# The update_state method is mandatory and gets called automatically from Pytonium.
class MyStateHandler:

    def update_state(self, namespace, key, value):
        print(f"State Update:\nNamespace={namespace}\nKey={key}\nValue={str(value)}")

# Create a MyStateHandler instance.
myStateHandler = MyStateHandler()
# Add a state handler for the 'user' namespace and receive updates. 'user' is just an example used on the test website.
pytonium.add_state_handler(myStateHandler, ["user"])
```
The only thing mandatory in a state handler is an update_state method with namespace, key and value as arguments. This method get called whenever a namespace changes a value to which the state handler is subscribed. In the example above is the state handler to the 'user' namespace subscribed.


The bindings of the Python functions and methods, and state handlers, has to be performed before Pytonium is initialized and started.
You can also bind complete Python objects with all its methods to Javascript, which is show in the complete example below, which contains all current features:

The following is the Python code, the corresponding HTML and Javascript code is below.
```python
import os
import time
from datetime import datetime

# Import the Pytonium class
from Pytonium import Pytonium, returns_value_to_javascript


# This class expose two methods as an endpoint of a javascript binding, and they get called on the test website.
# The first method gets called with one argument and returns a value.
class MyApi:

    def __init__(self):
        self.data = []

    # Needed decorator to mark the method as returning values as Promises in Javascript, optional with return type in Javascript to generate typescript d.ts file of all exposed Python methods and functions.
    @returns_value_to_javascript("number")
    def test_one(self, arg1: int):
        print("Python Method called from Javascript with one argument and returns a value!")
        print(arg1)
        return arg1

    def test_two(self, arg1: str, arg2: int, arg3: int):
        print("Python Method called from Javascript!")
        self.data.append(arg1)
        self.data.append(arg2)
        self.data.append(arg3)
        print(self.data)


# An example class to handle app state updates from Javascript.
# The update_state method is mandatory and gets called automatically from Pytonium.
class MyStateHandler:

    def update_state(self, namespace, key, value):
        print(f"State Update:\nNamespace={namespace}\nKey={key}\nValue={str(value)}")


# Create a Pytonium instance.
pytonium = Pytonium()

# Create a MyApi instance.
myApi = MyApi()

# Create a MyStateHandler instance.
myStateHandler = MyStateHandler()


# This function is the endpoint of a javascript binding, and it's get called on the test website and returns a Javascript object.
@returns_value_to_javascript("any")
def my_js_binding():
    return {"Answer": 42}


# Add a state handler for the 'user' namespace and receive updates. 'user' is just an example used on the test website.
pytonium.add_state_handler(myStateHandler, ["user"])

# Bind the MyApi instance and the test function to javascript.
pytonium.bind_function_to_javascript("testfunc", my_js_binding, "test_function_binding")
pytonium.bind_object_methods_to_javascript(myApi, "test_class_methods_binding")

# Generate a typescript d.ts file, of the Python bindings, for the IDE to support auto-completetion etc.
pytonium.generate_typescript_definitions("test.d.ts")


# To load a html file, on start up from disk, we need the absolute path to it, so we get it here.
pytonium_test_path = os.path.abspath(__file__)
pytonium_test_path = os.path.dirname(pytonium_test_path)

# Set a custom icon for the window.
pytonium.set_custom_icon_path(f"radioactive.ico")

# Start Pytonium and pass it the start-up URL or file and the width and height of the Window.
pytonium.initialize(f"file://{pytonium_test_path}\\index.html", 1920, 1080)


# Start a loop to update the Pytonium message loop and execute some javascript.
while pytonium.is_running():
    time.sleep(0.01)

    # Update the message loop.
    pytonium.update_message_loop()

    # Get the current time and date for displaying it on the test website.
    now = datetime.now()

    # Format the date and time string.
    date_time = now.strftime("%d.%m.%Y, %H:%M:%S")

    # Set an app state to a specific value.
    pytonium.set_state("app-general", "date", date_time)

    # Example on how to execute Javascript from Python:

    # Save the needed Javascript, to call a function and update a ticker with the current date and time.
    # We created and exposed this function in Javascript on the HTML site.
    # code = f"CallFromPythonExample.setTicker('{date_time}')"

    # Execute the javascript.
    # pytonium.execute_javascript(code)
```
Here is the corresponding HTML and Javascript code.
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>PytoniumTest</title>
</head>
<body>
<div id ="app">
    <p>Hello World!</p>
    <div id ="date">

    </div>
</div>

</body>
<script>

    // Define a function to showcase Pytonium features.
    function CallToPythonExample()
    {
        // Register to app state updates from Python and Javascript. You can pass a custom event name and a list of namespaces to subscribe to.
        Pytonium.appState.registerForStateUpdates("ChangeDate", ["app-general"]);

        // Add a listener for the custom event and retrieve information.
        document.addEventListener('ChangeDate', function(event) {
            const detail = event.detail;
            const namespace = detail.namespace;
            const key = detail.key;
            const value = detail.value;

            // console.log("State Updated:", namespace, key, value);
            document.getElementById('date').innerHTML = '<p>' + value + '</p>';
        });

        // Set some app state, synced to Python and Javascript.
        Pytonium.appState.setState("user", "age", 64)
        console.log(Pytonium.appState.getState("user", "age"));
        // Call function in python with return value.
        let myPromise = Pytonium.test_function_binding.testfunc();
        myPromise.then((resolvedValue) => {
            console.log("The answer to the Ultimate Question of Life, the Universe and Everything:", resolvedValue.Answer);
        });

        console.log(Pytonium.appState.getState("user", "age"));


        let myPromise2 = Pytonium.test_class_methods_binding.test_one(64);
        myPromise2.then((resolvedValue) => {
            console.log("The answer to the Ultimate Question of Life, the Universe and Everything:", resolvedValue);
        });
        Pytonium.test_class_methods_binding.test_two("Dlrow Olleh!", 20, 40)
    }

    // Check if Python bindings are ready and call them, if not add an event listener for the PytoniumReady event.
    if (window.PytoniumReady) {
        CallToPythonExample();
    } else {
        window.addEventListener('PytoniumReady', function() {
            CallToPythonExample();
        });
    }
    // Example for defining a function that is callable from Python.
    var CallFromPythonExample = {
        setTicker: function(date) {
            document.getElementById('app').innerHTML = '<p>Hello World!</p>' + '<p>' + date + '</p>';
        },
    };
</script>
</html>
```

It is tested and developed under Windows 11 and **Python 3.11**, but also has **Linux Support**. And can be used with **Python 3.10**.