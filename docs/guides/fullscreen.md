# Fullscreen Mode

Pytonium provides fullscreen support that fills the entire monitor with a
borderless window.  When entering fullscreen, the current window style and
position are saved and restored on exit.

---

## API

### Enter / Exit Fullscreen

```python
p.set_fullscreen(True)    # Enter fullscreen
p.set_fullscreen(False)   # Exit fullscreen
```

### Query Current State

```python
if p.is_fullscreen():
    print("Window is in fullscreen mode")
```

### Toggle

```python
p.toggle_fullscreen()     # Switch between fullscreen and windowed
```

---

## Fullscreen Change Callback

CEF can request fullscreen changes independently (for example, when the user
presses F11 or when JavaScript calls `document.requestFullscreen()`).  Use
`on_fullscreen_change()` to be notified of these requests.

```python
p.on_fullscreen_change(lambda fullscreen: print(f"Fullscreen: {fullscreen}"))
```

The callback receives a single `bool` argument: `True` when entering fullscreen,
`False` when exiting.

!!! tip "Wiring CEF requests to Pytonium"
    CEF's fullscreen request and Pytonium's window management are separate
    systems.  To make F11 and JavaScript fullscreen requests actually resize the
    window, wire the callback to `set_fullscreen()`:

    ```python
    p.on_fullscreen_change(lambda fs: p.set_fullscreen(fs))
    ```

---

## Implementation Details

On Windows, fullscreen is implemented as a borderless window that fills the
monitor:

1. The current window style (`GWL_STYLE`) and position (`RECT`) are saved.
2. The window style is changed to remove borders, title bar, and resize handles.
3. The window is resized to fill the monitor returned by `MonitorFromWindow()`.
4. On exit, the saved style and position are restored.

!!! note "Multi-monitor"
    The window goes fullscreen on whichever monitor it is currently on.
    `MonitorFromWindow` determines the correct monitor automatically.

!!! note "Safe re-entry"
    Calling `set_fullscreen(True)` when already fullscreen is a no-op -- it
    will not overwrite the saved window state.  Similarly, calling
    `set_fullscreen(False)` when already windowed has no effect.

---

## Example: Fullscreen Toggle Button

=== "Python (main.py)"

    ```python
    import time
    from Pytonium import Pytonium, returns_value_to_javascript

    p = Pytonium()

    # Wire CEF fullscreen requests (F11, JS requestFullscreen)
    p.on_fullscreen_change(lambda fs: p.set_fullscreen(fs))

    # Bind fullscreen controls to JavaScript
    p.bind_function_to_javascript(
        p.toggle_fullscreen, name="toggle", javascript_object="fullscreen"
    )

    @returns_value_to_javascript("boolean")
    def check_fullscreen():
        return p.is_fullscreen()

    p.bind_function_to_javascript(
        check_fullscreen, name="isActive", javascript_object="fullscreen"
    )

    p.add_custom_scheme("app", "./web/")
    p.initialize("app://index.html", 800, 600)

    while p.is_running():
        p.update_message_loop()
        time.sleep(0.016)

    p.shutdown()
    ```

=== "HTML (web/index.html)"

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Fullscreen Demo</title>
        <style>
            body {
                font-family: sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
                background: #1e1e2e;
                color: #cdd6f4;
            }
            button {
                padding: 12px 24px;
                font-size: 18px;
                border: 2px solid #89b4fa;
                background: transparent;
                color: #89b4fa;
                border-radius: 8px;
                cursor: pointer;
                margin-top: 16px;
            }
            button:hover {
                background: #89b4fa;
                color: #1e1e2e;
            }
        </style>
    </head>
    <body>
        <h1>Fullscreen Demo</h1>
        <p id="status">Windowed</p>
        <button id="toggle">Toggle Fullscreen</button>

        <script>
            function onReady() {
                const btn = document.getElementById("toggle");
                const status = document.getElementById("status");

                btn.addEventListener("click", async () => {
                    Pytonium.fullscreen.toggle();
                    // Brief delay for state to update
                    setTimeout(async () => {
                        const fs = await Pytonium.fullscreen.isActive();
                        status.textContent = fs ? "Fullscreen" : "Windowed";
                    }, 100);
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

## Example: Video Player Fullscreen

A common pattern is toggling fullscreen for media playback:

```python
# Python side
p.on_fullscreen_change(lambda fs: p.set_fullscreen(fs))

def enter_fullscreen():
    p.set_fullscreen(True)

def exit_fullscreen():
    p.set_fullscreen(False)

p.bind_function_to_javascript(enter_fullscreen, name="enter", javascript_object="fullscreen")
p.bind_function_to_javascript(exit_fullscreen, name="exit", javascript_object="fullscreen")
```

```javascript
// JavaScript side -- toggle fullscreen when video is double-clicked
document.getElementById("video").addEventListener("dblclick", () => {
    Pytonium.fullscreen.enter();
});

// Exit fullscreen with Escape key
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        Pytonium.fullscreen.exit();
    }
});
```
