---
title: Examples Overview
---

# Examples Overview

These examples demonstrate Pytonium's capabilities, from basic windowing to full desktop applications. Each example is a standalone project you can clone and run.

!!! tip "Examples Repository"
    All example source code is available at **[github.com/Maximilian-Winter/pytonium_examples](https://github.com/Maximilian-Winter/pytonium_examples)**. Clone the repository to run any example locally.

    ```bash
    git clone https://github.com/Maximilian-Winter/pytonium_examples.git
    cd pytonium_examples
    ```

---

## Example Gallery

| Example | Description | Key Features |
|---|---|---|
| **[Simple App](simple-app.md)** | Basic Python + HTML app with bindings, state, and context menus | Custom schemes, `@returns_value_to_javascript`, state management |
| **[Frameless Window](frameless-window.md)** | Custom window chrome with an HTML/CSS titlebar | `set_frameless_window`, drag/resize regions, window control bindings |
| **[3D with Babylon.js](babylon-js.md)** | 3D rendering using custom schemes and MIME types | MIME type mapping, custom data schemes, `.glb` model loading |
| **[Real-Time Line Graph](line-graph.md)** | Live data visualization with Python state updates | `set_state` in a loop, `registerForStateUpdates`, Canvas rendering |
| **[Control Center](control-center.md)** | Dashboard-style app with multiple panels | Multiple state namespaces, context menus, multi-panel layout |
| **[Data Studio](data-studio.md)** | Data analysis tool with interactive UI | File loading from Python, `@returns_value_to_javascript` for queries |

---

## Running an Example

Each example follows the same structure:

```
example-name/
    main.py         # Python entry point
    index.html      # Main HTML page
    style.css       # Styles (optional)
    app.js          # JavaScript logic (optional)
```

To run any example:

```bash
cd example-name
python main.py
```

!!! note "Prerequisites"
    Make sure Pytonium is installed before running examples:

    ```bash
    pip install Pytonium
    ```

---

## What to Learn from Each Example

**Starting out?** Begin with the [Simple App](simple-app.md). It covers all the fundamentals: custom schemes for local file loading, Python-to-JavaScript function bindings, and real-time state management.

**Want custom window chrome?** The [Frameless Window](frameless-window.md) example shows how to replace the native titlebar with an HTML/CSS design, including drag regions and window control buttons.

**Working with 3D or binary assets?** The [Babylon.js](babylon-js.md) example demonstrates MIME type mapping for non-standard file types and multiple custom schemes for different asset directories.

**Need real-time data?** The [Line Graph](line-graph.md) example shows the pattern for pushing data from Python and rendering live updates in JavaScript.

**Building something larger?** The [Control Center](control-center.md) and [Data Studio](data-studio.md) examples demonstrate multi-panel layouts, multiple state namespaces, and more advanced binding patterns.
