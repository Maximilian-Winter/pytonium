---
title: Simple App
---

# Simple App

This example demonstrates the fundamentals of a Pytonium application: custom schemes for local file loading, Python-to-JavaScript function bindings, and real-time state management.

!!! tip "Full Source"
    The complete source code is available in the main repository at [`pytonium_examples/pytonium_example_simple`](https://github.com/Maximilian-Winter/pytonium/tree/master/pytonium_examples/pytonium_example_simple).

---

## Python Entry Point

```python title="main.py"
import os
import time
from datetime import datetime
from Pytonium import Pytonium, returns_value_to_javascript

pytonium = Pytonium()


@returns_value_to_javascript("any")
def get_greeting():
    return {"message": "Hello from Python!", "answer": 42}


pytonium.bind_function_to_javascript(get_greeting, javascript_object="api")
pytonium.add_custom_scheme("app", os.path.dirname(os.path.abspath(__file__)) + "/")
pytonium.initialize("app://index.html", 800, 600)

while pytonium.is_running():
    time.sleep(0.01)
    pytonium.update_message_loop()
    pytonium.set_state("app", "time", datetime.now().strftime("%H:%M:%S"))
```

---

## HTML Page

```html title="index.html"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Pytonium Simple App</title>
    <style>
        body {
            font-family: system-ui, -apple-system, sans-serif;
            max-width: 600px;
            margin: 60px auto;
            padding: 0 20px;
            background: #1a1a2e;
            color: #e0e0e0;
        }
        h1 { color: #bb86fc; }
        #greeting { margin: 20px 0; padding: 16px; background: #16213e; border-radius: 8px; }
        #clock { font-size: 2rem; font-weight: bold; color: #03dac6; }
        button {
            padding: 10px 20px;
            background: #bb86fc;
            color: #1a1a2e;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            cursor: pointer;
        }
        button:hover { background: #9a67ea; }
    </style>
</head>
<body>
    <h1>Pytonium Simple App</h1>
    <button id="greetBtn">Get Greeting from Python</button>
    <div id="greeting"></div>
    <p>Current time from Python state:</p>
    <div id="clock">--:--:--</div>

    <script>
        document.addEventListener("PytoniumReady", function () {
            // Call the Python function and display the result
            document.getElementById("greetBtn").addEventListener("click", async function () {
                const result = await api.get_greeting();
                document.getElementById("greeting").textContent =
                    result.message + " The answer is " + result.answer;
            });

            // Subscribe to state updates from Python
            Pytonium.registerForStateUpdates("app", "time", function (value) {
                document.getElementById("clock").textContent = value;
            });
        });
    </script>
</body>
</html>
```

---

## How It Works

### Custom Schemes

```python
pytonium.add_custom_scheme("app", os.path.dirname(os.path.abspath(__file__)) + "/")
```

This registers the `app://` URL scheme and maps it to the directory containing `main.py`. When the browser requests `app://index.html`, Pytonium serves the file from disk. This avoids the need for a local web server.

!!! info "Scheme Registration"
    Custom schemes must be registered **before** calling `initialize()`. CEF registers schemes during process startup, so they cannot be added after the browser is running.

### The `@returns_value_to_javascript` Decorator

```python
@returns_value_to_javascript("any")
def get_greeting():
    return {"message": "Hello from Python!", "answer": 42}
```

This decorator marks the function as one that returns a value to JavaScript. The `"any"` parameter specifies the return type hint. When called from JavaScript, the function returns a `Promise` that resolves with the Python return value:

```javascript
const result = await api.get_greeting();
```

Supported type hints: `"any"`, `"string"`, `"int"`, `"float"`, `"bool"`, `"list"`, `"dict"`.

### Binding Functions

```python
pytonium.bind_function_to_javascript(get_greeting, javascript_object="api")
```

This binds `get_greeting` to JavaScript as `api.get_greeting()`. The `javascript_object` parameter groups functions under a namespace object. You can bind multiple functions to the same object:

```python
pytonium.bind_function_to_javascript(get_greeting, javascript_object="api")
pytonium.bind_function_to_javascript(get_data, javascript_object="api")
# Available in JS as: api.get_greeting(), api.get_data()
```

### State Management

```python
pytonium.set_state("app", "time", datetime.now().strftime("%H:%M:%S"))
```

`set_state(namespace, key, value)` pushes a value from Python to the JavaScript side. The first argument is a namespace (for organizing state), the second is the key name, and the third is the value (string, number, dict, or list).

On the JavaScript side, subscribe to changes with `registerForStateUpdates`:

```javascript
Pytonium.registerForStateUpdates("app", "time", function (value) {
    document.getElementById("clock").textContent = value;
});
```

The callback fires every time the Python side calls `set_state` with the matching namespace and key.

### The PytoniumReady Event

```javascript
document.addEventListener("PytoniumReady", function () {
    // Safe to use Pytonium APIs here
});
```

!!! warning "Wait for PytoniumReady"
    The `Pytonium` global object and all bound functions (like `api`) are injected after the page loads. Code that uses these APIs must wait for the `PytoniumReady` event. Accessing them before this event fires will result in `undefined` errors.

### The Message Loop

```python
while pytonium.is_running():
    time.sleep(0.01)
    pytonium.update_message_loop()
```

Pytonium uses a manual message loop. `update_message_loop()` processes CEF events (rendering, input, network, IPC) and must be called regularly. The `time.sleep(0.01)` call prevents busy-waiting and keeps CPU usage low.

`is_running()` returns `False` when the user closes the window, which exits the loop.

---

## Next Steps

- **[Frameless Window](frameless-window.md)** -- Remove the native titlebar and build custom window chrome.
- **[JavaScript Bindings Guide](../guides/javascript-bindings.md)** -- Full reference for binding functions and returning values.
- **[State Management Guide](../guides/state-management.md)** -- Advanced patterns for shared state.
