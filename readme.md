# Pytonium

**Build Python desktop apps with HTML, CSS, and JavaScript.**

Pytonium embeds the [Chromium Embedded Framework](https://bitbucket.org/chromiumembedded/cef/) (CEF 145 / Chromium 145) in Python, giving you the full power of modern web technologies for your desktop application UI.

[![PyPI](https://img.shields.io/pypi/v/Pytonium)](https://pypi.org/project/Pytonium/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/Maximilian-Winter/pytonium/blob/master/LICENSE)

## Install

```bash
pip install Pytonium
```

## Quick Start

```python
import time
from Pytonium import Pytonium

p = Pytonium()
p.initialize("https://example.com", 800, 600)

while p.is_running():
    time.sleep(0.01)
    p.update_message_loop()
```

That's it -- a native desktop window running a full Chromium browser, in 7 lines of Python.

## Features

- **Chromium rendering** -- Full browser engine for HTML/CSS/JS, use React, Tailwind, or any web framework
- **Python-JS bridge** -- Call Python functions from JavaScript, return values via Promises
- **State management** -- Shared state between Python and JS with namespace subscriptions and DOM events
- **Custom URL schemes** -- Map `myapp://` to a local folder for loading HTML, assets, and 3D models
- **Frameless windows** -- Build custom window chrome with HTML/CSS, Electron-style
- **Window control** -- Position, size, minimize, maximize, fullscreen, drag, native handle access
- **Multi-instance** -- Run multiple browser windows in a single process
- **TypeScript definitions** -- Auto-generate `.d.ts` files for IDE auto-completion
- **Async support** -- `asyncio` integration with `run_pytonium_async`
- **Event callbacks** -- React to title changes, URL navigation, and fullscreen state
- **Cross-platform** -- Windows 11 and Linux

## Example: Python + JavaScript Interop

```python
from Pytonium import Pytonium, returns_value_to_javascript

p = Pytonium()

@returns_value_to_javascript("any")
def get_data():
    return {"answer": 42, "source": "Python"}

p.bind_function_to_javascript(get_data, javascript_object="api")
p.initialize("file:///path/to/index.html", 800, 600)

while p.is_running():
    p.update_message_loop()
```

```javascript
// In your HTML/JS -- wait for bindings, then call Python
if (window.PytoniumReady) {
    callPython();
} else {
    window.addEventListener('PytoniumReady', callPython);
}

async function callPython() {
    const result = await Pytonium.api.get_data();
    console.log(result.answer); // 42
}
```

## Examples

Complete examples are included in the [`pytonium_examples/`](https://github.com/Maximilian-Winter/pytonium/tree/master/pytonium_examples) directory in this repository:

| Example | Description |
|---------|-------------|
| [Simple App](https://github.com/Maximilian-Winter/pytonium/tree/master/pytonium_examples/pytonium_example_simple) | Bindings, state management, and context menus |
| [Frameless Window](https://github.com/Maximilian-Winter/pytonium/tree/master/pytonium_examples/pytonium_example_frameless) | Custom HTML/CSS titlebar with window controls |
| [Babylon.js 3D](https://github.com/Maximilian-Winter/pytonium/tree/master/pytonium_examples/pytonium_example_babylon_js) | 3D rendering with custom schemes and MIME types |
| [Line Graph](https://github.com/Maximilian-Winter/pytonium/tree/master/pytonium_examples/pytonium_example_line_graph) | Real-time data visualization with state updates |
| [Control Center](https://github.com/Maximilian-Winter/pytonium/tree/master/pytonium_examples/pytonium_example_control_center) | Dashboard with multiple data panels |
| [Data Studio](https://github.com/Maximilian-Winter/pytonium/tree/master/pytonium_examples/pytonium_example_data_studio) | Interactive data analysis tool |

## Documentation

Full documentation is available at **[maximilian-winter.github.io/pytonium](https://maximilian-winter.github.io/pytonium/)**, covering:

- [Getting Started](https://maximilian-winter.github.io/pytonium/getting-started/installation/) -- Installation, quick start, and first app tutorial
- [Guides](https://maximilian-winter.github.io/pytonium/guides/javascript-bindings/) -- JS bindings, state management, frameless windows, async, and more
- [API Reference](https://maximilian-winter.github.io/pytonium/api/pytonium/) -- Complete Pytonium class reference (~35 methods)
- [Examples](https://maximilian-winter.github.io/pytonium/examples/) -- Walkthroughs of each example app
- [Building from Source](https://maximilian-winter.github.io/pytonium/building/build-guide/) -- Windows and Linux build instructions

## Platform Support

| Platform | Status |
|----------|--------|
| Windows 11 | Fully supported |
| Linux (X11) | Fully supported |
| Python 3.10+ | Required (64-bit) |

## Building from Source

See the [Build Guide](https://maximilian-winter.github.io/pytonium/building/build-guide/) or [`how-to-build-from-source.md`](https://github.com/Maximilian-Winter/pytonium/blob/master/how-to-build-from-source.md) for detailed instructions.

```bash
# Quick version (Windows)
pip install build scikit-build cmake ninja Cython
cmake -B cmake-build-release -DCMAKE_BUILD_TYPE=Release
cmake --build cmake-build-release --target pytonium_subprocess --config Release
cd building_pythonium_core && python prepare_build.py --platform windows --build-dir ../cmake-build-release
cd ../src/pytonium_python_framework && python -m build --wheel
pip install dist/pytonium-*.whl --force-reinstall
```

## License

[MIT License](https://github.com/Maximilian-Winter/pytonium/blob/master/LICENSE) -- Pytonium also includes [CEF](https://bitbucket.org/chromiumembedded/cef/) (BSD) and [nlohmann/json](https://github.com/nlohmann/json) (MIT).
