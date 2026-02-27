---
title: Control Center
---

# Control Center

This example demonstrates a dashboard-style application with multiple panels, each displaying different data from Python. It showcases state management with multiple namespaces, context menus for panel-specific actions, and a multi-panel layout.

!!! tip "Full Source"
    This page provides a conceptual walkthrough with key code snippets. The complete source code is available in the [pytonium_examples repository](https://github.com/Maximilian-Winter/pytonium_examples).

---

## Architecture

The Control Center is structured as a single-page application with multiple data panels, each driven by its own state namespace in Python:

```
Python (main.py)
    |
    |-- State namespace: "system"    --> System info panel
    |-- State namespace: "network"   --> Network status panel
    |-- State namespace: "tasks"     --> Task list panel
    |-- State namespace: "log"       --> Activity log panel
    |
    |-- Context menu: "panel"        --> Right-click actions per panel
    |-- Bindings: "dashboard"        --> Dashboard control functions
```

---

## Python: Multiple Data Sources

```python title="main.py (key sections)"
import os
import time
import json
import platform
from datetime import datetime
from Pytonium import Pytonium, returns_value_to_javascript

pytonium = Pytonium()

# -- Bindings --

@returns_value_to_javascript("any")
def get_system_info():
    """Return static system information."""
    return {
        "platform": platform.system(),
        "version": platform.version(),
        "python": platform.python_version(),
        "machine": platform.machine()
    }

@returns_value_to_javascript("any")
def get_tasks():
    """Return a list of tasks."""
    return [
        {"id": 1, "name": "Build UI", "status": "done"},
        {"id": 2, "name": "Add bindings", "status": "done"},
        {"id": 3, "name": "Write tests", "status": "in-progress"},
        {"id": 4, "name": "Deploy", "status": "pending"},
    ]

pytonium.bind_function_to_javascript(get_system_info, javascript_object="dashboard")
pytonium.bind_function_to_javascript(get_tasks, javascript_object="dashboard")

# -- Context Menus --

pytonium.add_context_menu_entry(
    "panel", "Refresh Panel",
    lambda: pytonium.execute_javascript("refreshActivePanel()")
)
pytonium.add_context_menu_entry(
    "panel", "Reset Layout",
    lambda: pytonium.execute_javascript("resetLayout()")
)

# -- Initialization --

pytonium.add_custom_scheme("app", os.path.dirname(os.path.abspath(__file__)) + "/")
pytonium.set_context_menu_namespace("panel")
pytonium.initialize("app://index.html", 1200, 800)

# -- Main Loop: push live data --

tick = 0
while pytonium.is_running():
    time.sleep(0.5)
    pytonium.update_message_loop()
    tick += 1

    # Update system panel with current time
    pytonium.set_state("system", "uptime", str(tick))
    pytonium.set_state("system", "time", datetime.now().strftime("%H:%M:%S"))

    # Update network panel (simulated data)
    pytonium.set_state("network", "status", json.dumps({
        "connected": True,
        "latency_ms": 12 + (tick % 20),
        "bytes_sent": tick * 1024,
        "bytes_recv": tick * 2048
    }))

    # Append to activity log (last 20 entries)
    if tick % 5 == 0:
        pytonium.set_state("log", "entry", json.dumps({
            "time": datetime.now().strftime("%H:%M:%S"),
            "message": f"Event at tick {tick}"
        }))
```

---

## JavaScript: Multi-Panel Layout

```javascript title="app.js (key sections)"
document.addEventListener("PytoniumReady", function () {

    // -- System Panel --
    Pytonium.registerForStateUpdates("system", "time", function (value) {
        document.getElementById("sys-time").textContent = value;
    });
    Pytonium.registerForStateUpdates("system", "uptime", function (value) {
        document.getElementById("sys-uptime").textContent = value + "s";
    });

    // Load static system info on startup
    dashboard.get_system_info().then(function (info) {
        document.getElementById("sys-platform").textContent =
            info.platform + " " + info.version;
        document.getElementById("sys-python").textContent = info.python;
    });

    // -- Network Panel --
    Pytonium.registerForStateUpdates("network", "status", function (raw) {
        const net = JSON.parse(raw);
        document.getElementById("net-status").textContent =
            net.connected ? "Connected" : "Disconnected";
        document.getElementById("net-latency").textContent = net.latency_ms + " ms";
        document.getElementById("net-sent").textContent =
            (net.bytes_sent / 1024).toFixed(1) + " KB";
        document.getElementById("net-recv").textContent =
            (net.bytes_recv / 1024).toFixed(1) + " KB";
    });

    // -- Tasks Panel --
    dashboard.get_tasks().then(function (tasks) {
        const list = document.getElementById("task-list");
        list.innerHTML = "";
        tasks.forEach(function (task) {
            const li = document.createElement("li");
            li.className = "task task-" + task.status;
            li.textContent = task.name + " [" + task.status + "]";
            list.appendChild(li);
        });
    });

    // -- Log Panel --
    const logEntries = [];
    Pytonium.registerForStateUpdates("log", "entry", function (raw) {
        const entry = JSON.parse(raw);
        logEntries.push(entry);
        if (logEntries.length > 20) logEntries.shift();

        const logEl = document.getElementById("log-list");
        logEl.innerHTML = "";
        logEntries.forEach(function (e) {
            const div = document.createElement("div");
            div.className = "log-entry";
            div.textContent = e.time + " - " + e.message;
            logEl.appendChild(div);
        });
        logEl.scrollTop = logEl.scrollHeight;
    });
});
```

---

## Key Patterns

### State Namespaces for Panel Isolation

Each panel operates on its own state namespace. This keeps data organized and prevents key collisions:

| Namespace | Keys | Panel |
|---|---|---|
| `system` | `time`, `uptime` | System info |
| `network` | `status` | Network status |
| `log` | `entry` | Activity log |

A panel only subscribes to its own namespace, so updates to `"network"` do not trigger callbacks in the system panel.

### Context Menus

```python
pytonium.add_context_menu_entry(
    "panel", "Refresh Panel",
    lambda: pytonium.execute_javascript("refreshActivePanel()")
)
```

Context menu entries are grouped into namespaces. The `"panel"` namespace is activated with `set_context_menu_namespace("panel")`. When the user right-clicks anywhere in the window, they see the entries registered under that namespace.

!!! info "Dynamic Context Menus"
    You can switch context menu namespaces at runtime with `set_context_menu_namespace()`. This allows different right-click menus for different panels or application modes.

### Combining Bindings and State

This example uses both patterns:

- **Bindings** (`@returns_value_to_javascript`) for on-demand data requests: system info and task list are fetched once at startup.
- **State** (`set_state`) for continuous updates: time, uptime, network stats, and log entries are pushed from the main loop.

The general rule:

| Pattern | Use When |
|---|---|
| Bindings | JavaScript needs data on demand (user action, page load) |
| State | Python pushes data continuously (monitoring, live feeds) |

---

## Layout Approach

The dashboard uses a CSS Grid layout to arrange panels:

```css
.dashboard {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 16px;
    padding: 16px;
    height: 100vh;
}

.panel {
    background: #1a1a2e;
    border-radius: 8px;
    padding: 20px;
    border: 1px solid #333;
    overflow-y: auto;
}

.panel h3 {
    color: #bb86fc;
    margin-bottom: 12px;
    border-bottom: 1px solid #333;
    padding-bottom: 8px;
}
```

Each panel is a `<div class="panel">` inside the grid. The grid automatically handles sizing and responsiveness.

---

## Next Steps

- **[State Management Guide](../guides/state-management.md)** -- Full reference for namespaces, subscriptions, and patterns.
- **[Context Menus Guide](../guides/context-menus.md)** -- Full reference for custom right-click menus.
- **[Data Studio](data-studio.md)** -- A data analysis example with more complex bindings.
