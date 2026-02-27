# Pytonium Class Reference

The `Pytonium` class is the main entry point for building desktop applications with HTML/CSS/JS user interfaces backed by Python. Each instance manages a CEF (Chromium Embedded Framework) browser window and provides methods for JavaScript interop, window control, state management, and more.

```python
from Pytonium import Pytonium
```

---

## Initialization & Lifecycle

### `__init__`

<div class="api-method" markdown>

```python
Pytonium()
```

</div>

Create a new Pytonium instance. This does **not** initialize CEF or create a browser window -- call `initialize()` or `create_browser()` for that.

```python
p = Pytonium()
```

---

### `initialize`

<div class="api-method" markdown>

```python
initialize(start_url: str, init_width: int, init_height: int) -> None
```

</div>

Initialize the CEF framework and open the first browser window. If CEF is already initialized (by another instance), this creates a new browser window within the existing CEF process.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `start_url` | `str` | -- | The URL to load when the browser window opens. Can be an `http://`, `https://`, `file:///`, or custom scheme URL. |
| `init_width` | `int` | -- | Initial window width in pixels. |
| `init_height` | `int` | -- | Initial window height in pixels. |

**Returns:** `None`

!!! warning "Pre-initialize configuration"
    Methods such as `set_frameless_window()`, `set_osr_mode()`, `set_cache_path()`, `set_custom_icon_path()`, `add_custom_scheme()`, and `bind_function_to_javascript()` must be called **before** `initialize()`.

```python
p = Pytonium()
p.set_frameless_window(True)
p.initialize("https://example.com", 1024, 768)
```

---

### `is_running`

<div class="api-method" markdown>

```python
is_running() -> bool
```

</div>

Check whether this instance's browser window is currently open and running.

**Returns:** `bool` -- `True` if the browser window is open.

```python
while p.is_running():
    p.update_message_loop()
```

---

### `update_message_loop`

<div class="api-method" markdown>

```python
update_message_loop() -> None
```

</div>

Process pending CEF messages. This must be called regularly (typically in a loop or via `run_pytonium_async`) to keep the browser responsive. CEF's message loop is global -- calling this on any instance processes events for **all** browser windows.

**Returns:** `None`

```python
import time
while p.is_running():
    p.update_message_loop()
    time.sleep(0.016)  # ~60 fps
```

---

### `shutdown`

<div class="api-method" markdown>

```python
shutdown() -> None
```

</div>

Shut down the CEF framework entirely. This should be called when all browser windows have been closed and the application is exiting.

**Returns:** `None`

!!! danger "Call only once"
    CEF shutdown is a global operation. Once called, no new browser windows can be created.

---

### `close_browser`

<div class="api-method" markdown>

```python
close_browser() -> None
```

</div>

Close this instance's browser window without shutting down CEF. Other browser windows remain open.

**Returns:** `None`

---

### `close_window`

<div class="api-method" markdown>

```python
close_window() -> None
```

</div>

Close the native OS window associated with this instance.

**Returns:** `None`

---

### `create_browser`

<div class="api-method" markdown>

```python
create_browser(url: str, width: int, height: int, frameless: bool = False, icon_path: str = "") -> int
```

</div>

Create an additional browser window. CEF must already be initialized (by a prior call to `initialize()` on any instance).

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `url` | `str` | -- | The URL to load in the new window. |
| `width` | `int` | -- | Window width in pixels. |
| `height` | `int` | -- | Window height in pixels. |
| `frameless` | `bool` | `False` | Whether the window should have no title bar or borders. |
| `icon_path` | `str` | `""` | Path to a custom window icon file (`.ico` on Windows). |

**Returns:** `int` -- The browser ID for the new window.

```python
p2 = Pytonium()
browser_id = p2.create_browser("https://example.org", 600, 400, frameless=True)
```

---

### `get_browser_id`

<div class="api-method" markdown>

```python
get_browser_id() -> int
```

</div>

Get the CEF browser identifier for this instance.

**Returns:** `int` -- The browser ID, or `-1` if no browser is open.

---

### `is_cef_initialized`

<div class="api-method" markdown>

```python
@classmethod
is_cef_initialized() -> bool
```

</div>

Check whether the CEF framework has been initialized by any Pytonium instance.

**Returns:** `bool` -- `True` if CEF is initialized.

```python
if not Pytonium.is_cef_initialized():
    p.initialize("https://example.com", 800, 600)
```

---

## JavaScript Bindings

### `bind_function_to_javascript`

<div class="api-method" markdown>

```python
bind_function_to_javascript(
    function_to_bind: Callable[..., Any],
    name: str = "",
    javascript_object: str = ""
) -> None
```

</div>

Bind a Python function so it can be called from JavaScript. The function becomes available as `Pytonium.{javascript_object}.{name}()` in the browser.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `function_to_bind` | `Callable` | -- | A callable Python function. Use the `@returns_value_to_javascript` decorator if it should return a value to JS. |
| `name` | `str` | `""` | The name to expose in JavaScript. Defaults to the function's `__name__`. |
| `javascript_object` | `str` | `""` | JS namespace object to attach the function to. If empty, the function is placed directly under `Pytonium`. |

**Returns:** `None`

!!! warning "Must be called before `initialize()`"
    All bindings must be registered before the browser window is created.

```python
from Pytonium import returns_value_to_javascript

@returns_value_to_javascript("string")
def greet(name):
    return f"Hello, {name}!"

p = Pytonium()
p.bind_function_to_javascript(greet, name="greet", javascript_object="api")
p.initialize("index.html", 800, 600)
# In JS: let msg = await Pytonium.api.greet("World");
```

---

### `bind_functions_to_javascript`

<div class="api-method" markdown>

```python
bind_functions_to_javascript(
    functions_to_bind: list[Callable[..., Any]],
    names: list[str] | None = None,
    javascript_object: str = ""
) -> None
```

</div>

Bind multiple Python functions at once.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `functions_to_bind` | `list[Callable]` | -- | A list of callable Python functions. |
| `names` | `list[str] \| None` | `None` | Optional list of JS names. Defaults to each function's `__name__`. |
| `javascript_object` | `str` | `""` | JS namespace object to attach the functions to. |

**Returns:** `None`

```python
p.bind_functions_to_javascript(
    [get_data, save_data],
    names=["getData", "saveData"],
    javascript_object="backend"
)
```

---

### `bind_object_methods_to_javascript`

<div class="api-method" markdown>

```python
bind_object_methods_to_javascript(
    obj: object,
    names: list[str] | None = None,
    javascript_object: str = ""
) -> None
```

</div>

Bind all public methods (those not starting with `__`) of a Python object so they can be called from JavaScript.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `obj` | `object` | -- | A Python object whose public methods will be bound. Must not be `None`. |
| `names` | `list[str] \| None` | `None` | Optional list of JS names for the methods. |
| `javascript_object` | `str` | `""` | JS namespace object to attach the methods to. |

**Returns:** `None`

```python
class MyAPI:
    def get_version(self):
        return "1.0.0"

    def compute(self, x, y):
        return x + y

p.bind_object_methods_to_javascript(MyAPI(), javascript_object="myApi")
```

---

### `return_value_to_javascript`

<div class="api-method" markdown>

```python
return_value_to_javascript(message_id: int, value: Any) -> None
```

</div>

Low-level method to send a return value back to a JavaScript Promise. Normally handled automatically by the `@returns_value_to_javascript` decorator; use this only for advanced use cases where you need manual control over when the value is returned.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `message_id` | `int` | -- | The message ID associated with the JavaScript call. |
| `value` | `Any` | -- | The Python value to return. Supported types: `int`, `float`, `str`, `bool`, `dict`, `list`. |

**Returns:** `None`

---

### `execute_javascript`

<div class="api-method" markdown>

```python
execute_javascript(code: str) -> None
```

</div>

Execute arbitrary JavaScript code in the browser context.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `code` | `str` | -- | The JavaScript code string to execute. |

**Returns:** `None`

```python
p.execute_javascript("document.title = 'Updated Title';")
```

---

### `generate_typescript_definitions`

<div class="api-method" markdown>

```python
generate_typescript_definitions(filename: str) -> None
```

</div>

Generate a TypeScript definition file (`.d.ts`) for all currently bound JavaScript functions. This enables IDE autocompletion and type checking for the JS side of the application.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `filename` | `str` | -- | Path to the `.d.ts` file to write. |

**Returns:** `None`

```python
p.bind_function_to_javascript(greet, javascript_object="api")
p.generate_typescript_definitions("pytonium.d.ts")
```

---

## State Management

### `set_state`

<div class="api-method" markdown>

```python
set_state(namespace: str, key: str, value: Any) -> None
```

</div>

Set a value in the application state. This notifies all subscribed Python state handlers and, if JavaScript subscribers are registered, triggers DOM events in the browser.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `namespace` | `str` | -- | The state namespace (e.g., `"ui"`, `"data"`). |
| `key` | `str` | -- | The state key within the namespace. |
| `value` | `Any` | -- | The value to store. Supported types: `int`, `float`, `str`, `bool`, `dict`, `list`. |

**Returns:** `None`

```python
p.set_state("app", "theme", "dark")
p.set_state("data", "items", [1, 2, 3])
```

---

### `add_state_handler`

<div class="api-method" markdown>

```python
add_state_handler(state_handler: object, namespaces: list[str]) -> None
```

</div>

Register a Python object as a state handler. The object must have an `update_state(namespace, key, value)` method. It will be called whenever `set_state` is invoked (from Python or JavaScript) for any of the subscribed namespaces.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `state_handler` | `object` | -- | An object with an `update_state(namespace: str, key: str, value: Any)` method. |
| `namespaces` | `list[str]` | -- | List of state namespace strings to subscribe to. |

**Returns:** `None`

!!! note
    If the handler object does not have an `update_state` method, a `UserWarning` is issued and the handler is ignored.

```python
class ThemeHandler:
    def update_state(self, namespace, key, value):
        if key == "theme":
            print(f"Theme changed to {value}")

p.add_state_handler(ThemeHandler(), ["app"])
```

---

## Context Menus

### `add_context_menu_entry`

<div class="api-method" markdown>

```python
add_context_menu_entry(
    context_menu_entry_function: Callable[..., Any],
    display_name: str = "",
    context_menu_namespace: str = ""
) -> None
```

</div>

Add a custom entry to the browser's right-click context menu.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `context_menu_entry_function` | `Callable` | -- | A callable invoked when the menu entry is clicked. |
| `display_name` | `str` | `""` | The label shown in the menu. Defaults to the function's `__name__`. |
| `context_menu_namespace` | `str` | `""` | Namespace for grouping menu entries. Defaults to `"app"`. |

**Returns:** `None`

```python
def reload_data():
    print("Reloading...")

p.add_context_menu_entry(reload_data, display_name="Reload Data")
```

---

### `add_context_menu_entries`

<div class="api-method" markdown>

```python
add_context_menu_entries(
    context_menu_entry_functions: list[Callable[..., Any]],
    display_names: list[str] | None = None,
    context_menu_namespace: str = ""
) -> None
```

</div>

Add multiple custom entries to the browser context menu at once.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `context_menu_entry_functions` | `list[Callable]` | -- | A list of callables for each menu entry. |
| `display_names` | `list[str] \| None` | `None` | Optional list of display labels. Defaults to each function's `__name__`. |
| `context_menu_namespace` | `str` | `""` | Namespace for grouping. Defaults to `"app"`. |

**Returns:** `None`

---

### `add_context_menu_entries_from_object`

<div class="api-method" markdown>

```python
add_context_menu_entries_from_object(
    context_menu_entries_object: object,
    display_names: list[str] | None = None,
    context_menu_namespace: str = ""
) -> None
```

</div>

Add context menu entries from all public methods of a Python object.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `context_menu_entries_object` | `object` | -- | A Python object whose public methods become menu entries. |
| `display_names` | `list[str] \| None` | `None` | Optional list of display labels. |
| `context_menu_namespace` | `str` | `""` | Namespace for grouping. Defaults to `"app"`. |

**Returns:** `None`

---

### `set_context_menu_namespace`

<div class="api-method" markdown>

```python
set_context_menu_namespace(context_menu_namespace: str) -> None
```

</div>

Set the active context menu namespace. Only entries belonging to this namespace will appear in the right-click menu.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `context_menu_namespace` | `str` | -- | The namespace whose entries will appear in the context menu. |

**Returns:** `None`

---

### `set_show_debug_context_menu`

<div class="api-method" markdown>

```python
set_show_debug_context_menu(show: bool) -> None
```

</div>

Enable or disable the CEF debug context menu entries (e.g., DevTools, View Source).

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `show` | `bool` | -- | `True` to show debug entries, `False` to hide them. |

**Returns:** `None`

---

## Window Control

### `set_frameless_window`

<div class="api-method" markdown>

```python
set_frameless_window(frameless: bool) -> None
```

</div>

Enable or disable frameless window mode. When frameless, the window has no title bar or borders.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `frameless` | `bool` | -- | `True` for frameless, `False` for standard window chrome. |

**Returns:** `None`

!!! warning "Must be called before `initialize()`"

---

### `set_osr_mode`

<div class="api-method" markdown>

```python
set_osr_mode(osr: bool) -> None
```

</div>

Enable or disable off-screen rendering (OSR) mode. OSR is required for transparent window backgrounds, where the browser renders to a buffer that is composited onto a layered Win32 window with per-pixel alpha.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `osr` | `bool` | -- | `True` to enable off-screen rendering. |

**Returns:** `None`

!!! warning "Must be called before `initialize()`"

---

### `set_parent_window`

<div class="api-method" markdown>

```python
set_parent_window(parent_hwnd: int) -> None
```

</div>

Set the parent window handle. When set, the browser window is created as a child (`WS_CHILD`) of the given parent instead of a standalone window. Used for embedding (e.g., wallpaper mode).

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `parent_hwnd` | `int` | -- | The parent window handle (HWND on Windows). Pass `0` to clear. |

**Returns:** `None`

!!! warning "Must be called before `initialize()`"

---

### `minimize_window`

<div class="api-method" markdown>

```python
minimize_window() -> None
```

</div>

Minimize the window to the taskbar.

**Returns:** `None`

---

### `maximize_window`

<div class="api-method" markdown>

```python
maximize_window() -> None
```

</div>

Maximize the window to fill the screen.

**Returns:** `None`

---

### `restore_window`

<div class="api-method" markdown>

```python
restore_window() -> None
```

</div>

Restore the window from a maximized or minimized state.

**Returns:** `None`

---

### `is_maximized`

<div class="api-method" markdown>

```python
is_maximized() -> bool
```

</div>

Check if the window is currently maximized.

**Returns:** `bool` -- `True` if maximized.

---

### `set_fullscreen`

<div class="api-method" markdown>

```python
set_fullscreen(fullscreen: bool) -> None
```

</div>

Enter or exit fullscreen mode. When entering fullscreen, the window fills the entire monitor it is currently on with all window chrome removed. When exiting, the previous window position, size, and style are restored.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `fullscreen` | `bool` | -- | `True` to enter fullscreen, `False` to exit. |

**Returns:** `None`

---

### `is_fullscreen`

<div class="api-method" markdown>

```python
is_fullscreen() -> bool
```

</div>

Check if the window is currently in fullscreen mode.

**Returns:** `bool` -- `True` if fullscreen.

---

### `toggle_fullscreen`

<div class="api-method" markdown>

```python
toggle_fullscreen() -> None
```

</div>

Toggle between fullscreen and windowed mode.

**Returns:** `None`

```python
# Wire up CEF's fullscreen callback to the window control
p.on_fullscreen_change(lambda fs: p.set_fullscreen(fs))
```

---

### `drag_window`

<div class="api-method" markdown>

```python
drag_window(delta_x: int, delta_y: int) -> None
```

</div>

Move the window by the specified pixel delta. Useful for implementing custom title bar drag behavior in frameless windows.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `delta_x` | `int` | -- | Horizontal offset in pixels. |
| `delta_y` | `int` | -- | Vertical offset in pixels. |

**Returns:** `None`

---

### `get_window_position`

<div class="api-method" markdown>

```python
get_window_position() -> tuple[int, int]
```

</div>

Get the current window position.

**Returns:** `tuple[int, int]` -- `(x, y)` coordinates of the top-left corner.

---

### `set_window_position`

<div class="api-method" markdown>

```python
set_window_position(x: int, y: int) -> None
```

</div>

Set the window position.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `x` | `int` | -- | X coordinate in pixels. |
| `y` | `int` | -- | Y coordinate in pixels. |

**Returns:** `None`

---

### `get_window_size`

<div class="api-method" markdown>

```python
get_window_size() -> tuple[int, int]
```

</div>

Get the current window size.

**Returns:** `tuple[int, int]` -- `(width, height)` in pixels.

---

### `set_window_size`

<div class="api-method" markdown>

```python
set_window_size(width: int, height: int) -> None
```

</div>

Set the window size.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `width` | `int` | -- | Window width in pixels. |
| `height` | `int` | -- | Window height in pixels. |

**Returns:** `None`

---

### `resize_window`

<div class="api-method" markdown>

```python
resize_window(new_width: int, new_height: int, anchor: int = 0) -> None
```

</div>

Resize the window from a specific anchor point. The anchor determines which corner of the window stays fixed during the resize.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `new_width` | `int` | -- | New window width in pixels. |
| `new_height` | `int` | -- | New window height in pixels. |
| `anchor` | `int` | `0` | Which corner stays fixed: `0` = top-left, `1` = top-right, `2` = bottom-left, `3` = bottom-right. |

**Returns:** `None`

---

### `get_native_window_handle`

<div class="api-method" markdown>

```python
get_native_window_handle() -> int
```

</div>

Get the native OS window handle for this browser window.

**Returns:** `int` -- The window handle (`HWND` on Windows, X11 window ID on Linux). Returns `0` if the browser is not initialized.

```python
hwnd = p.get_native_window_handle()
```

---

## Custom Schemes & MIME

### `add_custom_scheme`

<div class="api-method" markdown>

```python
add_custom_scheme(scheme_identifier: str, scheme_content_root_folder: str) -> None
```

</div>

Register a custom URL scheme mapped to a local folder. For example, registering `"app"` with `/path/to/web` allows loading `app://index.html` which serves `/path/to/web/index.html`.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `scheme_identifier` | `str` | -- | The scheme name (e.g., `"app"` for `app://` URLs). |
| `scheme_content_root_folder` | `str` | -- | Absolute path to the folder serving as content root. |

**Returns:** `None`

!!! warning "Must be called before `initialize()`"
    Custom schemes are registered once during CEF initialization and cannot be added afterward.

```python
p = Pytonium()
p.add_custom_scheme("app", "/path/to/my/web/content")
p.initialize("app://index.html", 800, 600)
```

---

### `add_mime_type_mapping`

<div class="api-method" markdown>

```python
add_mime_type_mapping(file_extension: str, mime_type: str) -> None
```

</div>

Add a custom file extension to MIME type mapping for custom schemes. CEF needs correct MIME types to handle files properly.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `file_extension` | `str` | -- | The file extension including the dot (e.g., `".wasm"`). |
| `mime_type` | `str` | -- | The MIME type (e.g., `"application/wasm"`). |

**Returns:** `None`

```python
p.add_mime_type_mapping(".wasm", "application/wasm")
p.add_mime_type_mapping(".glb", "model/gltf-binary")
```

---

## Configuration

### `set_cache_path`

<div class="api-method" markdown>

```python
set_cache_path(path: str) -> None
```

</div>

Set the path for the browser cache directory. This enables persistent cookies, localStorage, and other cached data across sessions.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `path` | `str` | -- | Absolute path to the cache directory. |

**Returns:** `None`

!!! warning "Must be called before `initialize()`"

---

### `set_custom_icon_path`

<div class="api-method" markdown>

```python
set_custom_icon_path(path: str) -> None
```

</div>

Set a custom window icon.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `path` | `str` | -- | Absolute path to the icon file (`.ico` on Windows). |

**Returns:** `None`

!!! warning "Must be called before `initialize()`"

---

### `load_url`

<div class="api-method" markdown>

```python
load_url(url: str) -> None
```

</div>

Navigate the browser to a new URL after initialization.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `url` | `str` | -- | The URL to load. |

**Returns:** `None`

```python
p.load_url("https://example.com/new-page")
```

---

### `pytonium_subprocess_path`

<div class="api-method" markdown>

```python
@classmethod
pytonium_subprocess_path() -> str
```

</div>

Get the path to the Pytonium subprocess executable. This is set automatically on import.

**Returns:** `str` -- The absolute path to the subprocess executable.

---

### `set_subprocess_path`

<div class="api-method" markdown>

```python
@classmethod
set_subprocess_path(value: str) -> None
```

</div>

Override the path to the Pytonium subprocess executable. This is set automatically on import and typically does not need to be changed.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `value` | `str` | -- | Absolute path to the subprocess executable. |

**Returns:** `None`

---

## Event Callbacks

### `on_title_change`

<div class="api-method" markdown>

```python
on_title_change(callback: Callable[[str], None]) -> None
```

</div>

Register a callback that is invoked when the browser page title changes.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `callback` | `Callable[[str], None]` | -- | A callable that receives the new title string. |

**Returns:** `None`

```python
p.on_title_change(lambda title: print(f"Title: {title}"))
```

---

### `on_address_change`

<div class="api-method" markdown>

```python
on_address_change(callback: Callable[[str], None]) -> None
```

</div>

Register a callback that is invoked when the browser URL changes (navigation events).

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `callback` | `Callable[[str], None]` | -- | A callable that receives the new URL string. |

**Returns:** `None`

```python
p.on_address_change(lambda url: print(f"Navigated to: {url}"))
```

---

### `on_fullscreen_change`

<div class="api-method" markdown>

```python
on_fullscreen_change(callback: Callable[[bool], None]) -> None
```

</div>

Register a callback that is invoked when the browser requests a fullscreen state change (e.g., from a `<video>` element or the Fullscreen API in JavaScript).

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `callback` | `Callable[[bool], None]` | -- | A callable that receives `True` when entering fullscreen, `False` when exiting. |

**Returns:** `None`

!!! tip "Wiring fullscreen"
    The CEF fullscreen callback and the window fullscreen control are decoupled. To make browser-initiated fullscreen requests actually change the window, wire them together:

    ```python
    p.on_fullscreen_change(lambda fs: p.set_fullscreen(fs))
    ```
