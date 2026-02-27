---
title: Frameless Window
---

# Frameless Window

This example demonstrates how to create a frameless window with a custom HTML/CSS titlebar, including drag regions and window control buttons (minimize, maximize, close).

!!! tip "Full Source"
    The complete source code is available in the [pytonium_examples repository](https://github.com/Maximilian-Winter/pytonium_examples).

---

## Python Entry Point

```python title="main.py"
import os
import time
from Pytonium import Pytonium

pytonium = Pytonium()

# Enable frameless mode before initialize
pytonium.set_frameless_window(True)

# Bind window control functions so JavaScript can call them
pytonium.bind_function_to_javascript(
    lambda: pytonium.drag_window(), javascript_object="window_controls",
    function_name="drag"
)
pytonium.bind_function_to_javascript(
    lambda: pytonium.minimize_window(), javascript_object="window_controls",
    function_name="minimize"
)
pytonium.bind_function_to_javascript(
    lambda: pytonium.maximize_window(), javascript_object="window_controls",
    function_name="maximize"
)
pytonium.bind_function_to_javascript(
    lambda: pytonium.close_window(), javascript_object="window_controls",
    function_name="close"
)

pytonium.add_custom_scheme("app", os.path.dirname(os.path.abspath(__file__)) + "/")
pytonium.initialize("app://index.html", 1024, 768)

while pytonium.is_running():
    time.sleep(0.01)
    pytonium.update_message_loop()
```

---

## HTML Page

```html title="index.html"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Frameless Window</title>
    <link rel="stylesheet" href="app://style.css">
</head>
<body>
    <div id="titlebar">
        <div id="titlebar-drag">
            <span class="title-text">My Frameless App</span>
        </div>
        <div id="titlebar-buttons">
            <button id="btn-minimize" class="titlebar-btn">&#x2014;</button>
            <button id="btn-maximize" class="titlebar-btn">&#x25A1;</button>
            <button id="btn-close" class="titlebar-btn close-btn">&#x2715;</button>
        </div>
    </div>
    <div id="content">
        <h1>Frameless Window Example</h1>
        <p>This window has no native titlebar. The titlebar above is pure HTML/CSS,
           and the buttons call Python functions to control the window.</p>
    </div>

    <script>
        document.addEventListener("PytoniumReady", function () {
            // Drag the window when the titlebar drag area is clicked
            document.getElementById("titlebar-drag").addEventListener("mousedown", function () {
                window_controls.drag();
            });

            // Window control buttons
            document.getElementById("btn-minimize").addEventListener("click", function () {
                window_controls.minimize();
            });
            document.getElementById("btn-maximize").addEventListener("click", function () {
                window_controls.maximize();
            });
            document.getElementById("btn-close").addEventListener("click", function () {
                window_controls.close();
            });
        });
    </script>
</body>
</html>
```

---

## Styles

```css title="style.css"
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: system-ui, -apple-system, sans-serif;
    background: #1a1a2e;
    color: #e0e0e0;
    overflow: hidden;
}

#titlebar {
    display: flex;
    align-items: center;
    height: 36px;
    background: #0f0f23;
    user-select: none;
    -webkit-user-select: none;
}

#titlebar-drag {
    flex: 1;
    height: 100%;
    display: flex;
    align-items: center;
    padding-left: 12px;
    cursor: default;
}

.title-text {
    font-size: 13px;
    color: #aaa;
}

#titlebar-buttons {
    display: flex;
    height: 100%;
}

.titlebar-btn {
    width: 46px;
    height: 100%;
    border: none;
    background: transparent;
    color: #ccc;
    font-size: 13px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
}

.titlebar-btn:hover {
    background: rgba(255, 255, 255, 0.1);
}

.close-btn:hover {
    background: #e81123;
    color: #fff;
}

#content {
    padding: 40px;
    height: calc(100vh - 36px);
    overflow-y: auto;
}

h1 { color: #bb86fc; margin-bottom: 16px; }
```

---

## How It Works

### Enabling Frameless Mode

```python
pytonium.set_frameless_window(True)
```

This must be called **before** `initialize()`. It removes the native window chrome (titlebar, borders) and gives you a raw window surface. Your HTML page occupies the entire window area, including where the titlebar would normally be.

### Window Control Methods

Pytonium provides four methods for controlling a frameless window:

| Method | Description |
|---|---|
| `drag_window()` | Starts a window drag operation from the current mouse position |
| `minimize_window()` | Minimizes the window to the taskbar |
| `maximize_window()` | Toggles between maximized and restored state |
| `close_window()` | Closes the window (causes `is_running()` to return `False`) |

These methods are bound to JavaScript so the HTML titlebar buttons can trigger them:

```python
pytonium.bind_function_to_javascript(
    lambda: pytonium.drag_window(),
    javascript_object="window_controls",
    function_name="drag"
)
```

### The Drag Region Pattern

The drag area is a `<div>` that covers the left portion of the titlebar. When the user presses the mouse button on this area, JavaScript calls `window_controls.drag()`, which initiates a native window drag operation:

```javascript
document.getElementById("titlebar-drag").addEventListener("mousedown", function () {
    window_controls.drag();
});
```

!!! note "Drag on mousedown"
    The drag function must be called on `mousedown`, not `click`. The native drag operation captures the mouse and handles the rest of the movement. By the time a `click` event fires, the drag opportunity has passed.

### Button Placement

The titlebar buttons are placed on the right side using flexbox, matching the standard Windows layout. Each button is 46px wide (the standard Windows titlebar button width) and spans the full titlebar height.

The close button has a distinct red hover color (`#e81123`) following the Windows convention.

---

## Variations

### Rounded Corners

On Windows 11, frameless windows automatically get rounded corners. If you want squared corners or a specific border radius, you can use CSS on the `<body>` or a wrapper `<div>`.

### Resizable Borders

By default, frameless windows can still be resized by dragging the edges. If you want to disable resizing, you can set a fixed window size or handle it in your window setup.

### Double-Click to Maximize

You can add a double-click handler on the drag area to toggle maximize:

```javascript
document.getElementById("titlebar-drag").addEventListener("dblclick", function () {
    window_controls.maximize();
});
```

---

## Next Steps

- **[Window Control Guide](../guides/window-control.md)** -- Full reference for window position, size, and state methods.
- **[Fullscreen Mode Guide](../guides/fullscreen.md)** -- Enter and exit fullscreen mode programmatically.
- **[Simple App](simple-app.md)** -- Start with the basics if you have not already.
