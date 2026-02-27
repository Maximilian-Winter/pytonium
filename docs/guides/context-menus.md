# Context Menus

Pytonium lets you add custom entries to the browser's right-click context menu.
Entries are organized by **namespaces**, so you can swap between different menus
at runtime depending on application context.

---

## Adding a Single Entry

Use `add_context_menu_entry()` to add one item to the context menu.

```python
from Pytonium import Pytonium

def copy_selection():
    print("Custom copy triggered")

p = Pytonium()
p.add_context_menu_entry(copy_selection, display_name="Copy Selection")
p.initialize("https://example.com", 800, 600)
```

| Parameter                      | Type       | Default            | Description                                         |
|--------------------------------|------------|--------------------|-----------------------------------------------------|
| `context_menu_entry_function`  | `Callable` | *(required)*       | A callable invoked when the entry is clicked.       |
| `display_name`                 | `str`      | Function's `__name__` | The label shown in the context menu.             |
| `context_menu_namespace`       | `str`      | `"app"`            | Namespace for grouping menu entries.                |

!!! warning "Register before initialize"
    Context menu entries **must** be registered before calling `initialize()`.
    Entries added after browser creation will not appear.

---

## Adding Multiple Entries

Use `add_context_menu_entries()` to register several entries at once.

```python
def zoom_in():
    print("Zoom in")

def zoom_out():
    print("Zoom out")

def reset_zoom():
    print("Reset zoom")

p.add_context_menu_entries(
    [zoom_in, zoom_out, reset_zoom],
    display_names=["Zoom In", "Zoom Out", "Reset Zoom"]
)
```

| Parameter                        | Type             | Default              | Description                              |
|----------------------------------|------------------|----------------------|------------------------------------------|
| `context_menu_entry_functions`   | `list[Callable]` | *(required)*         | List of callables for each menu entry.   |
| `display_names`                  | `list[str]`      | `None` (uses `__name__`) | Optional display labels.             |
| `context_menu_namespace`         | `str`            | `"app"`              | Namespace for grouping.                  |

!!! tip "Automatic naming"
    If you omit `display_names`, each entry uses the Python function's `__name__`
    as its label.

---

## Adding Entries from an Object

Use `add_context_menu_entries_from_object()` to expose all public methods of a
Python object as context menu entries.

```python
class EditMenu:
    def cut(self):
        print("Cut")

    def copy(self):
        print("Copy")

    def paste(self):
        print("Paste")

edit = EditMenu()
p.add_context_menu_entries_from_object(
    edit,
    display_names=["Cut", "Copy", "Paste"],
    context_menu_namespace="edit"
)
```

| Parameter                       | Type          | Default              | Description                                    |
|---------------------------------|---------------|----------------------|------------------------------------------------|
| `context_menu_entries_object`   | `object`      | *(required)*         | Object whose public methods become entries.    |
| `display_names`                 | `list[str]`   | `None` (uses method names) | Optional display labels.                 |
| `context_menu_namespace`        | `str`         | `"app"`              | Namespace for grouping.                        |

---

## Namespaces

Namespaces let you maintain multiple context menus and switch between them at
runtime.  Only entries in the **active** namespace are shown when the user
right-clicks.

```python
# Register entries in different namespaces
p.add_context_menu_entry(zoom_in, display_name="Zoom In", context_menu_namespace="viewer")
p.add_context_menu_entry(zoom_out, display_name="Zoom Out", context_menu_namespace="viewer")

p.add_context_menu_entry(cut, display_name="Cut", context_menu_namespace="editor")
p.add_context_menu_entry(copy, display_name="Copy", context_menu_namespace="editor")
p.add_context_menu_entry(paste, display_name="Paste", context_menu_namespace="editor")

# Switch the active namespace at runtime
p.set_context_menu_namespace("editor")
```

!!! note "Default namespace"
    If you do not specify a `context_menu_namespace`, entries are placed in the
    `"app"` namespace by default.

---

## Debug Context Menu

Pytonium can show a built-in debug context menu with CEF DevTools entries.  This
is useful during development.

```python
p.set_show_debug_context_menu(True)
```

When enabled, the context menu includes options to open the Chrome DevTools
inspector.

!!! tip "Development only"
    Disable the debug context menu for production builds by setting
    `set_show_debug_context_menu(False)` or simply not calling it (disabled by
    default).

---

## Complete Example

=== "Python"

    ```python
    import time
    from Pytonium import Pytonium

    class AppMenus:
        def __init__(self, pytonium):
            self.p = pytonium
            self.zoom_level = 100

        def zoom_in(self):
            self.zoom_level = min(200, self.zoom_level + 10)
            self.p.execute_javascript(
                f"document.body.style.zoom = '{self.zoom_level}%'"
            )

        def zoom_out(self):
            self.zoom_level = max(50, self.zoom_level - 10)
            self.p.execute_javascript(
                f"document.body.style.zoom = '{self.zoom_level}%'"
            )

        def reset_zoom(self):
            self.zoom_level = 100
            self.p.execute_javascript("document.body.style.zoom = '100%'")

    def toggle_dark_mode():
        print("Toggling dark mode")

    def show_about():
        print("About: Pytonium Demo v1.0")

    p = Pytonium()

    # Zoom menu namespace
    menus = AppMenus(p)
    p.add_context_menu_entries_from_object(
        menus,
        display_names=["Zoom In", "Zoom Out", "Reset Zoom"],
        context_menu_namespace="zoom"
    )

    # App menu namespace
    p.add_context_menu_entries(
        [toggle_dark_mode, show_about],
        display_names=["Toggle Dark Mode", "About"],
        context_menu_namespace="app"
    )

    # Enable debug tools in development
    p.set_show_debug_context_menu(True)

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
        <title>Context Menu Demo</title>
    </head>
    <body>
        <h1>Right-click anywhere for the context menu</h1>
        <p>The menu entries are defined in Python.</p>
    </body>
    </html>
    ```
