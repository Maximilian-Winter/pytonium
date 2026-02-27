# Event Callbacks

Pytonium provides callbacks for browser window events such as title changes,
URL navigation, and fullscreen state changes.  These let your Python code
react to what is happening inside the browser in real time.

---

## Available Callbacks

### on_title_change

Fires whenever the HTML `<title>` element changes.

```python
p.on_title_change(lambda title: print(f"Title: {title}"))
```

| Parameter  | Type                      | Description                             |
|------------|---------------------------|-----------------------------------------|
| `callback` | `Callable[[str], None]`   | Receives the new title string.          |

**Use case:** Dynamically update the native window title or log navigation.

---

### on_address_change

Fires whenever the browser navigates to a new URL.

```python
p.on_address_change(lambda url: print(f"URL: {url}"))
```

| Parameter  | Type                      | Description                             |
|------------|---------------------------|-----------------------------------------|
| `callback` | `Callable[[str], None]`   | Receives the new URL string.            |

**Use case:** Track navigation, update breadcrumbs, or restrict allowed URLs.

---

### on_fullscreen_change

Fires when CEF requests a fullscreen state change (e.g., the user presses F11,
or JavaScript calls `document.requestFullscreen()`).

```python
p.on_fullscreen_change(lambda fullscreen: print(f"Fullscreen: {fullscreen}"))
```

| Parameter  | Type                      | Description                                        |
|------------|---------------------------|----------------------------------------------------|
| `callback` | `Callable[[bool], None]`  | Receives `True` when entering, `False` when exiting. |

!!! tip "Wire to set_fullscreen"
    The callback only notifies you of the request.  To actually resize the
    window, wire it to `set_fullscreen()`:

    ```python
    p.on_fullscreen_change(lambda fs: p.set_fullscreen(fs))
    ```

---

## When to Register

Callbacks can be registered **before or after** `initialize()`.  Unlike
bindings and context menus, event callbacks do not need to be set up before
the browser window is created.

```python
p = Pytonium()

# Register before initialize -- works
p.on_title_change(lambda title: print(title))
p.initialize("https://example.com", 800, 600)

# Register after initialize -- also works
p.on_address_change(lambda url: print(url))
```

!!! note "One callback per event"
    Each `on_*` method sets a single callback.  Calling it again replaces the
    previous callback.

---

## Complete Example: Dynamic Window Title

=== "Python (main.py)"

    ```python
    import time
    from Pytonium import Pytonium

    p = Pytonium()

    # Mirror the HTML title to console output
    p.on_title_change(lambda title: print(f"Window title: {title}"))

    # Log all navigation
    p.on_address_change(lambda url: print(f"Navigated to: {url}"))

    # Handle fullscreen requests from the browser
    p.on_fullscreen_change(lambda fs: p.set_fullscreen(fs))

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
        <title>Home</title>
    </head>
    <body>
        <h1>Event Callbacks Demo</h1>
        <button id="page1">Page 1</button>
        <button id="page2">Page 2</button>

        <script>
            document.getElementById("page1").addEventListener("click", () => {
                document.title = "Page 1 - Dashboard";
            });

            document.getElementById("page2").addEventListener("click", () => {
                document.title = "Page 2 - Settings";
            });
        </script>
    </body>
    </html>
    ```

When the user clicks the buttons, the Python console prints:

```
Window title: Page 1 - Dashboard
Window title: Page 2 - Settings
```

---

## Example: Navigation Guard

Use `on_address_change` to restrict navigation to allowed domains:

```python
ALLOWED_DOMAINS = ["example.com", "cdn.example.com"]

def check_navigation(url: str):
    from urllib.parse import urlparse
    domain = urlparse(url).hostname
    if domain and domain not in ALLOWED_DOMAINS:
        print(f"Blocked navigation to: {domain}")
        p.load_url("app://blocked.html")

p.on_address_change(check_navigation)
```

---

## Example: Title-Based Window Updates

Sync the HTML page title with external state:

```python
def handle_title(title: str):
    # Update a status bar, tray tooltip, or log
    if "Error" in title:
        print(f"ERROR detected in page: {title}")
    elif "Loading" in title:
        print("Page is loading...")
    else:
        print(f"Page ready: {title}")

p.on_title_change(handle_title)
```

---

## All Callbacks Summary

| Method                   | Callback Signature              | Trigger                              |
|--------------------------|---------------------------------|--------------------------------------|
| `on_title_change(cb)`    | `(title: str) -> None`          | HTML `<title>` changes               |
| `on_address_change(cb)`  | `(url: str) -> None`            | Browser navigates to new URL         |
| `on_fullscreen_change(cb)` | `(fullscreen: bool) -> None`  | CEF fullscreen request (F11, JS API) |
