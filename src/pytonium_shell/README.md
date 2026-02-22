# PytoniumShell

A desktop widget framework for Windows, built on [Pytonium](../../readme.md).
Widgets are authored as HTML/CSS/JS with optional Python backends, rendered via CEF in frameless transparent windows.

Inspired by [Quickshell](https://quickshell.outfoxxed.me/) on Linux — but powered by Python instead of QML.

---

## Getting Started

### Requirements

- **Pytonium** >= 0.0.13
- **Python** 3.10+
- **Windows** 10/11

### Optional Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| `psutil` | System metrics (CPU, memory, disk, network, battery) | `pip install psutil` |
| `watchdog` | Hot reload (auto-refresh widgets on file changes) | `pip install watchdog` |
| `pystray` + `Pillow` | System tray icon with widget management menu | `pip install pystray Pillow` |

### Running

```bash
# Run the bundled example widgets
PYTHONPATH=src python -m pytonium_shell

# Run a specific widgets directory
PYTHONPATH=src python -m pytonium_shell --widgets-dir ./my_widgets

# With a custom config and theme
PYTHONPATH=src python -m pytonium_shell --widgets-dir ./my_widgets --config config.json --theme tokyo-night
```

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--widgets-dir` | bundled examples | Path to the directory containing widget folders |
| `--config` | *(none)* | Path to a `config.json` file for shell settings |
| `--theme` | `"default"` | Theme name (loads `<name>.json` from a themes directory) |

---

## Widgets

A widget is a directory containing at minimum a `widget.json` manifest and an `index.html` entry point.

### Directory Structure

```
my_widgets/
├── clock/
│   ├── widget.json          # Widget manifest (required)
│   ├── index.html           # UI entry point (required)
│   ├── style.css            # Optional separate stylesheet
│   └── script.js            # Optional separate script
├── system-monitor/
│   ├── widget.json
│   ├── index.html
│   └── backend.py           # Optional Python backend
└── ...
```

### Widget Manifest (`widget.json`)

```json
{
  "name": "my-widget",
  "version": "1.0.0",
  "description": "What this widget does",
  "entry": "index.html",
  "backend": "backend.py",

  "window": {
    "mode": "widget",
    "width": 280,
    "height": 200,
    "position": { "x": 20, "y": 20 },
    "anchor": "top",
    "height": 36,
    "reserve_space": true,
    "monitor": "primary",
    "always_on_top": true,
    "transparent_background": true,
    "show_in_taskbar": false,
    "click_through": false
  },

  "hotkey": "ctrl+alt+c",
  "permissions": ["system.cpu", "system.memory"],
  "state_namespaces": ["datetime", "system"],
  "hot_reload": true
}
```

### Manifest Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | *required* | Widget display name |
| `version` | string | — | Semantic version |
| `description` | string | — | Human-readable description |
| `entry` | string | `"index.html"` | HTML entry point filename |
| `backend` | string | — | Optional Python backend file |
| `hotkey` | string | — | Global hotkey to toggle this widget (e.g. `"ctrl+alt+c"`) |
| `permissions` | string[] | `[]` | Declared system data permissions |
| `state_namespaces` | string[] | `[]` | State namespaces this widget subscribes to |
| `hot_reload` | bool | `false` | Auto-reload on file changes (requires `watchdog`) |

### Window Configuration (`window` object)

| Field | Type | Default | Applies To | Description |
|-------|------|---------|------------|-------------|
| `mode` | string | `"widget"` | all | Window mode: `"widget"`, `"dashboard"`, `"bar"`, `"wallpaper"` |
| `width` | int | `300` | widget | Window width in pixels |
| `height` | int | `200` | widget, bar | Window height (or bar thickness) in pixels |
| `position` | object | — | widget | Initial position: `{"x": 0, "y": 0}` |
| `anchor` | string | `"top"` | bar | Dock edge: `"top"`, `"bottom"`, `"left"`, `"right"` |
| `reserve_space` | bool | `true` | bar | Reserve screen space (like the Windows taskbar) |
| `monitor` | string/int | `"primary"` | all | Target monitor: `"primary"` or monitor index (`0`, `1`, ...) |
| `always_on_top` | bool | `false` | widget, bar | Keep window above all others |
| `transparent_background` | bool | `false` | all | Enable per-pixel alpha transparency (OSR mode) |
| `show_in_taskbar` | bool | `true` | widget | Show in the Windows taskbar |
| `click_through` | bool | `false` | widget, wallpaper | Mouse events pass through to windows below |

---

## Window Modes

### `widget` — Floating Window

A freely positionable frameless window. Ideal for clocks, monitors, sticky notes.

- Positioned via `position` in manifest or restored from saved positions
- Supports `always_on_top`, `click_through`, transparency
- Position is persisted across restarts (saved to `widget_positions.json`)

```json
{
  "window": {
    "mode": "widget",
    "width": 220,
    "height": 100,
    "position": { "x": 20, "y": 20 },
    "always_on_top": true,
    "transparent_background": true,
    "show_in_taskbar": false
  }
}
```

### `dashboard` — Full-Screen Overlay

A full-screen overlay toggled by a global hotkey (default: `Ctrl+Alt+D`). Starts hidden.

- Covers the entire target monitor
- Fade-in / fade-out CSS animations on toggle
- Always on top, hidden from taskbar

```json
{
  "window": {
    "mode": "dashboard",
    "transparent_background": true
  }
}
```

The dashboard HTML should include these CSS rules for the toggle animation:

```css
body {
    opacity: 0;
    transition: opacity 0.3s ease;
}
body.fade-in  { opacity: 1; }
body.fade-out { opacity: 0; }
```

### `bar` — Docked Status Bar

A bar docked to a screen edge that reserves space (other windows won't overlap it), similar to the Windows taskbar. Uses the Win32 `SHAppBarMessage` API.

- Docks to `top`, `bottom`, `left`, or `right` edge
- Full width/height of the target monitor along the docked edge
- `reserve_space: true` makes the OS treat it like a taskbar

```json
{
  "window": {
    "mode": "bar",
    "anchor": "top",
    "height": 36,
    "reserve_space": true,
    "transparent_background": true
  }
}
```

### `wallpaper` — Behind Desktop Icons

A window rendered between the desktop wallpaper and the desktop icons. Uses the Win32 WorkerW/Progman technique.

- Covers the full target monitor
- Click-through by default (mouse passes to desktop icons)
- Survives `explorer.exe` restarts (periodic health check re-parents automatically)

```json
{
  "window": {
    "mode": "wallpaper",
    "transparent_background": false,
    "click_through": true,
    "monitor": "primary"
  }
}
```

---

## System Services & State

PytoniumShell polls system data via `psutil` and pushes it to widgets through Pytonium's state management system. Widgets declare which namespaces they want in `state_namespaces`.

### Available State Namespaces

#### `datetime`

| Key | Type | Example |
|-----|------|---------|
| `time` | string | `"14:30"` |
| `time_seconds` | string | `"14:30:45"` |
| `date` | string | `"22.02.2026"` |
| `day` | string | `"Saturday"` |

#### `system` (requires `psutil`)

| Key | Type | Example |
|-----|------|---------|
| `cpu_percent` | number[] | `[12.5, 8.3, 15.2, ...]` (per-core) |
| `cpu_avg` | number | `11.3` |
| `mem_total` | number | `17179869184` (bytes) |
| `mem_used` | number | `8589934592` (bytes) |
| `mem_percent` | number | `50.0` |
| `disk_total` | number | bytes |
| `disk_used` | number | bytes |
| `disk_percent` | number | `45.2` |
| `net_sent` | number | cumulative bytes sent |
| `net_recv` | number | cumulative bytes received |
| `battery_percent` | number | `85.0` (if battery present) |
| `battery_charging` | bool | `true` (if battery present) |

### Subscribing in JavaScript

```javascript
function init() {
    // Subscribe to state updates
    Pytonium.appState.registerForStateUpdates(
        "systemUpdate",     // custom event name
        ["system"],         // namespaces to subscribe to
        true,               // fire immediately with current values
        true                // receive all key updates
    );

    document.addEventListener("systemUpdate", function(event) {
        var key = event.detail.key;
        var value = event.detail.value;

        if (key === "cpu_avg") {
            document.getElementById("cpu").textContent = Math.round(value) + "%";
        }
    });
}

// Wait for Pytonium bindings to be ready
if (window.PytoniumReady) { init(); }
else { window.addEventListener("PytoniumReady", init); }
```

---

## Python Backend

Widgets can include an optional `backend.py` with a `WidgetBackend` class. All public methods are automatically bound to JavaScript under the `widget` namespace.

### `backend.py`

```python
import json

class WidgetBackend:
    def get_greeting(self, name):
        """Callable from JS as: widget.get_greeting("World")"""
        return f"Hello, {name}!"

    def get_data(self):
        """Return complex data as a JSON string."""
        return json.dumps({"items": [1, 2, 3], "count": 3})
```

### Calling from JavaScript

```javascript
// Simple call (no return value expected)
widget.get_greeting("World");

// Call with return value (returns a Promise)
widget.get_data().then(function(result) {
    var data = JSON.parse(result);
    console.log(data.items);
});
```

---

## Configuration (`config.json`)

An optional JSON file for shell-level settings, passed via `--config`.

```json
{
  "dashboard_hotkey": "ctrl+alt+d",
  "quit_hotkey": "ctrl+alt+q",
  "reload_hotkey": "ctrl+alt+r"
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `dashboard_hotkey` | string | `"ctrl+alt+d"` | Global hotkey to toggle dashboard widgets |
| `quit_hotkey` | string | *(none)* | Global hotkey to quit PytoniumShell |
| `reload_hotkey` | string | *(none)* | Global hotkey to reload all widget web views |

### Hotkey Format

Hotkeys are specified as `modifier+modifier+key` strings:

- **Modifiers**: `ctrl`, `alt`, `shift`, `win`
- **Keys**: `a`-`z`, `0`-`9`, `f1`-`f12`, `space`, `tab`, `escape`

Examples: `"ctrl+alt+d"`, `"shift+f1"`, `"ctrl+shift+r"`

---

## Theming

All widgets receive CSS custom properties injected by the shell. The default theme is **Tokyo Night**.

### Available CSS Variables

```css
/* Colors */
var(--shell-background)   /* rgba(26, 27, 38, 0.85) */
var(--shell-foreground)   /* #a9b1d6 */
var(--shell-accent)       /* #7aa2f7 */
var(--shell-accent2)      /* #bb9af7 */
var(--shell-success)      /* #9ece6a */
var(--shell-warning)      /* #e0af68 */
var(--shell-error)        /* #f7768e */
var(--shell-muted)        /* #565f89 */
var(--shell-border)       /* rgba(255, 255, 255, 0.08) */

/* Typography */
var(--shell-font)         /* 'Segoe UI', 'JetBrains Mono', 'Consolas', monospace */
var(--shell-font-size)    /* 13px */

/* Layout */
var(--shell-radius)       /* 12px */
```

### Custom Themes

Create a JSON file following the theme structure:

```json
{
  "name": "My Theme",
  "colors": {
    "background": "rgba(30, 30, 46, 0.9)",
    "foreground": "#cdd6f4",
    "accent": "#89b4fa",
    "accent2": "#cba6f7",
    "success": "#a6e3a1",
    "warning": "#f9e2af",
    "error": "#f38ba8",
    "muted": "#6c7086",
    "border": "rgba(255, 255, 255, 0.1)"
  },
  "font": {
    "family": "'Cascadia Code', 'Fira Code', monospace",
    "size": "14px"
  },
  "border_radius": "8px"
}
```

---

## System Tray

When `pystray` and `Pillow` are installed, PytoniumShell shows a system tray icon with a right-click menu:

- Toggle visibility of individual widgets (with checkmarks)
- Toggle dashboard overlay
- Reload all widgets
- Quit PytoniumShell

---

## Position Persistence

Widget-mode windows remember their position across restarts. Positions are saved to `widget_positions.json` next to the widgets directory.

- Auto-saves every 30 seconds while running
- Saves on shutdown
- Saved positions override the `position` field in `widget.json`

---

## Hot Reload

When `watchdog` is installed and `hot_reload: true` is set in the manifest, the shell watches the widget directory for changes:

- `.html`, `.css`, `.js` changes trigger a browser reload (200ms debounce)
- `.py` backend changes are detected (full restart support planned)

---

## Multi-Monitor Support

Widgets can target a specific monitor via the `monitor` field:

```json
{
  "window": {
    "monitor": "primary"
  }
}
```

| Value | Description |
|-------|-------------|
| `"primary"` | The primary display (default) |
| `0`, `1`, `2`... | Monitor by index (primary is `0`) |

This affects the positioning and sizing of `dashboard`, `bar`, and `wallpaper` mode widgets.

---

## Examples

Example widgets are provided in `pythonium_shell_examples/`, organized by mode for easy testing:

```
pythonium_shell_examples/
├── examples_widgets/            # Floating widgets (clock + system monitor)
│   ├── clock/
│   └── system-monitor/
├── examples_bar/                # Docked status bar
│   └── status-bar/
├── examples_wallpaper/          # Live wallpaper behind icons
│   └── live-wallpaper/
└── widgets_dashboard_example/   # Full-screen dashboard overlay
    └── dashboard/
```

Run each independently:

```bash
# Basic floating widgets
PYTHONPATH=src python -m pytonium_shell --widgets-dir pythonium_shell_examples/examples_widgets

# Status bar docked to top
PYTHONPATH=src python -m pytonium_shell --widgets-dir pythonium_shell_examples/examples_bar

# Live wallpaper behind desktop icons
PYTHONPATH=src python -m pytonium_shell --widgets-dir pythonium_shell_examples/examples_wallpaper

# Dashboard overlay (toggle with Ctrl+Alt+D)
PYTHONPATH=src python -m pytonium_shell --widgets-dir pythonium_shell_examples/widgets_dashboard_example
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    PytoniumShell Core                      │
│                     (Python Process)                       │
├──────────────┬──────────────┬─────────────────────────────┤
│  ShellManager │  WidgetMgr   │  System Services            │
│  - config     │  - lifecycle  │  - CPU/RAM/Disk (psutil)    │
│  - tray icon  │  - loading    │  - Network (psutil)         │
│  - hotkeys    │  - positions  │  - Battery (psutil)         │
│  - shutdown   │  - hot reload │  - DateTime                 │
├──────────────┴──────────────┴─────────────────────────────┤
│               Pytonium (CEF + Python Bridge)               │
│  - Frameless transparent windows (OSR)                     │
│  - JS <-> Python function bindings                         │
│  - State management (namespaces)                           │
├───────────────────────────────────────────────────────────┤
│             Win32 API / OS Layer                           │
│  - SHAppBarMessage (dock bar, reserve screen space)        │
│  - WorkerW / Progman (wallpaper mode)                      │
│  - SetWindowPos (always-on-top, positioning)               │
│  - RegisterHotKey (global hotkeys)                         │
│  - EnumDisplayMonitors (multi-monitor)                     │
└───────────────────────────────────────────────────────────┘
```

### Source Files

| File | Purpose |
|------|---------|
| `shell_manager.py` | Main lifecycle, config, hotkey/tray dispatch |
| `widget_manager.py` | Widget discovery, loading, mode setup, dashboard toggle |
| `widget_instance.py` | Per-widget data container |
| `win32_window_helper.py` | Win32 API wrappers (ctypes) |
| `system_services.py` | psutil polling, state push |
| `hotkey_listener.py` | Multi-hotkey RegisterHotKey on background thread |
| `system_tray.py` | pystray system tray icon |
| `position_store.py` | Widget position persistence (JSON) |
| `theme.py` | Theme loading and CSS variable injection |
| `hot_reload.py` | watchdog file watcher |
| `__main__.py` | CLI entry point |
