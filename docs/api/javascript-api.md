# JavaScript API Reference

Pytonium injects a JavaScript API into every browser window, providing access to bound Python functions, application state management, and readiness detection. This page documents the JavaScript-side interfaces available in the browser context.

---

## The `Pytonium` Namespace

All Python functions bound via `bind_function_to_javascript()` are accessible under the global `Pytonium` namespace. Functions are organized by the `javascript_object` parameter used during binding.

```
Pytonium.{objectName}.{functionName}(args...)
```

For example, if you bind a Python function with `javascript_object="api"` and `name="getData"`:

```python
# Python
p.bind_function_to_javascript(get_data, name="getData", javascript_object="api")
```

It becomes available in JavaScript as:

```javascript
// JavaScript
Pytonium.api.getData();
```

!!! note "Functions without a namespace"
    If `javascript_object` is left empty (`""`), the function is placed directly under the `Pytonium` namespace:

    ```javascript
    Pytonium.myFunction();
    ```

---

## `Pytonium.appState`

The `appState` namespace provides built-in methods for managing shared application state between Python and JavaScript.

### `registerForStateUpdates`

```javascript
Pytonium.appState.registerForStateUpdates(
    eventName,          // string
    namespaces,         // string[]
    getUpdatesFromJavascript, // boolean
    getUpdatesFromPytonium    // boolean
)
```

Subscribe to state changes. When a subscribed state value changes, a custom DOM event is dispatched on `window`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `eventName` | `string` | The name of the custom DOM event to dispatch when state changes. |
| `namespaces` | `string[]` | Array of state namespace strings to subscribe to. |
| `getUpdatesFromJavascript` | `boolean` | If `true`, receive events for state changes made from JavaScript (`setState`). |
| `getUpdatesFromPytonium` | `boolean` | If `true`, receive events for state changes made from Python (`set_state`). |

```javascript
// Subscribe to all changes in the "ui" and "data" namespaces
Pytonium.appState.registerForStateUpdates(
    "stateChanged",
    ["ui", "data"],
    true,   // changes from JS
    true    // changes from Python
);

window.addEventListener("stateChanged", (event) => {
    console.log("State updated:", event.detail);
});
```

---

### `setState`

```javascript
Pytonium.appState.setState(namespace, key, value)
```

Set a state value. This is synchronized to the Python side and triggers any registered state handlers and DOM event subscribers.

| Parameter | Type | Description |
|-----------|------|-------------|
| `namespace` | `string` | The state namespace. |
| `key` | `string` | The key within the namespace. |
| `value` | `any` | The value to store. Supported types: numbers, strings, booleans, objects, arrays. |

```javascript
Pytonium.appState.setState("ui", "theme", "dark");
Pytonium.appState.setState("data", "items", [1, 2, 3]);
```

---

### `getState`

```javascript
Pytonium.appState.getState(namespace, key)
```

Get the current value of a state entry.

| Parameter | Type | Description |
|-----------|------|-------------|
| `namespace` | `string` | The state namespace. |
| `key` | `string` | The key within the namespace. |

**Returns:** The stored value, or `undefined` if not set.

```javascript
let theme = Pytonium.appState.getState("ui", "theme");
console.log(theme); // "dark"
```

---

### `removeState`

```javascript
Pytonium.appState.removeState(namespace, key)
```

Remove a state entry.

| Parameter | Type | Description |
|-----------|------|-------------|
| `namespace` | `string` | The state namespace. |
| `key` | `string` | The key to remove. |

```javascript
Pytonium.appState.removeState("ui", "theme");
```

---

## State Event Detail

When a state update fires a DOM event (registered via `registerForStateUpdates`), the `event.detail` object contains:

```javascript
{
    namespace: "string",  // The state namespace
    key: "string",        // The key that changed
    value: any            // The new value
}
```

### Full Example

```javascript
// Register for state updates
Pytonium.appState.registerForStateUpdates(
    "onAppState",
    ["app"],
    true,
    true
);

// Listen for changes
window.addEventListener("onAppState", (event) => {
    const { namespace, key, value } = event.detail;
    if (key === "theme") {
        document.body.classList.toggle("dark", value === "dark");
    }
});

// Trigger a change (from JS side)
Pytonium.appState.setState("app", "theme", "dark");
```

When the Python side calls `p.set_state("app", "counter", 10)`, the same event fires in the browser, allowing the UI to react to backend-driven state changes.

---

## `PytoniumReady` Event

Pytonium bindings are injected into the browser during page load. Because the injection may happen asynchronously, you should check for readiness before calling any `Pytonium.*` functions.

### `window.PytoniumReady`

A boolean property set to `true` on the `window` object once all bindings are available.

### `PytoniumReady` Event

A custom DOM event dispatched on `window` when bindings become available.

### Recommended Pattern

```javascript
function init() {
    // Safe to use Pytonium.* here
    Pytonium.appState.registerForStateUpdates("stateChanged", ["app"], true, true);
    console.log("Pytonium bindings are ready");
}

if (window.PytoniumReady) {
    init();
} else {
    window.addEventListener("PytoniumReady", init);
}
```

!!! tip "Always use the readiness check"
    Calling `Pytonium.*` before the bindings are injected will result in `ReferenceError: Pytonium is not defined`. The pattern above ensures your code runs only after the API is available.

---

## Return Values (Promises)

Python functions decorated with `@returns_value_to_javascript` return Promises in JavaScript. Use `await` or `.then()` to retrieve the value.

### Using `async`/`await`

```javascript
async function loadData() {
    let count = await Pytonium.api.getCount();
    let items = await Pytonium.api.getItems();
    console.log(`Got ${count} items:`, items);
}
```

### Using `.then()`

```javascript
Pytonium.api.getCount().then((count) => {
    console.log("Count:", count);
});
```

### Type Conversion

Values returned from Python are automatically converted to their JavaScript equivalents:

| Python Return Type | JavaScript Result |
|--------------------|-------------------|
| `int` | `number` |
| `float` | `number` |
| `str` | `string` |
| `bool` | `boolean` |
| `dict` | `object` |
| `list` | `Array` |
| `None` | `undefined` |

### Functions Without the Decorator

If a bound Python function does **not** use `@returns_value_to_javascript`, calling it from JavaScript returns `void` (i.e., `undefined`). The function still executes on the Python side.

```javascript
// Python function without decorator: def log_message(msg): print(msg)
Pytonium.api.log_message("hello"); // returns undefined, but Python prints "hello"
```

---

## Generated TypeScript Definitions

Pytonium can generate a `.d.ts` TypeScript definition file that describes all bound functions, the `appState` namespace, and the `PytoniumReady` event. This provides IDE autocompletion, inline documentation, and type checking.

### Generating Definitions

```python
# After binding all functions, before or after initialize()
p.generate_typescript_definitions("pytonium.d.ts")
```

### Structure of the Generated File

The generated `.d.ts` file follows this structure:

```typescript
declare namespace Pytonium {
  export namespace api {
    function getCount(): number;
    function getGreeting(name: string): string;
    function logMessage(msg: string): void;
  }

  export namespace appState {
    function registerForStateUpdates(
      eventName: string,
      namespaces: string[],
      getUpdatesFromJavascript: boolean,
      getUpdatesFromPytonium: boolean
    ): void;
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

### Using in Your Project

Place the generated `.d.ts` file in your web project's source directory or reference it in your `tsconfig.json`:

```json
{
  "compilerOptions": {
    "typeRoots": ["./"]
  },
  "include": ["pytonium.d.ts", "src/**/*.ts"]
}
```

!!! info "Parameter type inference"
    TypeScript parameter types in the generated file are inferred from Python type annotations on the bound functions. If a parameter has no annotation, it defaults to `any`. For best results, add type hints to your Python functions:

    ```python
    @returns_value_to_javascript("string")
    def greet(name: str) -> str:
        return f"Hello, {name}!"
    ```

### The `appState` Namespace

The `appState` definitions are always included in the generated file, regardless of whether you use state management. This ensures IDE support for the built-in state API.

### `Window` and `WindowEventMap` Extensions

The generated file also extends the global `Window` and `WindowEventMap` interfaces to include:

- `window.PytoniumReady: boolean` -- for the readiness check
- `WindowEventMap.PytoniumReady: Event` -- for typed event listeners

This allows TypeScript to recognize the `PytoniumReady` property and event without type errors:

```typescript
// TypeScript knows about PytoniumReady
if (window.PytoniumReady) {
    init();
} else {
    window.addEventListener("PytoniumReady", init);
}
```
