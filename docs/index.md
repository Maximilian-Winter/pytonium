---
title: Pytonium - Python Desktop Apps with Web UIs
hide:
  - navigation
  - toc
---

# Build Python Desktop Apps with HTML, CSS, and JavaScript

**Pytonium** embeds the Chromium Embedded Framework in Python, giving you the full power of modern web technologies for your desktop application UI.

---

## Get Started in Seconds

```bash
pip install Pytonium
```

```python
import time
from Pytonium import Pytonium

p = Pytonium()
p.initialize("https://example.com", 800, 600)

while p.is_running():
    time.sleep(0.01)
    p.update_message_loop()
```

That is a complete, runnable Pytonium application. It opens a native window displaying a web page, and runs until the user closes it.

[Get Started](getting-started/installation.md){ .md-button .md-button--primary }
[API Reference](api/pytonium.md){ .md-button }
[Examples](examples/index.md){ .md-button }

---

## Features

<div class="feature-grid" markdown>

<div class="feature" markdown>

### Chromium Rendering

Full Chromium browser engine powered by CEF 145 (Chromium 145). Render any HTML, CSS, and JavaScript your browser can -- inside a native desktop window.

</div>

<div class="feature" markdown>

### Python-JS Bridge

Call Python functions from JavaScript and return values via Promises. Bind individual functions or entire objects with a single method call.

</div>

<div class="feature" markdown>

### State Management

Shared state between Python and JavaScript with event subscriptions. Set state from Python, subscribe from JS, and react to changes on either side.

</div>

<div class="feature" markdown>

### Reactive Components

Build UIs entirely in Python with reactive state bindings. State changes trigger surgical DOM updates -- no virtual DOM, no JavaScript framework needed.

</div>

<div class="feature" markdown>

### Custom Schemes

Register custom URL protocols (e.g., `myapp://`) for loading local files. Serve your HTML, CSS, JS, and assets from your project directory without a web server.

</div>

<div class="feature" markdown>

### Context Menus

Add custom right-click menu entries with Python callbacks. Group entries into namespaces and switch between them at runtime.

</div>

<div class="feature" markdown>

### Frameless Windows

Build custom window chrome with HTML/CSS, Electron-style. Control minimize, maximize, close, drag, and resize entirely from your frontend.

</div>

<div class="feature" markdown>

### Multi-Instance

Run multiple browser windows in a single process. Each window gets its own bindings, state, and lifecycle while sharing a single CEF runtime.

</div>

<div class="feature" markdown>

### TypeScript Definitions

Auto-generate `.d.ts` files for IDE auto-completion. Your bound Python functions appear in VS Code with full type information.

</div>

<div class="feature" markdown>

### Async Support

asyncio integration with `run_pytonium_async`. Drop the manual while-loop and run Pytonium alongside other async tasks in your application.

</div>

<div class="feature" markdown>

### Cross-Platform

Windows 11 and Linux support, Python 3.10+. Build on one platform and deploy on both with the same Python code and web UI.

</div>

</div>

---

## Next Steps

- **[Installation](getting-started/installation.md)** -- Install Pytonium and verify your setup.
- **[Quick Start](getting-started/quickstart.md)** -- Learn the core concepts: message loops, custom schemes, and the PytoniumReady event.
- **[Your First App](getting-started/first-app.md)** -- Build a complete app with Python-JS communication and state management.
- **[API Reference](api/pytonium.md)** -- Full reference for the Pytonium class and all its methods.
- **[Examples](examples/index.md)** -- Browse example applications from simple to complex.

!!! note "Platform Support"
    Pytonium is tested on **Windows 11** and **Linux** with **Python 3.10+**. macOS support is not yet available.
