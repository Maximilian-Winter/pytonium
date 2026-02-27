# Decorators & Helper Functions

Pytonium provides decorators and async helper functions that simplify common patterns. These are imported directly from the `Pytonium` package alongside the main class.

```python
from Pytonium import Pytonium, returns_value_to_javascript, run_pytonium_async, run_pytonium_multi_async
```

---

## `@returns_value_to_javascript`

<div class="api-method" markdown>

```python
@returns_value_to_javascript(return_type: str = "any")
```

</div>

A decorator that marks a bound Python function as returning a value to JavaScript via a Promise. Without this decorator, JavaScript calls to bound Python functions return `void`.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `return_type` | `str` | `"any"` | The TypeScript type used when generating `.d.ts` definitions. Common values: `"number"`, `"string"`, `"boolean"`, `"object"`, `"any"`, `"void"`. |

### How It Works

When you decorate a function with `@returns_value_to_javascript`, Pytonium sets two attributes on the function object:

- `func.returns_value_to_javascript = True`
- `func.return_type = return_type`

When `bind_function_to_javascript` detects these attributes, it configures the binding so that the function's return value is automatically serialized and sent back to JavaScript as a resolved Promise.

### Supported Return Types

The following Python types are automatically converted for JavaScript:

| Python Type | JavaScript Type | TypeScript `return_type` |
|-------------|-----------------|--------------------------|
| `int` | `number` | `"number"` |
| `float` | `number` | `"number"` |
| `str` | `string` | `"string"` |
| `bool` | `boolean` | `"boolean"` |
| `dict` | `object` | `"object"` |
| `list` | `Array` | `"any"` |
| `None` | `undefined` | `"void"` |

### Example

```python
from Pytonium import Pytonium, returns_value_to_javascript

@returns_value_to_javascript("number")
def get_count():
    return 42

@returns_value_to_javascript("string")
def get_greeting(name):
    return f"Hello, {name}!"

@returns_value_to_javascript("object")
def get_config():
    return {"theme": "dark", "fontSize": 14}

p = Pytonium()
p.bind_function_to_javascript(get_count, javascript_object="api")
p.bind_function_to_javascript(get_greeting, javascript_object="api")
p.bind_function_to_javascript(get_config, javascript_object="api")
p.initialize("app://index.html", 800, 600)
```

On the JavaScript side:

```javascript
// All calls return Promises
let count = await Pytonium.api.get_count();        // 42
let msg = await Pytonium.api.get_greeting("World"); // "Hello, World!"
let cfg = await Pytonium.api.get_config();           // {theme: "dark", fontSize: 14}
```

!!! info "Without the decorator"
    If a function is bound **without** the decorator, calling it from JavaScript returns `void`. The function still executes on the Python side, but no value is sent back.

    ```python
    def log_message(msg):
        print(msg)

    p.bind_function_to_javascript(log_message, javascript_object="api")
    # JS: Pytonium.api.log_message("hello"); // returns void
    ```

---

## `run_pytonium_async`

<div class="api-method" markdown>

```python
async def run_pytonium_async(pytonium: Pytonium, interval: float = 0.016) -> None
```

</div>

An async coroutine that runs the Pytonium message loop, replacing the typical `while/sleep/update_message_loop` pattern. This integrates Pytonium into a standard `asyncio` event loop, allowing you to run other async tasks concurrently.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `pytonium` | `Pytonium` | -- | A Pytonium instance that has already been initialized. |
| `interval` | `float` | `0.016` | Seconds between message loop updates. The default of `0.016` corresponds to approximately 60 frames per second. |

**Returns:** `None` (runs until the browser window is closed)

### Example

```python
import asyncio
from Pytonium import Pytonium, run_pytonium_async

p = Pytonium()
p.initialize("https://example.com", 800, 600)
asyncio.run(run_pytonium_async(p))
```

### With Concurrent Tasks

Because this is an async coroutine, you can run other async work alongside the browser:

```python
import asyncio
from Pytonium import Pytonium, run_pytonium_async

async def background_task(p):
    while p.is_running():
        p.set_state("data", "timestamp", time.time())
        await asyncio.sleep(1.0)

async def main():
    p = Pytonium()
    p.initialize("https://example.com", 800, 600)
    await asyncio.gather(
        run_pytonium_async(p),
        background_task(p),
    )

asyncio.run(main())
```

!!! note "Equivalent manual loop"
    `run_pytonium_async` is equivalent to the following manual loop:

    ```python
    while pytonium.is_running():
        pytonium.update_message_loop()
        await asyncio.sleep(interval)
    ```

---

## `run_pytonium_multi_async`

<div class="api-method" markdown>

```python
async def run_pytonium_multi_async(instances: list[Pytonium], interval: float = 0.016) -> None
```

</div>

An async coroutine for running multiple Pytonium instances. CEF's message loop is global -- calling `update_message_loop()` on any instance processes events for **all** browser windows. This helper pumps the message loop while any instance is still running.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `instances` | `list[Pytonium]` | -- | A list of initialized Pytonium instances. |
| `interval` | `float` | `0.016` | Seconds between message loop updates (default ~60fps). |

**Returns:** `None` (runs until all browser windows are closed)

!!! info "Global message loop"
    CEF uses a single global message loop. You do **not** need to call `update_message_loop()` on each instance separately. Calling it on any one instance (the first in the list) is sufficient to process events for all windows.

### Example

```python
import asyncio
from Pytonium import Pytonium, run_pytonium_multi_async

p1 = Pytonium()
p1.initialize("https://example.com", 800, 600)

p2 = Pytonium()
p2.create_browser("https://example.org", 600, 400)

asyncio.run(run_pytonium_multi_async([p1, p2]))
```

### When Windows Are Closed Independently

The loop continues as long as **any** instance reports `is_running() == True`. When a user closes one window, the other windows remain functional. The loop exits only when the last browser window is closed.

```python
import asyncio
from Pytonium import Pytonium, run_pytonium_multi_async

async def main():
    windows = []
    for url in ["https://example.com", "https://example.org", "https://example.net"]:
        p = Pytonium()
        if not windows:
            p.initialize(url, 800, 600)
        else:
            p.create_browser(url, 800, 600)
        windows.append(p)

    await run_pytonium_multi_async(windows)
    # All windows closed, clean up
    windows[0].shutdown()

asyncio.run(main())
```

!!! tip "Shutdown"
    After the multi-async loop exits, call `shutdown()` on any one instance to cleanly shut down the CEF framework.
