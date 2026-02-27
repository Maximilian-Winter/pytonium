# Window Control

Pytonium provides a comprehensive set of methods for controlling the browser
window's position, size, state, and appearance from Python.

---

## Window Position

### Getting the Position

```python
x, y = p.get_window_position()
print(f"Window is at ({x}, {y})")
```

Returns a `tuple[int, int]` of the top-left corner coordinates in screen pixels.

### Setting the Position

```python
p.set_window_position(100, 200)
```

Moves the window so its top-left corner is at screen coordinates `(100, 200)`.

---

## Window Size

### Getting the Size

```python
width, height = p.get_window_size()
print(f"Window size: {width}x{height}")
```

Returns a `tuple[int, int]` of the window's width and height in pixels.

### Setting the Size

```python
p.set_window_size(1280, 720)
```

### Resizing with an Anchor

`resize_window()` resizes the window while keeping a specific corner fixed.

```python
p.resize_window(1920, 1080, anchor=0)
```

| Anchor Value | Corner Kept Fixed |
|--------------|-------------------|
| `0`          | Top-left (default)|
| `1`          | Top-right         |
| `2`          | Bottom-left       |
| `3`          | Bottom-right      |

!!! tip "Anchor use case"
    Anchored resizing is useful for sidebar-style applications or panels that
    should grow in a specific direction without shifting position.

---

## Window State

### Minimize, Maximize, Restore

```python
p.minimize_window()   # Minimize to taskbar
p.maximize_window()   # Maximize to fill screen
p.restore_window()    # Restore from maximized state
```

### Checking Maximized State

```python
if p.is_maximized():
    p.restore_window()
else:
    p.maximize_window()
```

### Closing the Window

```python
p.close_window()
```

---

## Fullscreen

Pytonium supports true fullscreen mode (borderless, filling the entire monitor).

```python
p.set_fullscreen(True)    # Enter fullscreen
p.set_fullscreen(False)   # Exit fullscreen
p.toggle_fullscreen()     # Toggle between states

if p.is_fullscreen():
    print("Currently in fullscreen")
```

!!! note "Fullscreen guide"
    For detailed fullscreen usage including event callbacks, see the
    [Fullscreen Mode](fullscreen.md) guide.

---

## Window Dragging

For frameless windows, `drag_window()` moves the window by a relative offset.

```python
p.drag_window(delta_x=10, delta_y=5)
```

This is typically bound to JavaScript and driven by mouse events on a custom
title bar.  See the [Frameless Windows](frameless-windows.md) guide for a
complete example.

---

## Native Window Handle

Get the OS-level window handle for advanced interop with native APIs.

```python
hwnd = p.get_native_window_handle()
print(f"Window handle: {hwnd}")
```

| Platform | Return Value                        |
|----------|-------------------------------------|
| Windows  | `HWND` as an integer                |
| Linux    | X11 window ID as an integer         |

Returns `0` if the browser is not initialized.

!!! tip "Win32 interop"
    The `HWND` can be passed to `ctypes` calls for Win32 API operations like
    setting window transparency, registering hotkeys, or embedding child
    windows.

---

## Parent Window

Set a parent window handle to create the browser as a child window.

```python
# Create the browser as a child of another window
p.set_parent_window(parent_hwnd)
p.initialize("https://example.com", 800, 600)

# Clear parent (standalone mode)
p.set_parent_window(0)
```

!!! warning "Call before initialize"
    `set_parent_window()` must be called before `initialize()`.  It configures
    the window creation flags (`WS_CHILD` vs `WS_POPUP` on Windows).

---

## Loading URLs

Navigate to a new URL after the browser is already initialized.

```python
p.initialize("https://example.com", 800, 600)

# Later, navigate to a different page
p.load_url("https://example.org/dashboard")
```

---

## Custom Icon

Set a custom window icon (appears in the title bar and taskbar).

```python
p.set_custom_icon_path("./assets/icon.ico")
p.initialize("app://index.html", 800, 600)
```

!!! warning "Call before initialize"
    `set_custom_icon_path()` must be called before `initialize()`.

!!! note "Platform note"
    On Windows, use `.ico` format.  On Linux, standard image formats are
    supported.

---

## Complete Example

=== "Python (window positioning)"

    ```python
    import time
    from Pytonium import Pytonium, returns_value_to_javascript

    p = Pytonium()

    @returns_value_to_javascript("object")
    def get_position():
        x, y = p.get_window_position()
        return {"x": x, "y": y}

    @returns_value_to_javascript("object")
    def get_size():
        w, h = p.get_window_size()
        return {"width": w, "height": h}

    def move_to(x: int, y: int):
        p.set_window_position(x, y)

    def resize_to(width: int, height: int):
        p.set_window_size(width, height)

    def center_window():
        # Simple centering on a 1920x1080 screen
        w, h = p.get_window_size()
        p.set_window_position((1920 - w) // 2, (1080 - h) // 2)

    p.bind_function_to_javascript(get_position, javascript_object="win")
    p.bind_function_to_javascript(get_size, javascript_object="win")
    p.bind_function_to_javascript(move_to, javascript_object="win")
    p.bind_function_to_javascript(resize_to, javascript_object="win")
    p.bind_function_to_javascript(center_window, name="center", javascript_object="win")

    p.add_custom_scheme("app", "./web/")
    p.initialize("app://index.html", 800, 600)

    while p.is_running():
        p.update_message_loop()
        time.sleep(0.016)

    p.shutdown()
    ```

=== "JavaScript"

    ```javascript
    async function showWindowInfo() {
        const pos = await Pytonium.win.get_position();
        const size = await Pytonium.win.get_size();
        console.log(`Position: (${pos.x}, ${pos.y})`);
        console.log(`Size: ${size.width}x${size.height}`);
    }

    // Move window to top-left corner
    Pytonium.win.move_to(0, 0);

    // Resize to 1280x720
    Pytonium.win.resize_to(1280, 720);

    // Center on screen
    Pytonium.win.center();
    ```

---

## API Reference Summary

| Method                         | Pre-init | Description                                  |
|--------------------------------|----------|----------------------------------------------|
| `get_window_position()`        | No       | Returns `(x, y)` tuple                       |
| `set_window_position(x, y)`    | No       | Move window to screen coordinates             |
| `get_window_size()`            | No       | Returns `(width, height)` tuple               |
| `set_window_size(w, h)`        | No       | Resize window                                 |
| `resize_window(w, h, anchor)`  | No       | Resize with fixed corner                      |
| `minimize_window()`            | No       | Minimize to taskbar                           |
| `maximize_window()`            | No       | Maximize to fill screen                       |
| `restore_window()`             | No       | Restore from maximized                        |
| `is_maximized()`               | No       | Check if maximized                            |
| `close_window()`               | No       | Close the window                              |
| `set_fullscreen(bool)`         | No       | Enter/exit fullscreen                         |
| `is_fullscreen()`              | No       | Check fullscreen state                        |
| `toggle_fullscreen()`          | No       | Toggle fullscreen                             |
| `drag_window(dx, dy)`          | No       | Drag window by offset                         |
| `get_native_window_handle()`   | No       | Get OS window handle                          |
| `set_parent_window(hwnd)`      | Yes      | Set parent window                             |
| `load_url(url)`                | No       | Navigate to URL                               |
| `set_custom_icon_path(path)`   | Yes      | Set window icon                               |
| `set_frameless_window(bool)`   | Yes      | Enable frameless mode                         |

*Pre-init = "Yes" means the method must be called before `initialize()`.*
