# State Management

Pytonium provides a built-in state management system for sharing data between
Python and JavaScript.  State is organized by **namespaces**, and both sides can
read, write, and subscribe to changes in real time.

---

## Concepts

- **Namespace** -- A logical grouping for related state (e.g. `"user"`,
  `"settings"`, `"dashboard"`).
- **Key** -- A string identifier within a namespace.
- **Value** -- Any serializable type: `int`, `float`, `str`, `bool`, `dict`, or
  `list`.

State flows bidirectionally:

```
Python  --set_state()--->  Shared State  <---setState()--  JavaScript
Python  <--update_state--  Shared State  --DOM event--->   JavaScript
```

---

## Setting State from Python

Use `set_state(namespace, key, value)` to push a value into the shared state.
Any subscribed handlers (Python or JavaScript) are notified immediately.

```python
p = Pytonium()

# Set individual values
p.set_state("user", "name", "Alice")
p.set_state("user", "score", 42)
p.set_state("settings", "theme", "dark")

# Set complex values
p.set_state("dashboard", "stats", {
    "cpu": 45.2,
    "memory": 68.1,
    "processes": ["python", "chrome", "vscode"]
})
```

---

## Subscribing from Python

Create a handler class with an `update_state(self, namespace, key, value)` method,
then register it with `add_state_handler()`.

```python
class DashboardHandler:
    def update_state(self, namespace: str, key: str, value):
        print(f"State changed: {namespace}.{key} = {value}")

handler = DashboardHandler()
p.add_state_handler(handler, namespaces=["dashboard", "settings"])
```

| Parameter       | Type          | Description                                         |
|-----------------|---------------|-----------------------------------------------------|
| `state_handler` | `object`      | An object with an `update_state` method.            |
| `namespaces`    | `list[str]`   | List of namespace strings to subscribe to.          |

!!! warning "Handler requirements"
    The handler object **must** have an `update_state` method.  If it does not,
    Pytonium emits a `UserWarning` and the handler is ignored.

!!! note "Register before initialize"
    State handlers should be registered before calling `initialize()` to ensure
    they receive all state changes from the start.

---

## JavaScript API

On the JavaScript side, state is accessed through the `Pytonium.appState`
namespace.

### Setting State

```javascript
Pytonium.appState.setState("user", "name", "Bob");
Pytonium.appState.setState("settings", "theme", "light");
```

### Getting State

```javascript
const name = Pytonium.appState.getState("user", "name");
console.log(name); // "Bob"
```

### Removing State

```javascript
Pytonium.appState.removeState("user", "score");
```

### Subscribing to Changes

Use `registerForStateUpdates()` to receive state changes as DOM events.

```javascript
Pytonium.appState.registerForStateUpdates(
    "onDashboardUpdate",   // Custom event name
    ["dashboard"],         // Namespaces to watch
    true,                  // Receive updates from JavaScript setState
    true                   // Receive updates from Python set_state
);
```

| Parameter              | Type       | Description                                       |
|------------------------|------------|---------------------------------------------------|
| `eventName`            | `string`   | The custom DOM event name to dispatch.             |
| `namespaces`           | `string[]` | Array of namespace strings to subscribe to.        |
| `getUpdatesFromJavascript` | `boolean` | Receive events triggered by JS `setState`.     |
| `getUpdatesFromPytonium`  | `boolean` | Receive events triggered by Python `set_state`.|

Once registered, listen for the event on `window`:

```javascript
window.addEventListener("onDashboardUpdate", (event) => {
    const { namespace, key, value } = event.detail;
    console.log(`${namespace}.${key} changed to`, value);
});
```

!!! tip "Selective subscriptions"
    You can create multiple registrations with different event names for
    different namespaces.  The `fromJS` and `fromPython` flags let you filter
    the direction of updates.

---

## Real-Time Update Pattern

A common pattern is pushing data from Python (e.g., sensor readings, system
stats) to the JavaScript UI in real time.

=== "Python (main.py)"

    ```python
    import time
    import random
    from Pytonium import Pytonium

    p = Pytonium()
    p.add_custom_scheme("app", "./web/")
    p.initialize("app://index.html", 800, 600)

    last_update = 0
    while p.is_running():
        p.update_message_loop()

        now = time.time()
        if now - last_update > 1.0:
            p.set_state("sensors", "temperature", round(random.uniform(20, 30), 1))
            p.set_state("sensors", "humidity", round(random.uniform(40, 80), 1))
            last_update = now

        time.sleep(0.016)

    p.shutdown()
    ```

=== "JavaScript (web/index.html)"

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Live Sensors</title>
        <style>
            .sensor { font-size: 2rem; margin: 1rem; }
        </style>
    </head>
    <body>
        <div class="sensor">Temperature: <span id="temp">--</span> C</div>
        <div class="sensor">Humidity: <span id="hum">--</span>%</div>

        <script>
            function onReady() {
                Pytonium.appState.registerForStateUpdates(
                    "sensorUpdate",
                    ["sensors"],
                    false,
                    true
                );

                window.addEventListener("sensorUpdate", (e) => {
                    const { key, value } = e.detail;
                    if (key === "temperature") {
                        document.getElementById("temp").textContent = value;
                    } else if (key === "humidity") {
                        document.getElementById("hum").textContent = value;
                    }
                });
            }

            if (window.PytoniumReady) {
                onReady();
            } else {
                window.addEventListener("PytoniumReady", onReady);
            }
        </script>
    </body>
    </html>
    ```

---

## Complete Example: Settings Panel

This example shows bidirectional state flow -- JavaScript sets preferences, and
Python reacts to them.

=== "Python"

    ```python
    import time
    from Pytonium import Pytonium

    class SettingsHandler:
        def update_state(self, namespace, key, value):
            if namespace == "settings":
                print(f"Setting changed: {key} = {value}")
                if key == "volume":
                    # Apply volume change in your audio system
                    pass

    p = Pytonium()
    handler = SettingsHandler()
    p.add_state_handler(handler, namespaces=["settings"])

    # Set defaults
    p.set_state("settings", "volume", 75)
    p.set_state("settings", "theme", "dark")

    p.add_custom_scheme("app", "./web/")
    p.initialize("app://settings.html", 600, 400)

    while p.is_running():
        p.update_message_loop()
        time.sleep(0.016)

    p.shutdown()
    ```

=== "JavaScript"

    ```javascript
    function onReady() {
        // Subscribe to settings changes from Python (for defaults)
        Pytonium.appState.registerForStateUpdates(
            "settingsChanged", ["settings"], true, true
        );

        window.addEventListener("settingsChanged", (e) => {
            const { key, value } = e.detail;
            if (key === "volume") {
                document.getElementById("volume").value = value;
            }
            if (key === "theme") {
                document.body.className = value;
            }
        });

        // Send changes back to Python
        document.getElementById("volume").addEventListener("input", (e) => {
            Pytonium.appState.setState("settings", "volume", parseInt(e.target.value));
        });

        document.getElementById("themeToggle").addEventListener("click", () => {
            const current = Pytonium.appState.getState("settings", "theme");
            const next = current === "dark" ? "light" : "dark";
            Pytonium.appState.setState("settings", "theme", next);
        });
    }

    if (window.PytoniumReady) {
        onReady();
    } else {
        window.addEventListener("PytoniumReady", onReady);
    }
    ```
