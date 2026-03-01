# Context Menus

Pytonium lets you build rich, fully customizable right-click context menus
from Python. Menus support **standard items**, **check items**, **radio items**,
**separators**, **submenus**, **accelerators**, and **runtime modifications** —
all organized by **namespaces** so you can swap between different menus at
runtime.

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

## Separators

Use `add_context_menu_separator()` to insert a visual divider between menu
items.

```python
p.add_context_menu_entry(cut, "Cut")
p.add_context_menu_entry(copy, "Copy")
p.add_context_menu_entry(paste, "Paste")
p.add_context_menu_separator()
p.add_context_menu_entry(select_all, "Select All")
```

| Parameter                | Type   | Default  | Description                           |
|--------------------------|--------|----------|---------------------------------------|
| `context_menu_namespace` | `str`  | `"app"`  | Namespace where the separator appears.|

---

## Check Items

Use `add_context_menu_check_item()` to add a togglable checkbox entry. The
checked state is **automatically toggled** each time the user clicks the item.

```python
def toggle_bold(params):
    print(f"Bold is now toggled")

p.add_context_menu_check_item(toggle_bold, display_name="Bold", checked=False)
```

| Parameter                      | Type       | Default            | Description                                    |
|--------------------------------|------------|--------------------|------------------------------------------------|
| `context_menu_entry_function`  | `Callable` | *(required)*       | Called when the item is clicked.               |
| `display_name`                 | `str`      | Function's `__name__` | Label shown in the menu.                    |
| `checked`                      | `bool`     | `False`            | Initial checked state.                         |
| `context_menu_namespace`       | `str`      | `"app"`            | Namespace for grouping.                        |

---

## Radio Items

Use `add_context_menu_radio_item()` to add a radio button entry. Items with
the same `group_id` are mutually exclusive — selecting one automatically
deselects the others in the group.

```python
def align_left():
    print("Left alignment")

def align_center():
    print("Center alignment")

def align_right():
    print("Right alignment")

p.add_context_menu_radio_item(align_left, "Left", group_id=1)
p.add_context_menu_radio_item(align_center, "Center", group_id=1)
p.add_context_menu_radio_item(align_right, "Right", group_id=1)
```

| Parameter                      | Type       | Default            | Description                                    |
|--------------------------------|------------|--------------------|------------------------------------------------|
| `context_menu_entry_function`  | `Callable` | *(required)*       | Called when the item is selected.              |
| `display_name`                 | `str`      | Function's `__name__` | Label shown in the menu.                    |
| `group_id`                     | `int`      | `0`                | Radio group — only one per group is selected.  |
| `context_menu_namespace`       | `str`      | `"app"`            | Namespace for grouping.                        |

---

## Submenus

Use `add_context_menu_submenu()` to create a nested submenu. The children of
the submenu are items registered under the `sub_namespace`.

```python
# Create the submenu entry
p.add_context_menu_submenu("Alignment", sub_namespace="align")

# Add items to the submenu's namespace
p.add_context_menu_radio_item(align_left, "Left", group_id=1,
                              context_menu_namespace="align")
p.add_context_menu_radio_item(align_center, "Center", group_id=1,
                              context_menu_namespace="align")
p.add_context_menu_radio_item(align_right, "Right", group_id=1,
                              context_menu_namespace="align")
```

| Parameter                | Type   | Default   | Description                                       |
|--------------------------|--------|-----------|---------------------------------------------------|
| `display_name`           | `str`  | *(required)* | Label shown for the submenu.                   |
| `sub_namespace`          | `str`  | *(required)* | Namespace whose entries fill the submenu.       |
| `context_menu_namespace` | `str`  | `"app"`   | Parent namespace where the submenu appears.       |

!!! tip "Nested submenus"
    You can nest submenus by adding a `add_context_menu_submenu()` entry
    inside another submenu's namespace, pointing to yet another sub-namespace.

---

## Accelerators

Use `set_context_menu_item_accelerator()` to assign a keyboard shortcut label
to a menu item. The shortcut is **displayed** next to the item label.

```python
# Assuming items are at indices 0, 1, 2 in their namespace
p.set_context_menu_item_accelerator(0, ord('X'), ctrl=True)           # Ctrl+X
p.set_context_menu_item_accelerator(1, ord('C'), ctrl=True)           # Ctrl+C
p.set_context_menu_item_accelerator(2, ord('V'), ctrl=True)           # Ctrl+V
p.set_context_menu_item_accelerator(3, ord('A'), ctrl=True, shift=True)  # Ctrl+Shift+A
```

| Parameter                | Type   | Default  | Description                                     |
|--------------------------|--------|----------|-------------------------------------------------|
| `item_index`             | `int`  | *(required)* | Index of the item in its namespace.          |
| `key_code`               | `int`  | *(required)* | Virtual key code (e.g. `ord('C')`).          |
| `ctrl`                   | `bool` | `False`  | Require Ctrl modifier.                          |
| `shift`                  | `bool` | `False`  | Require Shift modifier.                         |
| `alt`                    | `bool` | `False`  | Require Alt modifier.                           |
| `context_menu_namespace` | `str`  | `"app"`  | Namespace of the item.                          |

---

## Runtime Modifications

After registering menu items, you can modify their properties at runtime.
Changes take effect the **next time** the context menu is shown.

### Enable / Disable

```python
# Disable the Copy item (index 1) — it appears greyed out
p.set_context_menu_item_enabled(1, False)

# Re-enable it
p.set_context_menu_item_enabled(1, True)
```

### Checked State

```python
# Programmatically check or uncheck a check item
p.set_context_menu_item_checked(0, True)
```

### Visibility

```python
# Hide an item entirely
p.set_context_menu_item_visible(2, False)
```

### Clear All Entries

```python
# Remove all entries from a namespace (allows full runtime rebuild)
p.clear_context_menu_entries("app")
```

| Method                              | Parameters                                   | Description                         |
|-------------------------------------|----------------------------------------------|-------------------------------------|
| `set_context_menu_item_enabled()`   | `item_index`, `enabled`, `namespace="app"`   | Enable or disable (grey out) item.  |
| `set_context_menu_item_checked()`   | `item_index`, `checked`, `namespace="app"`   | Set check/radio checked state.      |
| `set_context_menu_item_visible()`   | `item_index`, `visible`, `namespace="app"`   | Show or hide an item.               |
| `clear_context_menu_entries()`      | `namespace="app"`                            | Remove all items from a namespace.  |

---

## Context Data (ContextMenuParams)

When the user right-clicks, Pytonium captures context information about the
click location. If your handler accepts a parameter, it will receive a
`ContextMenuParams` object with the following fields:

```python
from Pytonium import ContextMenuParams

def my_handler(params: ContextMenuParams):
    print(f"Clicked at ({params.x}, {params.y})")
    print(f"Selected text: {params.selection_text}")
    print(f"Link URL: {params.link_url}")
```

| Field              | Type   | Description                                                        |
|--------------------|--------|--------------------------------------------------------------------|
| `x`                | `int`  | Mouse X coordinate relative to the browser view.                  |
| `y`                | `int`  | Mouse Y coordinate relative to the browser view.                  |
| `selection_text`   | `str`  | Currently selected text (empty if none).                          |
| `link_url`         | `str`  | URL of the link under the cursor (empty if none).                 |
| `source_url`       | `str`  | URL of the element (image, video, etc.) under the cursor.         |
| `page_url`         | `str`  | URL of the top-level page.                                        |
| `is_editable`      | `bool` | `True` if the right-clicked element is an editable field.         |
| `has_image`        | `bool` | `True` if the element has image contents.                         |
| `media_type`       | `int`  | CEF media type (0=none, 1=image, 2=video, 3=audio).              |
| `type_flags`       | `int`  | Bitmask of context type flags.                                    |
| `edit_state_flags` | `int`  | Bitmask of edit capabilities (undo, redo, cut, copy, paste, etc.).|

!!! tip "Backward compatible"
    Handlers that accept **no parameters** continue to work — `ContextMenuParams`
    is only passed when the handler's signature requests it.

---

## Dynamic Menus (on_before_context_menu)

Use `on_before_context_menu()` to register a callback that fires **just
before** the context menu is shown. This lets you dynamically enable, disable,
check, or hide items based on the current right-click context.

```python
def before_menu(params: ContextMenuParams):
    has_selection = bool(params.selection_text)
    # Only enable Copy if text is selected
    p.set_context_menu_item_enabled(0, has_selection)

    # Only show "Open Link" if a link was right-clicked
    has_link = bool(params.link_url)
    p.set_context_menu_item_visible(3, has_link)

p.on_before_context_menu(before_menu)
```

The callback receives a `ContextMenuParams` and is called **before** the menu
is built, so any changes you make to item enabled/checked/visible state will
be reflected in the menu that appears.

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
    from Pytonium import Pytonium, ContextMenuParams

    class EditorMenu:
        def __init__(self, pytonium):
            self.p = pytonium
            self.bold = False

        def cut(self, params: ContextMenuParams):
            if params.selection_text:
                print(f"Cutting: {params.selection_text}")

        def copy(self, params: ContextMenuParams):
            if params.selection_text:
                print(f"Copying: {params.selection_text}")

        def paste(self):
            print("Pasting from clipboard")

        def select_all(self):
            self.p.execute_javascript("document.execCommand('selectAll')")

        def toggle_bold(self):
            self.bold = not self.bold
            print(f"Bold: {'on' if self.bold else 'off'}")

        def align_left(self):
            print("Align left")

        def align_center(self):
            print("Align center")

        def align_right(self):
            print("Align right")

    p = Pytonium()
    menu = EditorMenu(p)

    # --- Standard items ---
    p.add_context_menu_entry(menu.cut, "Cut")
    p.add_context_menu_entry(menu.copy, "Copy")
    p.add_context_menu_entry(menu.paste, "Paste")

    # --- Separator ---
    p.add_context_menu_separator()

    p.add_context_menu_entry(menu.select_all, "Select All")

    # --- Separator ---
    p.add_context_menu_separator()

    # --- Check item ---
    p.add_context_menu_check_item(menu.toggle_bold, "Bold")

    # --- Submenu with radio items ---
    p.add_context_menu_submenu("Alignment", sub_namespace="align")
    p.add_context_menu_radio_item(
        menu.align_left, "Left", group_id=1,
        context_menu_namespace="align")
    p.add_context_menu_radio_item(
        menu.align_center, "Center", group_id=1,
        context_menu_namespace="align")
    p.add_context_menu_radio_item(
        menu.align_right, "Right", group_id=1,
        context_menu_namespace="align")

    # --- Accelerators ---
    p.set_context_menu_item_accelerator(0, ord('X'), ctrl=True)   # Cut
    p.set_context_menu_item_accelerator(1, ord('C'), ctrl=True)   # Copy
    p.set_context_menu_item_accelerator(2, ord('V'), ctrl=True)   # Paste
    p.set_context_menu_item_accelerator(4, ord('A'), ctrl=True)   # Select All

    # --- Dynamic menu behavior ---
    def before_menu(params: ContextMenuParams):
        has_selection = bool(params.selection_text)
        # Only enable Cut/Copy when text is selected
        p.set_context_menu_item_enabled(0, has_selection)  # Cut
        p.set_context_menu_item_enabled(1, has_selection)  # Copy

    p.on_before_context_menu(before_menu)

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
        <style>
            body { font-family: sans-serif; padding: 2rem; }
            .editable {
                border: 1px solid #ccc;
                padding: 1rem;
                min-height: 200px;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <h1>Context Menu Demo</h1>
        <p>Right-click anywhere for the context menu.</p>
        <div class="editable" contenteditable="true">
            Select some text here and right-click to see Cut and Copy
            become enabled. Try the Bold check item and the Alignment
            submenu with radio items.
        </div>
    </body>
    </html>
    ```
