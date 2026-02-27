# Frameless Windows

Pytonium supports frameless (chromeless) windows -- windows with no native title
bar or borders.  This lets you build fully custom window chrome with HTML and
CSS, giving your application a unique look.

---

## Enabling Frameless Mode

Call `set_frameless_window(True)` **before** `initialize()`.

```python
from Pytonium import Pytonium

p = Pytonium()
p.set_frameless_window(True)
p.initialize("app://index.html", 1024, 768)
```

!!! warning "Must be called before initialize"
    `set_frameless_window()` configures the window creation flags.  It has no
    effect if called after the browser window already exists.

---

## Window Control Functions

With the native title bar removed, you need to provide your own minimize,
maximize, restore, and close buttons.  Bind the Pytonium window control methods
to JavaScript so your HTML buttons can drive them.

```python
from Pytonium import Pytonium, returns_value_to_javascript

p = Pytonium()
p.set_frameless_window(True)

# Bind window control methods
p.bind_function_to_javascript(p.minimize_window, name="minimize", javascript_object="window")
p.bind_function_to_javascript(p.maximize_window, name="maximize", javascript_object="window")
p.bind_function_to_javascript(p.restore_window, name="restore", javascript_object="window")
p.bind_function_to_javascript(p.close_window, name="close", javascript_object="window")

@returns_value_to_javascript("boolean")
def is_maximized():
    return p.is_maximized()

p.bind_function_to_javascript(is_maximized, name="isMaximized", javascript_object="window")
```

---

## Window Dragging

Without a native title bar, users cannot drag the window.  Pytonium provides
`drag_window(delta_x, delta_y)` for programmatic dragging.

Bind it to JavaScript and wire it to mouse events on your custom title bar:

```python
p.bind_function_to_javascript(p.drag_window, name="drag", javascript_object="window")
```

=== "JavaScript (drag handler)"

    ```javascript
    const titleBar = document.getElementById("titlebar");
    let isDragging = false;
    let lastX, lastY;

    titleBar.addEventListener("mousedown", (e) => {
        isDragging = true;
        lastX = e.screenX;
        lastY = e.screenY;
    });

    document.addEventListener("mousemove", (e) => {
        if (!isDragging) return;
        const deltaX = e.screenX - lastX;
        const deltaY = e.screenY - lastY;
        lastX = e.screenX;
        lastY = e.screenY;
        Pytonium.window.drag(deltaX, deltaY);
    });

    document.addEventListener("mouseup", () => {
        isDragging = false;
    });
    ```

=== "CSS (webkit drag region)"

    ```css
    /* Alternative: use CSS app-region for native-like drag behavior */
    #titlebar {
        -webkit-app-region: drag;
    }

    /* Buttons inside the drag region must be marked as no-drag */
    #titlebar button {
        -webkit-app-region: no-drag;
    }
    ```

!!! tip "CSS app-region"
    `-webkit-app-region: drag` provides a simpler alternative to JavaScript
    mouse tracking.  Elements marked with `no-drag` inside a drag region
    remain clickable.  Use this for simple cases; use the JavaScript approach
    when you need more control.

---

## Complete Example

A full frameless window application with a custom title bar featuring minimize,
maximize/restore, and close buttons.

=== "Python (main.py)"

    ```python
    import time
    from Pytonium import Pytonium, returns_value_to_javascript

    p = Pytonium()
    p.set_frameless_window(True)

    # Bind window controls
    p.bind_function_to_javascript(p.minimize_window, name="minimize", javascript_object="win")
    p.bind_function_to_javascript(p.maximize_window, name="maximize", javascript_object="win")
    p.bind_function_to_javascript(p.restore_window, name="restore", javascript_object="win")
    p.bind_function_to_javascript(p.close_window, name="close", javascript_object="win")
    p.bind_function_to_javascript(p.drag_window, name="drag", javascript_object="win")

    @returns_value_to_javascript("boolean")
    def is_maximized():
        return p.is_maximized()

    p.bind_function_to_javascript(is_maximized, name="isMaximized", javascript_object="win")

    p.add_custom_scheme("app", "./web/")
    p.initialize("app://index.html", 1024, 768)

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
        <title>Frameless Window</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }

            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                background: #1e1e2e;
                color: #cdd6f4;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }

            #titlebar {
                display: flex;
                align-items: center;
                justify-content: space-between;
                height: 36px;
                background: #181825;
                -webkit-app-region: drag;
                user-select: none;
                padding: 0 8px;
                flex-shrink: 0;
            }

            #titlebar .title {
                font-size: 13px;
                opacity: 0.8;
            }

            #titlebar .controls {
                display: flex;
                -webkit-app-region: no-drag;
            }

            #titlebar .controls button {
                width: 46px;
                height: 36px;
                border: none;
                background: transparent;
                color: #cdd6f4;
                font-size: 14px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            #titlebar .controls button:hover {
                background: rgba(255, 255, 255, 0.1);
            }

            #titlebar .controls button.close:hover {
                background: #e64553;
                color: white;
            }

            #content {
                flex: 1;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 2rem;
            }
        </style>
    </head>
    <body>
        <div id="titlebar">
            <span class="title">My Application</span>
            <div class="controls">
                <button id="btn-min" title="Minimize">&#x2014;</button>
                <button id="btn-max" title="Maximize">&#x25A1;</button>
                <button id="btn-close" class="close" title="Close">&#x2715;</button>
            </div>
        </div>

        <div id="content">
            <h1>Frameless Window Demo</h1>
        </div>

        <script>
            function onReady() {
                document.getElementById("btn-min").addEventListener("click", () => {
                    Pytonium.win.minimize();
                });

                document.getElementById("btn-max").addEventListener("click", async () => {
                    const maximized = await Pytonium.win.isMaximized();
                    if (maximized) {
                        Pytonium.win.restore();
                    } else {
                        Pytonium.win.maximize();
                    }
                });

                document.getElementById("btn-close").addEventListener("click", () => {
                    Pytonium.win.close();
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

## Combining with Custom Icons

Frameless windows pair well with custom application icons:

```python
p = Pytonium()
p.set_frameless_window(True)
p.set_custom_icon_path("./assets/icon.ico")
p.initialize("app://index.html", 1024, 768)
```

The icon appears in the Windows taskbar even though the native title bar is
hidden.
