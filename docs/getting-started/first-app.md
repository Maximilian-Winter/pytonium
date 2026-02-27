---
title: Your First App
---

# Your First App

In this tutorial, you will build a complete Pytonium application that demonstrates the core features of the framework: binding Python functions to JavaScript, handling return values via Promises, managing shared state, and generating TypeScript definitions.

The app will display a greeting, call Python to get the current time, and subscribe to live state updates pushed from Python.

---

## Project Structure

Create a new directory for your project with two files:

```
my-first-app/
    main.py
    index.html
```

That is all you need. Pytonium serves your HTML through a custom URL scheme, so there is no build step or bundling required.

---

## Step 1: The HTML Frontend

Create `index.html` with a simple UI containing a greeting area, a button to call Python, and a live clock driven by state updates:

```html title="index.html"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>My First Pytonium App</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 2rem;
            padding: 2rem;
        }

        h1 {
            font-size: 2rem;
            color: #b388ff;
        }

        .card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 2rem;
            width: 100%;
            max-width: 500px;
            text-align: center;
        }

        .card h2 {
            font-size: 1.1rem;
            color: #aaa;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        #greeting-text {
            font-size: 1.4rem;
            color: #fff;
            min-height: 1.6em;
        }

        #clock-display {
            font-size: 2.5rem;
            font-weight: 700;
            color: #ffab40;
            font-variant-numeric: tabular-nums;
        }

        button {
            background: #7c4dff;
            color: #fff;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 2rem;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.2s;
        }

        button:hover {
            background: #651fff;
        }
    </style>
</head>
<body>
    <h1>My First Pytonium App</h1>

    <div class="card">
        <h2>Greeting from Python</h2>
        <p id="greeting-text">Press the button to get a greeting.</p>
        <br>
        <button id="greet-btn">Get Greeting</button>
    </div>

    <div class="card">
        <h2>Live Clock (State Updates)</h2>
        <p id="clock-display">--:--:--</p>
    </div>

    <script>
        function init() {
            // --- 1. Call a Python function that returns a value ---
            const btn = document.getElementById('greet-btn');
            const greetingText = document.getElementById('greeting-text');

            btn.addEventListener('click', async function () {
                // get_greeting() is a bound Python function.
                // Because it uses @returns_value_to_javascript,
                // it returns a JavaScript Promise.
                const result = await Pytonium.myApp.get_greeting("World");
                greetingText.textContent = result;
            });

            // --- 2. Subscribe to state updates from Python ---
            Pytonium.appState.registerForStateUpdates(
                "clock-update",     // event name (arbitrary)
                ["clock"],          // namespaces to watch
                false,              // get updates from JavaScript setState calls
                true                // get updates from Python set_state calls
            );

            window.addEventListener("clock-update", function (event) {
                const clockDisplay = document.getElementById('clock-display');
                clockDisplay.textContent = event.detail.value;
            });
        }

        // Wait for Pytonium bindings to be injected
        if (window.PytoniumReady) {
            init();
        } else {
            window.addEventListener('PytoniumReady', init);
        }
    </script>
</body>
</html>
```

There are two key interactions happening here:

1. **Calling Python**: The button click calls `Pytonium.myApp.get_greeting("World")`, which is a Python function bound under the `myApp` JavaScript namespace. It returns a Promise that resolves with the Python return value.

2. **State subscriptions**: `registerForStateUpdates` subscribes to changes in the `"clock"` namespace. Whenever Python calls `set_state("clock", ...)`, a custom DOM event fires with the new value in `event.detail.value`.

---

## Step 2: The Python Backend

Create `main.py` with the Pytonium setup, function bindings, and a state handler:

```python title="main.py"
import os
import time
from datetime import datetime
from Pytonium import Pytonium, returns_value_to_javascript


# -- Bound functions ----------------------------------------------------------

@returns_value_to_javascript(return_type="string")
def get_greeting(name):
    """Called from JavaScript. Returns a greeting string via a Promise."""
    current_time = datetime.now().strftime("%H:%M:%S")
    return f"Hello, {name}! The time is {current_time}."


# -- State handler ------------------------------------------------------------

class ClockStateHandler:
    """Receives state change notifications from the 'clock' namespace."""

    def update_state(self, namespace, key, value):
        print(f"[State] {namespace}.{key} = {value}")


# -- Main application ---------------------------------------------------------

def main():
    p = Pytonium()

    # Serve local files through a custom scheme
    content_root = os.path.dirname(os.path.abspath(__file__)) + "/"
    p.add_custom_scheme("app", content_root)

    # Bind Python function to JavaScript under the "myApp" namespace.
    # In JavaScript this becomes: Pytonium.myApp.get_greeting(name)
    p.bind_function_to_javascript(get_greeting, javascript_object="myApp")

    # Register a state handler that listens to the "clock" namespace
    clock_handler = ClockStateHandler()
    p.add_state_handler(clock_handler, ["clock"])

    # Enable DevTools context menu during development
    p.set_show_debug_context_menu(True)

    # Generate TypeScript definitions for IDE auto-completion
    p.generate_typescript_definitions("pytonium.d.ts")

    # Initialize the browser window
    p.initialize("app://index.html", 600, 500)

    # Main loop: update CEF and push state
    last_second = -1
    while p.is_running():
        time.sleep(0.01)
        p.update_message_loop()

        # Push the current time to JavaScript once per second
        now = datetime.now()
        if now.second != last_second:
            last_second = now.second
            p.set_state("clock", "time", now.strftime("%H:%M:%S"))


if __name__ == "__main__":
    main()
```

Let's walk through each section.

---

## Step 3: Understanding the Code

### The `@returns_value_to_javascript` Decorator

```python
@returns_value_to_javascript(return_type="string")
def get_greeting(name):
    return f"Hello, {name}! The time is {current_time}."
```

This decorator tells Pytonium that the function returns a value back to JavaScript. Without it, the function would be fire-and-forget (no return value). The `return_type` parameter is used when generating TypeScript definitions.

Supported `return_type` values: `"string"`, `"number"`, `"boolean"`, `"object"`, `"any"`.

!!! info "How return values work"
    When JavaScript calls a decorated function, Pytonium returns a **Promise**. The Python function executes, and its return value is automatically serialized and sent back to resolve the Promise. Supported Python types: `str`, `int`, `float`, `bool`, `dict`, `list`.

### Binding Functions to JavaScript

```python
p.bind_function_to_javascript(get_greeting, javascript_object="myApp")
```

This makes `get_greeting` callable from JavaScript as `Pytonium.myApp.get_greeting(name)`. The `javascript_object` parameter groups functions under a namespace. If omitted, the function is available directly on the `Pytonium` object.

You can also bind multiple functions at once:

```python
p.bind_functions_to_javascript(
    [func_a, func_b, func_c],
    javascript_object="myApp"
)
```

Or bind all public methods of an object:

```python
p.bind_object_methods_to_javascript(my_api_object, javascript_object="api")
```

### State Management

State management in Pytonium works through namespaced key-value pairs that are shared between Python and JavaScript.

**Setting state from Python:**

```python
p.set_state("clock", "time", "14:30:00")
```

**Subscribing in JavaScript:**

```javascript
Pytonium.appState.registerForStateUpdates(
    "clock-update",  // DOM event name to fire
    ["clock"],       // namespaces to watch
    false,           // notify on JS-side setState calls
    true             // notify on Python-side set_state calls
);

window.addEventListener("clock-update", function (event) {
    // event.detail.namespace -- the namespace that changed
    // event.detail.key       -- the key that changed
    // event.detail.value     -- the new value
    console.log(event.detail.value);
});
```

**Adding a state handler on the Python side:**

```python
class ClockStateHandler:
    def update_state(self, namespace, key, value):
        print(f"{namespace}.{key} = {value}")

p.add_state_handler(ClockStateHandler(), ["clock"])
```

The handler's `update_state` method is called whenever state changes in any of the subscribed namespaces.

!!! tip "State is bidirectional"
    JavaScript can also set state with `Pytonium.appState.setState(namespace, key, value)`, and Python state handlers will receive the update if they are subscribed to that namespace.

### The PytoniumReady Guard

```javascript
if (window.PytoniumReady) {
    init();
} else {
    window.addEventListener('PytoniumReady', init);
}
```

This pattern ensures your JavaScript code does not run until Pytonium's bindings are available. The `PytoniumReady` event fires once after CEF injects the JavaScript bridge. The `window.PytoniumReady` boolean check handles the case where your script loads after the event has already fired.

---

## Step 4: Generate TypeScript Definitions

The call to `generate_typescript_definitions` in `main.py` creates a `pytonium.d.ts` file:

```python
p.generate_typescript_definitions("pytonium.d.ts")
```

This file provides type information for your IDE. After running the app once, you will have a `pytonium.d.ts` file that looks something like:

```typescript
declare namespace Pytonium {
  export namespace myApp {
    function get_greeting(name: any): string;
  }
  export namespace appState {
    function registerForStateUpdates(
      eventName: string,
      namespaces: string[],
      getUpdatesFromJavascript: boolean,
      getUpdatesFromPytonium: boolean
    ): void;
    function setState(namespace: string, key: string, value: any): void;
    function getState(namespace: string, key: string): any;
    function removeState(namespace: string, key: string): void;
  }
}

interface Window {
  PytoniumReady: boolean;
}

interface WindowEventMap {
  PytoniumReady: Event;
}
```

Place this file in your project root or wherever your editor can discover it. VS Code and other TypeScript-aware editors will pick it up automatically and provide auto-completion for all your bound functions.

---

## Step 5: Run the App

Run your application from the project directory:

```bash
python main.py
```

You should see:

1. A window opens showing your UI with a dark gradient background.
2. Click **"Get Greeting"** -- it calls Python and displays the returned greeting.
3. The live clock updates every second, driven by `set_state` from the Python main loop.
4. A `pytonium.d.ts` file is created in your project directory.

!!! note "First run"
    If this is your first time running Pytonium after installation, there will be a brief delay while CEF binaries are extracted. This only happens once.

---

## Complete File Listing

Here are both files for easy copy-paste:

=== "main.py"

    ```python
    import os
    import time
    from datetime import datetime
    from Pytonium import Pytonium, returns_value_to_javascript


    @returns_value_to_javascript(return_type="string")
    def get_greeting(name):
        """Called from JavaScript. Returns a greeting string via a Promise."""
        current_time = datetime.now().strftime("%H:%M:%S")
        return f"Hello, {name}! The time is {current_time}."


    class ClockStateHandler:
        """Receives state change notifications from the 'clock' namespace."""

        def update_state(self, namespace, key, value):
            print(f"[State] {namespace}.{key} = {value}")


    def main():
        p = Pytonium()

        content_root = os.path.dirname(os.path.abspath(__file__)) + "/"
        p.add_custom_scheme("app", content_root)

        p.bind_function_to_javascript(get_greeting, javascript_object="myApp")

        clock_handler = ClockStateHandler()
        p.add_state_handler(clock_handler, ["clock"])

        p.set_show_debug_context_menu(True)
        p.generate_typescript_definitions("pytonium.d.ts")

        p.initialize("app://index.html", 600, 500)

        last_second = -1
        while p.is_running():
            time.sleep(0.01)
            p.update_message_loop()

            now = datetime.now()
            if now.second != last_second:
                last_second = now.second
                p.set_state("clock", "time", now.strftime("%H:%M:%S"))


    if __name__ == "__main__":
        main()
    ```

=== "index.html"

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>My First Pytonium App</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: system-ui, -apple-system, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #e0e0e0;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 2rem;
                padding: 2rem;
            }
            h1 { font-size: 2rem; color: #b388ff; }
            .card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 2rem;
                width: 100%;
                max-width: 500px;
                text-align: center;
            }
            .card h2 {
                font-size: 1.1rem;
                color: #aaa;
                margin-bottom: 1rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            #greeting-text { font-size: 1.4rem; color: #fff; min-height: 1.6em; }
            #clock-display {
                font-size: 2.5rem;
                font-weight: 700;
                color: #ffab40;
                font-variant-numeric: tabular-nums;
            }
            button {
                background: #7c4dff;
                color: #fff;
                border: none;
                border-radius: 8px;
                padding: 0.75rem 2rem;
                font-size: 1rem;
                cursor: pointer;
                transition: background 0.2s;
            }
            button:hover { background: #651fff; }
        </style>
    </head>
    <body>
        <h1>My First Pytonium App</h1>

        <div class="card">
            <h2>Greeting from Python</h2>
            <p id="greeting-text">Press the button to get a greeting.</p>
            <br>
            <button id="greet-btn">Get Greeting</button>
        </div>

        <div class="card">
            <h2>Live Clock (State Updates)</h2>
            <p id="clock-display">--:--:--</p>
        </div>

        <script>
            function init() {
                const btn = document.getElementById('greet-btn');
                const greetingText = document.getElementById('greeting-text');

                btn.addEventListener('click', async function () {
                    const result = await Pytonium.myApp.get_greeting("World");
                    greetingText.textContent = result;
                });

                Pytonium.appState.registerForStateUpdates(
                    "clock-update", ["clock"], false, true
                );

                window.addEventListener("clock-update", function (event) {
                    document.getElementById('clock-display').textContent =
                        event.detail.value;
                });
            }

            if (window.PytoniumReady) {
                init();
            } else {
                window.addEventListener('PytoniumReady', init);
            }
        </script>
    </body>
    </html>
    ```

---

## What You Learned

In this tutorial you used the following Pytonium features:

| Feature | What it does |
|---|---|
| `add_custom_scheme()` | Registers a custom URL protocol for serving local files |
| `@returns_value_to_javascript` | Marks a Python function as returning a value to JS (via Promise) |
| `bind_function_to_javascript()` | Makes a Python function callable from JavaScript |
| `add_state_handler()` | Registers a Python object to receive state change notifications |
| `set_state()` | Pushes a value into the shared state system |
| `registerForStateUpdates()` | Subscribes JavaScript to state changes (fires DOM events) |
| `generate_typescript_definitions()` | Creates a `.d.ts` file for IDE auto-completion |
| `PytoniumReady` event | Ensures JS code runs only after Pytonium bindings are available |

---

## Next Steps

- **[JavaScript Bindings Guide](../guides/javascript-bindings.md)** -- Deep dive into binding functions, objects, and handling return types.
- **[State Management Guide](../guides/state-management.md)** -- Advanced state patterns, multiple namespaces, and bidirectional updates.
- **[Frameless Windows Guide](../guides/frameless-windows.md)** -- Build a custom title bar and window controls with HTML/CSS.
- **[Examples](../examples/index.md)** -- Browse more complete example applications.
