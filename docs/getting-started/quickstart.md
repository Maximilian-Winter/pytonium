---
title: Quick Start
---

# Quick Start

This guide introduces the core concepts you need to build a Pytonium application: creating an instance, running the message loop, loading content, and waiting for the JavaScript bridge.

---

## Creating a Pytonium Instance

Every Pytonium application starts by creating an instance and calling `initialize()`:

```python
from Pytonium import Pytonium

p = Pytonium()
p.initialize("https://example.com", 800, 600)
```

The three arguments to `initialize()` are:

1. **`start_url`** -- The URL to load when the window opens.
2. **`init_width`** -- The initial window width in pixels.
3. **`init_height`** -- The initial window height in pixels.

This opens a native desktop window with a Chromium browser inside, displaying the given URL.

---

## The Message Loop

Pytonium uses CEF's message loop to process browser events (rendering, input, network requests, etc.). You must call `update_message_loop()` regularly to keep the browser responsive:

```python
import time
from Pytonium import Pytonium

p = Pytonium()
p.initialize("https://example.com", 800, 600)

while p.is_running():
    time.sleep(0.01)
    p.update_message_loop()
```

- **`is_running()`** returns `True` as long as the browser window is open.
- **`update_message_loop()`** processes all pending CEF events.
- **`time.sleep(0.01)`** prevents the loop from consuming 100% CPU. A 10ms sleep gives approximately 100 updates per second, which is more than enough for smooth rendering.

!!! warning "Do not skip the message loop"
    If you stop calling `update_message_loop()`, the browser window will freeze and become unresponsive. This call must happen on the main thread.

---

## Loading Content

### Remote URLs

Pass any `http://` or `https://` URL directly to `initialize()`:

```python
p.initialize("https://example.com", 800, 600)
```

### Local Files with `file://`

You can load local HTML files using the `file://` protocol:

```python
import os

html_path = os.path.abspath("index.html")
p.initialize(f"file:///{html_path}", 800, 600)
```

### Local Files with Custom Schemes

Custom schemes are the recommended way to serve local content. They provide clean URLs and avoid cross-origin issues that can occur with `file://`:

```python
import os
from Pytonium import Pytonium

p = Pytonium()

# Register a custom scheme before initializing
content_root = os.path.dirname(os.path.abspath(__file__)) + "/"
p.add_custom_scheme("myapp", content_root)

# Now use the scheme in your start URL
p.initialize("myapp://index.html", 800, 600)
```

!!! note "Call `add_custom_scheme()` before `initialize()`"
    Custom schemes must be registered before calling `initialize()`. The scheme name becomes a URL protocol, and the content root folder is the base directory for resolving file paths within that scheme.

With the example above, `myapp://styles/app.css` in your HTML would resolve to `<content_root>/styles/app.css` on disk.

---

## Setting a Window Title

The window title is set from your HTML `<title>` tag:

```html
<!DOCTYPE html>
<html>
<head>
    <title>My Pytonium App</title>
</head>
<body>
    <h1>Hello from Pytonium</h1>
</body>
</html>
```

You can also change the title dynamically from JavaScript:

```javascript
document.title = "New Window Title";
```

To react to title changes on the Python side, use the `on_title_change` callback:

```python
p.on_title_change(lambda title: print(f"Title changed to: {title}"))
```

---

## Setting a Custom Icon

Set a custom window icon before calling `initialize()`:

```python
p.set_custom_icon_path("icon.ico")
```

!!! tip
    On Windows, use `.ico` files for best results. The path can be relative to your working directory or an absolute path.

---

## The PytoniumReady Event

When Pytonium initializes a browser window, it injects JavaScript bindings (bound Python functions, state management, etc.) into the page. These bindings are not available immediately when the page starts loading -- they are injected after the CEF context is created.

Your JavaScript code **must wait for the `PytoniumReady` event** before accessing any Pytonium APIs:

```javascript
function init() {
    // Safe to use Pytonium bindings here
    console.log("Pytonium is ready!");
}

// Check if already ready (e.g., if script runs after the event fired)
if (window.PytoniumReady) {
    init();
} else {
    window.addEventListener('PytoniumReady', init);
}
```

!!! warning "Always check for PytoniumReady"
    If you call Pytonium JavaScript functions before the bindings are injected, you will get `undefined is not a function` errors. Always use the pattern shown above.

---

## Using Async Instead of a While Loop

If your application uses `asyncio`, you can replace the manual while-loop with `run_pytonium_async`:

```python
import asyncio
from Pytonium import Pytonium, run_pytonium_async

p = Pytonium()
p.initialize("https://example.com", 800, 600)

asyncio.run(run_pytonium_async(p))
```

This is functionally equivalent to the while-loop pattern but allows Pytonium to coexist with other async tasks:

```python
import asyncio
from Pytonium import Pytonium, run_pytonium_async

async def main():
    p = Pytonium()
    p.initialize("https://example.com", 800, 600)

    # Run Pytonium alongside other async tasks
    await asyncio.gather(
        run_pytonium_async(p),
        some_other_async_task(),
    )

asyncio.run(main())
```

`run_pytonium_async` accepts an optional `interval` parameter (default `0.016`, approximately 60 updates per second).

---

## Enabling Developer Tools

During development, you can enable the CEF debug context menu to access Chrome DevTools:

```python
p.set_show_debug_context_menu(True)
```

Right-click anywhere in the browser window and select the DevTools option to open the inspector.

---

## Complete Minimal Example

Putting it all together, here is a minimal application that loads a local HTML file using a custom scheme:

=== "main.py"

    ```python
    import time
    import os
    from Pytonium import Pytonium

    p = Pytonium()

    # Serve local files via custom scheme
    content_root = os.path.dirname(os.path.abspath(__file__)) + "/"
    p.add_custom_scheme("app", content_root)

    # Optional: custom icon and debug menu
    # p.set_custom_icon_path("icon.ico")
    p.set_show_debug_context_menu(True)

    p.initialize("app://index.html", 1024, 768)

    while p.is_running():
        time.sleep(0.01)
        p.update_message_loop()
    ```

=== "index.html"

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>My Pytonium App</title>
        <style>
            body {
                font-family: system-ui, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: #1a1a2e;
                color: #eee;
            }
        </style>
    </head>
    <body>
        <h1>Hello from Pytonium</h1>
    </body>
    </html>
    ```

---

## Next Steps

Now that you understand the basics, follow the [Your First App](first-app.md) tutorial to build a complete application with Python-JavaScript communication and state management.
