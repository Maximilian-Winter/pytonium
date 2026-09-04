# Pytonium

**Build local Python desktop apps with a real Chromium UI.**

[![PyPI](https://img.shields.io/pypi/v/Pytonium)](https://pypi.org/project/Pytonium/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Pytonium embeds the [Chromium Embedded Framework](https://bitbucket.org/chromiumembedded/cef/) in Python, so you can build desktop software with the UI tools web developers already know: HTML, CSS, JavaScript, Canvas, WebGL, React, Svelte, Vue, Tailwind, Babylon.js, or just a single `index.html`.

It is for people who want Python to stay in charge of the application, while the frontend gets the full browser platform instead of a small native widget set.

## Why Pytonium?

- **Use the web as your UI layer.** Render modern HTML/CSS/JS in a native desktop window powered by CEF 145 / Chromium 145.
- **Keep your app logic in Python.** Bind Python functions and objects into JavaScript, including Promise-based return values.
- **Share state across the boundary.** Push namespaced state from Python to JavaScript, listen for DOM events, and react to frontend changes from Python.
- **Ship local assets cleanly.** Register custom URL schemes like `app://index.html` for HTML, CSS, JS, images, models, and data files.
- **Control the window.** Build frameless windows, custom title bars, fullscreen experiences, context menus, and multi-window apps.
- **Stay editor-friendly.** Generate TypeScript definitions for your Python bindings so frontend code gets autocomplete.

Pytonium works especially well for internal tools, dashboards, data apps, visual editors, local AI tools, 3D previews, and experiments where Python libraries and a rich browser UI belong in the same process.

## Install

```bash
pip install Pytonium
```

The first import extracts the bundled CEF runtime once. After that, startup is normal.

Supported platforms:

| Platform | Status |
| --- | --- |
| Windows 10/11, x86_64 | Supported |
| Linux X11, x86_64 | Supported |
| macOS | Not supported yet |
| Python | 3.10+ |

See the [installation guide](https://maximilian-winter.github.io/pytonium/getting-started/installation/) for virtual environment setup and Linux system packages.

## A Tiny App

```python
import time
from Pytonium import Pytonium

p = Pytonium()
p.initialize("https://example.com", 800, 600)

while p.is_running():
    time.sleep(0.01)
    p.update_message_loop()
```

That opens a native desktop window running Chromium. From there you can load local files, bind Python APIs, stream state to the page, or replace the native frame with your own HTML/CSS chrome.

## Python and JavaScript Together

```python
import os
from Pytonium import Pytonium, returns_value_to_javascript

p = Pytonium()

@returns_value_to_javascript("object")
def get_project_status():
    return {
        "name": "Pytonium",
        "runtime": "Python",
        "ui": "Chromium",
    }

p.bind_function_to_javascript(get_project_status, javascript_object="api")

content_root = os.path.dirname(os.path.abspath(__file__)) + "/"
p.add_custom_scheme("app", content_root)
p.initialize("app://index.html", 900, 600)
```

```javascript
async function init() {
  const status = await Pytonium.api.get_project_status();
  document.querySelector("#status").textContent =
    `${status.name}: ${status.runtime} + ${status.ui}`;
}

if (window.PytoniumReady) {
  init();
} else {
  window.addEventListener("PytoniumReady", init);
}
```

For a complete walkthrough with local files, state updates, callbacks, and TypeScript generation, start with [Your First App](https://maximilian-winter.github.io/pytonium/getting-started/first-app/).

## Examples

The [`pytonium_examples/`](pytonium_examples/) directory contains runnable apps that show different parts of the framework:

| Example | What it demonstrates |
| --- | --- |
| [Simple App](pytonium_examples/pytonium_example_simple/) | Bindings, shared state, context menus, and local files |
| [Frameless Window](pytonium_examples/pytonium_example_frameless/) | Custom HTML/CSS titlebar and window controls |
| [Babylon.js 3D](pytonium_examples/pytonium_example_babylon_js/) | WebGL, custom schemes, MIME types, and `.glb` assets |
| [Line Graph](pytonium_examples/pytonium_example_line_graph/) | Live Python state updates rendered in Canvas |
| [Control Center](pytonium_examples/pytonium_example_control_center/) | Dashboard-style UI with multiple state namespaces |
| [Data Studio](pytonium_examples/pytonium_example_data_studio/) | Interactive local data analysis |
| [Reactive App](pytonium_examples/pytonium_example_reactive/) | Python-authored reactive components |

Browse the [examples guide](https://maximilian-winter.github.io/pytonium/examples/) for explanations and run instructions.

## Documentation

The README is intentionally short. The real documentation lives here:

- [Getting Started](https://maximilian-winter.github.io/pytonium/getting-started/installation/)
- [Quick Start](https://maximilian-winter.github.io/pytonium/getting-started/quickstart/)
- [Guides](https://maximilian-winter.github.io/pytonium/guides/javascript-bindings/)
- [API Reference](https://maximilian-winter.github.io/pytonium/api/pytonium/)
- [Examples](https://maximilian-winter.github.io/pytonium/examples/)
- [Building from Source](https://maximilian-winter.github.io/pytonium/building/build-guide/)

## Build From Source

Most users should install from PyPI. If you want to work on Pytonium itself, see the [build guide](https://maximilian-winter.github.io/pytonium/building/build-guide/) or the repository-local [how-to-build-from-source.md](how-to-build-from-source.md).

For docs development:

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

## License

Pytonium is released under the [MIT License](LICENSE). It also includes CEF, which is distributed under the BSD license, and [nlohmann/json](https://github.com/nlohmann/json), which is distributed under the MIT license.
