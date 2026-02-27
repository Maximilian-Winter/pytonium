# Multi-Instance

Pytonium supports running multiple browser windows in a single process.  CEF is
initialized once globally, and each `Pytonium` instance manages its own browser
window with independent bindings, state handlers, and context menus.

---

## Creating Additional Windows

The first window is created with `initialize()`.  Additional windows are created
with `create_browser()`, which returns a browser ID.

```python
from Pytonium import Pytonium

# First window -- this also initializes CEF
p1 = Pytonium()
p1.initialize("https://example.com", 800, 600)

# Second window -- CEF is already initialized
p2 = Pytonium()
browser_id = p2.create_browser("https://example.org", 600, 400)
print(f"Second browser ID: {browser_id}")
```

| Parameter    | Type   | Default      | Description                         |
|--------------|--------|--------------|-------------------------------------|
| `url`        | `str`  | *(required)* | The URL to load.                    |
| `width`      | `int`  | *(required)* | Window width in pixels.             |
| `height`     | `int`  | *(required)* | Window height in pixels.            |
| `frameless`  | `bool` | `False`      | Whether the window is frameless.    |
| `icon_path`  | `str`  | `""`         | Path to a custom icon file.         |

!!! note "CEF must be initialized first"
    `create_browser()` requires that CEF is already running.  Call
    `initialize()` on at least one instance before using `create_browser()` on
    others.

---

## Browser IDs

Each browser window has a unique integer ID assigned by CEF.

```python
id1 = p1.get_browser_id()
id2 = p2.get_browser_id()
print(f"Window 1: {id1}, Window 2: {id2}")
```

Returns `-1` if no browser is open for that instance.

---

## CEF Initialization State

Use the class method `is_cef_initialized()` to check whether CEF has been
initialized.

```python
print(Pytonium.is_cef_initialized())  # True after any initialize() call
```

This is useful when writing library code that may or may not be the first to
create a window.

---

## The Global Message Loop

CEF uses a single global message loop.  Calling `update_message_loop()` on
**any** Pytonium instance processes events for **all** browser windows.

```python
import time

# Only need to call update_message_loop on one instance
while p1.is_running() or p2.is_running():
    p1.update_message_loop()
    time.sleep(0.016)
```

!!! warning "One loop drives all windows"
    Do not call `update_message_loop()` on multiple instances -- it is
    redundant and wasteful.  Pick one instance (typically the first) and use
    it for the loop.

---

## Independent Bindings and State

Each Pytonium instance has its own set of JavaScript bindings, state handlers,
and context menus.  There is no cross-talk between windows.

```python
# p1 gets its own bindings
def greet():
    print("Hello from window 1")

p1.bind_function_to_javascript(greet, javascript_object="app")

# p2 gets different bindings
def farewell():
    print("Goodbye from window 2")

p2.bind_function_to_javascript(farewell, javascript_object="app")
```

!!! note "Binding timing"
    For the first window (`initialize()`), bindings must be registered before
    `initialize()`.  For subsequent windows (`create_browser()`), bindings
    must be registered on the instance before calling `create_browser()`.

---

## Closing Windows

### Close a Single Window

```python
p2.close_browser()  # Closes p2's window, CEF keeps running
```

### Shutdown CEF

```python
p1.shutdown()  # Shuts down CEF entirely
```

!!! warning "Shutdown order"
    Call `shutdown()` only after all browser windows have been closed.
    Shutting down CEF while windows are still open may cause issues.

---

## Async Multi-Instance

Pytonium provides `run_pytonium_multi_async()` for running multiple instances
within an `asyncio` event loop.

```python
import asyncio
from Pytonium import Pytonium, run_pytonium_multi_async

p1 = Pytonium()
p1.initialize("https://example.com", 800, 600)

p2 = Pytonium()
p2.create_browser("https://example.org", 600, 400)

asyncio.run(run_pytonium_multi_async([p1, p2]))
```

The helper pumps the message loop while any instance in the list is still
running, then returns.

The `interval` parameter controls how frequently the loop is polled (default
`0.016` seconds, approximately 60fps):

```python
asyncio.run(run_pytonium_multi_async([p1, p2], interval=0.008))  # ~120fps
```

---

## Combining with Other Async Tasks

Use `asyncio.gather` to run the Pytonium loop alongside other coroutines.

```python
import asyncio
from Pytonium import Pytonium, run_pytonium_multi_async

async def background_data_fetch(p):
    """Periodically push data to the browser."""
    while p.is_running():
        p.set_state("data", "timestamp", time.time())
        await asyncio.sleep(1.0)

async def main():
    p1 = Pytonium()
    p1.initialize("https://example.com", 800, 600)

    p2 = Pytonium()
    p2.create_browser("https://example.org", 600, 400)

    await asyncio.gather(
        run_pytonium_multi_async([p1, p2]),
        background_data_fetch(p1),
    )

    p1.shutdown()

asyncio.run(main())
```

---

## Complete Example

=== "Python"

    ```python
    import time
    from Pytonium import Pytonium, returns_value_to_javascript

    # --- Window 1: Main application ---
    p1 = Pytonium()

    @returns_value_to_javascript("string")
    def get_app_name():
        return "Multi-Window Demo"

    p1.bind_function_to_javascript(get_app_name, javascript_object="app")
    p1.add_custom_scheme("main", "./web/main/")
    p1.initialize("main://index.html", 800, 600)

    # --- Window 2: Settings panel ---
    p2 = Pytonium()

    def apply_setting(key: str, value: str):
        print(f"Setting applied: {key} = {value}")
        # Push the setting to the main window's state
        p1.set_state("settings", key, value)

    p2.bind_function_to_javascript(apply_setting, javascript_object="settings")
    p2.add_custom_scheme("settings", "./web/settings/")
    p2.create_browser("settings://index.html", 400, 300, frameless=True)

    # --- Main loop ---
    while p1.is_running() or p2.is_running():
        p1.update_message_loop()
        time.sleep(0.016)

    p1.shutdown()
    ```

=== "Main window HTML"

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head><title>Main Window</title></head>
    <body>
        <h1 id="title">Loading...</h1>
        <script>
            window.addEventListener("PytoniumReady", async () => {
                const name = await Pytonium.app.get_app_name();
                document.getElementById("title").textContent = name;
            });
        </script>
    </body>
    </html>
    ```

=== "Settings window HTML"

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head><title>Settings</title></head>
    <body>
        <label>Theme:
            <select id="theme">
                <option value="dark">Dark</option>
                <option value="light">Light</option>
            </select>
        </label>
        <script>
            window.addEventListener("PytoniumReady", () => {
                document.getElementById("theme").addEventListener("change", (e) => {
                    Pytonium.settings.apply_setting("theme", e.target.value);
                });
            });
        </script>
    </body>
    </html>
    ```
