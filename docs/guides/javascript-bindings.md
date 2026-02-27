# JavaScript Bindings

Pytonium lets you call Python functions directly from JavaScript running in the
browser.  Bindings are registered in Python, exposed on a global `Pytonium`
object in JavaScript, and can optionally return values back to JS via promises.

---

## Binding a Single Function

Use `bind_function_to_javascript()` to expose one Python function to JavaScript.

```python
from Pytonium import Pytonium

def greet(name: str):
    print(f"Hello, {name}!")

p = Pytonium()
p.bind_function_to_javascript(greet, name="greet", javascript_object="myApp")
p.initialize("app://index.html", 800, 600)
```

| Parameter            | Type       | Default          | Description                                                                 |
|----------------------|------------|------------------|-----------------------------------------------------------------------------|
| `function_to_bind`   | `Callable` | *(required)*     | The Python callable to expose.                                              |
| `name`               | `str`      | Function's `__name__` | The name to use in JavaScript.                                           |
| `javascript_object`  | `str`      | `""`             | Optional namespace object (e.g. `"myApp"` makes it `Pytonium.myApp.greet`). |

!!! warning "Register before initialize"
    All bindings **must** be registered before calling `initialize()`.  Bindings
    added after the browser window is created will not be available in
    JavaScript.

---

## Binding Multiple Functions

Use `bind_functions_to_javascript()` to register several functions at once.

```python
def start_task():
    print("Task started")

def stop_task():
    print("Task stopped")

p.bind_functions_to_javascript(
    [start_task, stop_task],
    names=["start", "stop"],
    javascript_object="tasks"
)
```

| Parameter            | Type             | Default            | Description                                       |
|----------------------|------------------|--------------------|---------------------------------------------------|
| `functions_to_bind`  | `list[Callable]` | *(required)*       | A list of Python callables.                       |
| `names`              | `list[str]`      | `None` (uses `__name__`) | Optional JS names for each function.        |
| `javascript_object`  | `str`            | `""`               | Optional namespace object.                        |

---

## Binding Object Methods

Use `bind_object_methods_to_javascript()` to expose all public methods of a
Python object.  Private methods (those starting with `__`) are skipped
automatically.

```python
class FileManager:
    def open_file(self, path: str):
        print(f"Opening {path}")

    def save_file(self, path: str, content: str):
        print(f"Saving to {path}")

fm = FileManager()
p.bind_object_methods_to_javascript(fm, javascript_object="files")
```

The methods are now available as `Pytonium.files.open_file(path)` and
`Pytonium.files.save_file(path, content)` in JavaScript.

---

## Returning Values to JavaScript

By default, bound functions return `void` to the JavaScript caller.  To send a
value back, decorate the function with `@returns_value_to_javascript(return_type)`.

```python
from Pytonium import Pytonium, returns_value_to_javascript

@returns_value_to_javascript("number")
def add(a: int, b: int):
    return a + b

@returns_value_to_javascript("string")
def get_greeting(name: str):
    return f"Hello, {name}!"

@returns_value_to_javascript("object")
def get_config():
    return {"theme": "dark", "fontSize": 14}

p = Pytonium()
p.bind_function_to_javascript(add, javascript_object="math")
p.bind_function_to_javascript(get_greeting, javascript_object="utils")
p.bind_function_to_javascript(get_config, javascript_object="utils")
```

The `return_type` string maps to TypeScript/JavaScript types:

| Python Return | `return_type` value |
|---------------|---------------------|
| `int`, `float`| `"number"`          |
| `str`         | `"string"`          |
| `bool`        | `"boolean"`         |
| `dict`        | `"object"`          |
| `list`        | `"object"`          |
| Mixed / any   | `"any"`             |

---

## Calling Bound Functions from JavaScript

Bound functions are available on the global `Pytonium` object.  If you specified
a `javascript_object`, the function is nested under that namespace.

=== "JavaScript (fire-and-forget)"

    ```javascript
    // No javascript_object specified
    Pytonium.greet("World");

    // With javascript_object="myApp"
    Pytonium.myApp.greet("World");
    ```

=== "JavaScript (with return value)"

    ```javascript
    // Functions decorated with @returns_value_to_javascript return a Promise
    const sum = await Pytonium.math.add(2, 3);
    console.log(sum); // 5

    const greeting = await Pytonium.utils.get_greeting("Alice");
    console.log(greeting); // "Hello, Alice!"

    const config = await Pytonium.utils.get_config();
    console.log(config.theme); // "dark"
    ```

!!! tip "Promises"
    Functions decorated with `@returns_value_to_javascript` automatically return
    a JavaScript `Promise`.  Use `await` or `.then()` to retrieve the value.

---

## Waiting for PytoniumReady

Pytonium bindings are injected into the JavaScript context during browser
initialization.  You **must** wait for them to be available before calling any
bound function.  Pytonium sets `window.PytoniumReady = true` and dispatches a
`PytoniumReady` event on `window` once the bindings are ready.

=== "JavaScript (check flag)"

    ```javascript
    if (window.PytoniumReady) {
        Pytonium.myApp.greet("World");
    }
    ```

=== "JavaScript (listen for event)"

    ```javascript
    window.addEventListener("PytoniumReady", () => {
        Pytonium.myApp.greet("World");
    });
    ```

=== "JavaScript (combined pattern)"

    ```javascript
    function onReady() {
        Pytonium.myApp.greet("World");
    }

    if (window.PytoniumReady) {
        onReady();
    } else {
        window.addEventListener("PytoniumReady", onReady);
    }
    ```

---

## Complete Example

Below is a full working example with a Python backend and an HTML/JavaScript
frontend.

=== "Python (main.py)"

    ```python
    import time
    from Pytonium import Pytonium, returns_value_to_javascript

    @returns_value_to_javascript("number")
    def multiply(a: int, b: int):
        return a * b

    def log_message(message: str):
        print(f"[JS] {message}")

    p = Pytonium()
    p.bind_function_to_javascript(multiply, javascript_object="math")
    p.bind_function_to_javascript(log_message, javascript_object="app")
    p.add_custom_scheme("myapp", "./web/")
    p.initialize("myapp://index.html", 800, 600)

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
        <title>Pytonium Bindings Demo</title>
    </head>
    <body>
        <h1>JavaScript Bindings</h1>
        <button id="calc">Calculate 6 x 7</button>
        <p id="result"></p>

        <script>
            function onReady() {
                Pytonium.app.log_message("Bindings are ready!");

                document.getElementById("calc").addEventListener("click", async () => {
                    const result = await Pytonium.math.multiply(6, 7);
                    document.getElementById("result").textContent = `Result: ${result}`;
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

## Supported Argument Types

The following Python types can be passed between JavaScript and Python:

| Python Type | JavaScript Type |
|-------------|-----------------|
| `int`       | `number`        |
| `float`     | `number`        |
| `str`       | `string`        |
| `bool`      | `boolean`       |
| `dict`      | `object`        |
| `list`      | `Array`         |

!!! note "Nested structures"
    Dictionaries and lists can be nested arbitrarily.  Pytonium handles
    recursive conversion between Python and JavaScript types automatically.
