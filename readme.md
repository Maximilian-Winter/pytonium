# Pytonium

**Turn your Python code into a desktop app with a Chromium UI.**

[![PyPI](https://img.shields.io/pypi/v/Pytonium)](https://pypi.org/project/Pytonium/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Bring your Python libraries, data, and application logic. Build the interface with HTML, CSS, and JavaScript. Pytonium connects them in a desktop window powered by the Chromium Embedded Framework (CEF).

Create a dashboard for a Python workflow, an interactive data tool, or a 3D viewer. Start with a single HTML file, bring a frontend built with React, Svelte, or Vue, or author reactive UI components in Python.

**[Get started](https://maximilian-winter.github.io/pytonium/getting-started/installation/)** · **[Documentation](https://maximilian-winter.github.io/pytonium/)** · **[Explore examples](https://maximilian-winter.github.io/pytonium/examples/)**

## Why build with Pytonium?

- **Put your Python code behind a real interface.** Call Python functions from JavaScript and receive results as Promises. Use your existing libraries for the work behind the UI.
- **Design with the browser tools you know.** Use modern CSS, Canvas, and WebGL, with Chromium rendering your interface inside a native desktop window.
- **Keep the interface connected to your data.** Share state between Python and JavaScript and subscribe to changes for live charts, progress displays, and interactive controls.
- **Make the window part of your design.** Create custom HTML/CSS title bars, frameless windows, context menus, and multi-window apps.
- **Load your UI locally.** Serve bundled frontend files through URLs such as `app://index.html`, without running a separate web server.

For frontend development, Pytonium can [generate TypeScript definitions](https://maximilian-winter.github.io/pytonium/guides/typescript-definitions/) for your Python bindings. Prefer writing the UI in Python? Explore [reactive components](https://maximilian-winter.github.io/pytonium/guides/reactive-components/).

## Try it

Install Pytonium:

```bash
pip install Pytonium
```

Save this as `main.py`:

```python
import time
from Pytonium import Pytonium

app = Pytonium()
app.initialize("https://example.com", 800, 600)

while app.is_running():
    time.sleep(0.01)
    app.update_message_loop()
```

Run `python main.py` to open a Chromium desktop window. Close the window to exit.

**Next: [build your first app](https://maximilian-winter.github.io/pytonium/getting-started/first-app/)** to load your own HTML, call Python from JavaScript, and send state updates to the page.

Requires **Python 3.10+** on **Windows 10/11 or Linux X11**, with **x86_64** architecture. macOS is not supported yet. The first import extracts the bundled Chromium runtime and takes a little longer. See the [installation guide](https://maximilian-winter.github.io/pytonium/getting-started/installation/) for setup and Linux dependencies.

## See what you can build

Explore the example apps for ideas and starting points:

| Example | What to explore |
| --- | --- |
| [Data Studio](pytonium_examples/pytonium_example_data_studio/) | A local data analysis UI with Python handling the data |
| [Control Center](pytonium_examples/pytonium_example_control_center/) | A dashboard with multiple panels driven by Python state |
| [Babylon.js 3D](pytonium_examples/pytonium_example_babylon_js/) | A WebGL scene with local 3D assets |
| [Frameless Window](pytonium_examples/pytonium_example_frameless/) | A custom HTML/CSS title bar and window controls |
| [Reactive App](pytonium_examples/pytonium_example_reactive/) | An interface authored with Python reactive components |

Find more examples and walkthroughs in the [examples guide](https://maximilian-winter.github.io/pytonium/examples/).

## Go further

- [Quick start](https://maximilian-winter.github.io/pytonium/getting-started/quickstart/) — application lifecycle, local content, and the JavaScript bridge.
- [Python–JavaScript bindings](https://maximilian-winter.github.io/pytonium/guides/javascript-bindings/) and [state management](https://maximilian-winter.github.io/pytonium/guides/state-management/) — connect your UI to your application.
- [API reference](https://maximilian-winter.github.io/pytonium/api/pytonium/) — methods, arguments, and behavior.
- [Build from source](https://maximilian-winter.github.io/pytonium/building/build-guide/) — work on Pytonium itself.

## Get involved

Bug reports, feature requests, documentation improvements, and example apps are welcome. [Open an issue](https://github.com/Maximilian-Winter/pytonium/issues) or read the [contributing guide](https://maximilian-winter.github.io/pytonium/about/contributing/) to get started.

## License

Pytonium is [MIT licensed](LICENSE). See [third-party licenses](https://maximilian-winter.github.io/pytonium/about/license/) for CEF and other included dependencies.
