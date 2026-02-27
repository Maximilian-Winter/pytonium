# TypeScript Definitions

Pytonium can generate a TypeScript definition file (`.d.ts`) that describes all
your bound JavaScript functions, their parameters, and return types.  This gives
you autocompletion, type checking, and documentation in your IDE.

---

## Generating Definitions

Call `generate_typescript_definitions()` after registering all your bindings.

```python
from Pytonium import Pytonium, returns_value_to_javascript

@returns_value_to_javascript("number")
def add(a: int, b: int):
    return a + b

@returns_value_to_javascript("string")
def greet(name: str):
    return f"Hello, {name}"

def log_message(msg: str):
    print(msg)

p = Pytonium()
p.bind_function_to_javascript(add, javascript_object="math")
p.bind_function_to_javascript(greet, javascript_object="utils")
p.bind_function_to_javascript(log_message, javascript_object="utils")

# Generate after all bindings are registered
p.generate_typescript_definitions("./web/pytonium.d.ts")

p.add_custom_scheme("app", "./web/")
p.initialize("app://index.html", 800, 600)
```

!!! note "Timing"
    `generate_typescript_definitions()` can be called before or after
    `initialize()`, but it **must** be called after all bindings have been
    registered.  Only bindings that exist at the time of generation are
    included.

---

## Generated Output

For the bindings above, the generated `pytonium.d.ts` file looks like this:

```typescript
declare namespace Pytonium {
  export namespace math {
    function add(a: number, b: number): number;
  }
  export namespace utils {
    function greet(name: string): string;
    function log_message(msg: string): void;
  }
  export namespace appState {
    function registerForStateUpdates(eventName: string, namespaces: string[], getUpdatesFromJavascript: boolean, getUpdatesFromPytonium: boolean): void;
    function setState(namespace: string, key: string, value: any): void;
    function getState(namespace: string, key: string): any;
    function removeState(namespace: string, key: string): void;
  }
}
interface Window {
  PytoniumReady: boolean;
}
interface WindowEventMap {
  PytoniumReady: Event;
}
```

The generated file includes:

- All bound functions organized by their `javascript_object` namespace
- Parameter names and types (mapped from Python type annotations)
- Return types from the `@returns_value_to_javascript` decorator
- The `appState` namespace with all state management functions
- The `PytoniumReady` flag and event declarations

---

## Type Mapping

Python type annotations are converted to TypeScript types:

| Python Type | TypeScript Type |
|-------------|-----------------|
| `int`       | `number`        |
| `float`     | `number`        |
| `str`       | `string`        |
| `bool`      | `boolean`       |
| `object`    | `object`        |
| `None`      | `void`          |
| *(other)*   | `any`           |

!!! tip "Add type annotations"
    The more complete your Python type annotations are, the more useful the
    generated TypeScript definitions become.  Functions without annotations
    will have their parameters typed as `any`.

---

## Using in Your IDE

### VS Code / WebStorm

Place the generated `.d.ts` file in your web project directory.  Most IDEs
pick up TypeScript definition files automatically.

```
my_project/
    web/
        index.html
        app.js
        pytonium.d.ts    <-- Place here
    main.py
```

With the definitions in place, your IDE provides:

- Autocompletion for `Pytonium.math.add()`, `Pytonium.utils.greet()`, etc.
- Parameter type hints as you type
- Error highlighting for incorrect argument types
- Documentation of the `appState` API

### jsconfig.json (Optional)

For JavaScript projects (not TypeScript), create a `jsconfig.json` to ensure
your IDE picks up the types:

```json
{
    "compilerOptions": {
        "checkJs": true
    },
    "include": ["**/*.js", "pytonium.d.ts"]
}
```

---

## Regenerating Definitions

Regenerate the file whenever you change your bindings.  A good practice is to
call `generate_typescript_definitions()` as part of your application startup
during development:

```python
import os

p = Pytonium()

# ... register all bindings ...

if os.environ.get("DEV_MODE"):
    p.generate_typescript_definitions("./web/pytonium.d.ts")

p.initialize("app://index.html", 800, 600)
```

!!! tip "Development workflow"
    Run your app once with `DEV_MODE=1` to regenerate the definitions, then
    your IDE immediately picks up the updated types.

---

## Complete Example

=== "Python (main.py)"

    ```python
    import time
    from Pytonium import Pytonium, returns_value_to_javascript

    @returns_value_to_javascript("object")
    def get_user_info():
        return {"name": "Alice", "role": "admin"}

    @returns_value_to_javascript("number")
    def calculate(a: float, b: float, operation: str):
        ops = {"add": a + b, "sub": a - b, "mul": a * b, "div": a / b if b else 0}
        return ops.get(operation, 0)

    def send_notification(title: str, body: str):
        print(f"Notification: {title} - {body}")

    p = Pytonium()
    p.bind_function_to_javascript(get_user_info, javascript_object="api")
    p.bind_function_to_javascript(calculate, javascript_object="api")
    p.bind_function_to_javascript(send_notification, javascript_object="api")

    p.generate_typescript_definitions("./web/pytonium.d.ts")

    p.add_custom_scheme("app", "./web/")
    p.initialize("app://index.html", 800, 600)

    while p.is_running():
        p.update_message_loop()
        time.sleep(0.016)

    p.shutdown()
    ```

=== "Generated (web/pytonium.d.ts)"

    ```typescript
    declare namespace Pytonium {
      export namespace api {
        function get_user_info(): object;
        function calculate(a: number, b: number, operation: string): number;
        function send_notification(title: string, body: string): void;
      }
      export namespace appState {
        function registerForStateUpdates(eventName: string, namespaces: string[], getUpdatesFromJavascript: boolean, getUpdatesFromPytonium: boolean): void;
        function setState(namespace: string, key: string, value: any): void;
        function getState(namespace: string, key: string): any;
        function removeState(namespace: string, key: string): void;
      }
    }
    interface Window {
      PytoniumReady: boolean;
    }
    interface WindowEventMap {
      PytoniumReady: Event;
    }
    ```

=== "JavaScript (web/app.js)"

    ```javascript
    // With pytonium.d.ts in place, your IDE provides autocompletion:

    async function init() {
        // IDE shows: get_user_info(): object
        const user = await Pytonium.api.get_user_info();
        console.log(user.name);

        // IDE shows: calculate(a: number, b: number, operation: string): number
        const result = await Pytonium.api.calculate(10, 5, "add");
        console.log(result); // 15

        // IDE shows: send_notification(title: string, body: string): void
        Pytonium.api.send_notification("Welcome", "App loaded successfully");
    }

    if (window.PytoniumReady) {
        init();
    } else {
        window.addEventListener("PytoniumReady", init);
    }
    ```
