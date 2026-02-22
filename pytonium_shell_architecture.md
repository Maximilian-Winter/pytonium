# PytoniumShell — Architecture Design

A desktop widget/shell framework for Windows (and Linux), built on Pytonium.
Widgets are authored as HTML/CSS/JS + Python, rendered via CEF in transparent frameless windows.

---

## 1. High-Level Overview

```
┌─────────────────────────────────────────────────────────┐
│                    PytoniumShell Core                    │
│                     (Python Process)                     │
├─────────────┬──────────────┬────────────────────────────┤
│  Shell Mgr  │  Widget Mgr  │  System Services Layer     │
│  - config   │  - lifecycle  │  - CPU/RAM/Disk (psutil)   │
│  - tray     │  - loading    │  - Audio (pycaw)           │
│  - hotkeys  │  - positions  │  - Network (psutil/wmi)    │
│             │  - hot reload │  - Virtual Desktops (COM)  │
│             │              │  - Notifications (win10toast)│
│             │              │  - Window list (win32gui)   │
├─────────────┴──────────────┴────────────────────────────┤
│              Pytonium (CEF + Python Bridge)              │
│  - Frameless transparent windows                         │
│  - JS ↔ Python function bindings                         │
│  - State management (namespaces)                         │
│  - Custom protocol schemes                               │
├─────────────────────────────────────────────────────────┤
│          Win32 API / OS Layer                            │
│  - SHAppBarMessage (dock bar, reserve screen space)      │
│  - SetWindowPos (always-on-top, z-order)                 │
│  - SetLayeredWindowAttributes (transparency)             │
│  - WS_EX_NOACTIVATE, WS_EX_TOOLWINDOW (no taskbar)      │
│  - RegisterHotKey (global hotkeys)                       │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure

```
~/.pytonium-shell/
├── config.json                  # Global shell config
├── widgets/
│   ├── bar/                     # A status bar widget
│   │   ├── widget.json          # Widget manifest
│   │   ├── index.html           # UI entry point
│   │   ├── style.css
│   │   ├── script.js
│   │   └── backend.py           # Python-side logic (optional)
│   ├── clock/
│   │   ├── widget.json
│   │   ├── index.html
│   │   └── backend.py
│   ├── system-monitor/
│   │   ├── widget.json
│   │   ├── index.html
│   │   └── backend.py
│   └── ...
└── themes/
    ├── default.json
    └── tokyo-night.json
```

---

## 3. Widget Manifest (`widget.json`)

Each widget declares its properties and window behavior:

```json
{
  "name": "status-bar",
  "version": "1.0.0",
  "description": "A top-of-screen status bar",
  "entry": "index.html",
  "backend": "backend.py",

  "window": {
    "mode": "bar",
    "anchor": "top",
    "height": 36,
    "monitor": "all",
    "reserve_space": true,
    "always_on_top": true,
    "click_through": false,
    "transparent_background": true,
    "show_in_taskbar": false
  },

  "permissions": [
    "system.cpu",
    "system.memory",
    "system.network",
    "audio",
    "virtual_desktops",
    "window_list"
  ],

  "state_namespaces": ["bar", "system"],

  "hot_reload": true
}
```

### Window Modes

| Mode        | Description                                           |
|-------------|-------------------------------------------------------|
| `bar`       | Docked to screen edge, reserves space via SHAppBarMessage |
| `overlay`   | Floating, always-on-top, no space reservation         |
| `widget`    | Floating, freely positionable, remembers position     |
| `wallpaper` | Behind all windows, fills screen                      |
| `dashboard` | Full-screen overlay, toggled via hotkey               |

---

## 4. Core Components

### 4.1 Shell Manager

The entry point. Manages the lifecycle of the entire shell.

```python
class ShellManager:
    """
    - Loads config.json
    - Discovers widgets in the widgets/ directory
    - Starts/stops WidgetManager instances
    - Manages the system tray icon (right-click menu for reload, quit, settings)
    - Registers global hotkeys
    - Runs the main Pytonium update loop
    """

    def __init__(self):
        self.config = load_config()
        self.widget_manager = WidgetManager(self.config)
        self.system_services = SystemServices()
        self.tray = SystemTrayIcon()

    def run(self):
        self.widget_manager.load_all_widgets()
        self.system_services.start()

        while self.is_running():
            time.sleep(0.01)
            self.widget_manager.update_all()
            self.system_services.poll()
```

### 4.2 Widget Manager

Handles discovering, loading, and managing individual widget instances.

```python
class WidgetManager:
    """
    For each widget directory:
    1. Parse widget.json manifest
    2. Create a Pytonium instance with appropriate window flags
    3. Load the optional backend.py and bind its functions/classes
    4. Bind system service data via state namespaces
    5. Set up file watching for hot reload
    """

    def load_widget(self, widget_path: str) -> WidgetInstance:
        manifest = load_manifest(widget_path / "widget.json")
        
        pytonium = Pytonium()
        
        # Configure window based on manifest
        pytonium.set_frameless_window(True)
        
        # Custom scheme to serve widget files
        pytonium.add_custom_scheme("widget", str(widget_path))
        
        # Load and bind backend.py if present
        if manifest.backend:
            backend_module = import_module(widget_path / manifest.backend)
            if hasattr(backend_module, "WidgetBackend"):
                backend = backend_module.WidgetBackend()
                pytonium.bind_object_methods_to_javascript(
                    backend, javascript_object="widget"
                )
        
        # Bind system services based on permissions
        self._bind_system_services(pytonium, manifest.permissions)
        
        # Initialize with appropriate size/position
        window_config = manifest.window
        pytonium.initialize(
            f"widget://index.html",
            window_config.width,
            window_config.height
        )
        
        # Apply Win32 window flags (after init, when HWND exists)
        self._apply_window_flags(pytonium, window_config)
        
        return WidgetInstance(pytonium, manifest)
```

### 4.3 System Services Layer

Polls or subscribes to system data and pushes it into Pytonium state namespaces.

```python
class SystemServices:
    """
    Periodically collects system data and pushes it into
    the shared state that widgets can subscribe to.
    """
    
    def __init__(self, shell_manager):
        self.shell = shell_manager
        self.poll_interval = 1.0  # seconds
    
    def poll(self):
        # CPU & Memory
        cpu = psutil.cpu_percent(percpu=True)
        mem = psutil.virtual_memory()
        self.push_state("system", "cpu_percent", cpu)
        self.push_state("system", "cpu_avg", sum(cpu) / len(cpu))
        self.push_state("system", "mem_total", mem.total)
        self.push_state("system", "mem_used", mem.used)
        self.push_state("system", "mem_percent", mem.percent)
        
        # Disk
        disk = psutil.disk_usage("/")
        self.push_state("system", "disk_percent", disk.percent)
        
        # Network
        net = psutil.net_io_counters()
        self.push_state("system", "net_sent", net.bytes_sent)
        self.push_state("system", "net_recv", net.bytes_recv)
        
        # Battery (if available)
        battery = psutil.sensors_battery()
        if battery:
            self.push_state("system", "battery_percent", battery.percent)
            self.push_state("system", "battery_charging", battery.power_plugged)
        
        # Audio volume (via pycaw)
        volume = self.get_audio_volume()
        self.push_state("audio", "volume", volume)
        self.push_state("audio", "muted", self.is_muted())
        
        # Date/Time
        now = datetime.now()
        self.push_state("datetime", "time", now.strftime("%H:%M"))
        self.push_state("datetime", "date", now.strftime("%d.%m.%Y"))
        self.push_state("datetime", "day", now.strftime("%A"))
    
    def push_state(self, namespace, key, value):
        """Push state to all widget Pytonium instances that
        have the namespace in their permissions."""
        for widget in self.shell.widget_manager.active_widgets:
            if namespace in widget.manifest.state_namespaces:
                widget.pytonium.set_state(namespace, key, value)
```

### 4.4 Win32 Window Integration

After Pytonium creates the CEF window, we need to apply OS-level window flags.

```python
import ctypes
import ctypes.wintypes
import win32gui
import win32con

class Win32WindowHelper:
    """
    Applies Windows-specific window properties to Pytonium windows.
    Must be called after pytonium.initialize() when the HWND exists.
    """
    
    @staticmethod
    def find_pytonium_hwnd(pytonium_instance) -> int:
        """Find the HWND of the Pytonium CEF window.
        This may require Pytonium to expose the HWND, or we
        enumerate windows to find it by PID/title."""
        # Option A: Pytonium exposes it directly (ideal — may need a small addition)
        # return pytonium_instance.get_hwnd()
        
        # Option B: Find by window enumeration
        pass
    
    @staticmethod
    def make_always_on_top(hwnd: int):
        win32gui.SetWindowPos(
            hwnd, win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )
    
    @staticmethod
    def make_wallpaper(hwnd: int):
        """Place window behind all others, above the desktop."""
        # Find the WorkerW window behind the desktop icons
        # and parent our widget to it
        pass
    
    @staticmethod
    def hide_from_taskbar(hwnd: int):
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        ex_style |= win32con.WS_EX_TOOLWINDOW  # Hides from taskbar
        ex_style &= ~win32con.WS_EX_APPWINDOW   # Remove app window flag
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
    
    @staticmethod
    def make_click_through(hwnd: int):
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        ex_style |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
    
    @staticmethod
    def dock_as_appbar(hwnd: int, edge: str, height: int):
        """Register as an AppBar to reserve screen space,
        like the Windows taskbar does."""
        # Uses SHAppBarMessage with ABM_NEW, ABM_SETPOS
        # edge: "top", "bottom", "left", "right"
        pass
    
    @staticmethod
    def set_position(hwnd: int, x: int, y: int, w: int, h: int):
        win32gui.SetWindowPos(
            hwnd, None, x, y, w, h,
            win32con.SWP_NOZORDER
        )
```

---

## 5. Widget JS API

Widgets get a `Shell` namespace injected alongside `Pytonium`, providing a clean API:

```typescript
// Auto-generated shell.d.ts

declare namespace Shell {
    /** System information (subscribe via state events) */
    namespace system {
        function getCpu(): Promise<number[]>;
        function getMemory(): Promise<{total: number, used: number, percent: number}>;
        function getDisk(): Promise<{total: number, used: number, percent: number}>;
        function getBattery(): Promise<{percent: number, charging: boolean} | null>;
        function getNetwork(): Promise<{sent: number, recv: number}>;
    }

    /** Audio control */
    namespace audio {
        function getVolume(): Promise<number>;
        function setVolume(level: number): void;
        function toggleMute(): void;
    }

    /** Window management */
    namespace window {
        function getActiveWindow(): Promise<{title: string, exe: string}>;
        function listWindows(): Promise<Array<{hwnd: number, title: string, exe: string}>>;
    }

    /** Virtual desktops */
    namespace desktops {
        function getCurrent(): Promise<number>;
        function getCount(): Promise<number>;
        function switchTo(index: number): void;
    }

    /** Widget self-control */
    namespace self {
        function setPosition(x: number, y: number): void;
        function setSize(width: number, height: number): void;
        function setOpacity(alpha: number): void;
        function setClickThrough(enabled: boolean): void;
        function close(): void;
        function reload(): void;
    }

    /** Theme access */
    namespace theme {
        function getColors(): Promise<ThemeColors>;
        function onThemeChanged(callback: (colors: ThemeColors) => void): void;
    }
}

interface ThemeColors {
    background: string;
    foreground: string;
    accent: string;
    muted: string;
    border: string;
    // ...extensible
}

// State subscription (using existing Pytonium appState)
// Pytonium.appState.registerForStateUpdates("systemUpdate", ["system"], true, true);
// document.addEventListener("systemUpdate", (e) => { ... });
```

---

## 6. Example Widget: System Monitor

### `widgets/system-monitor/widget.json`
```json
{
  "name": "system-monitor",
  "version": "1.0.0",
  "entry": "index.html",
  "backend": "backend.py",
  "window": {
    "mode": "widget",
    "width": 280,
    "height": 180,
    "position": { "x": 20, "y": 60 },
    "always_on_top": true,
    "transparent_background": true,
    "show_in_taskbar": false
  },
  "permissions": ["system.cpu", "system.memory"],
  "state_namespaces": ["system"],
  "hot_reload": true
}
```

### `widgets/system-monitor/index.html`
```html
<!DOCTYPE html>
<html>
<head>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        background: transparent;
        font-family: 'JetBrains Mono', 'Consolas', monospace;
        color: #a9b1d6;
    }
    .container {
        background: rgba(26, 27, 38, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        backdrop-filter: blur(12px);
    }
    .title {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #565f89;
        margin-bottom: 12px;
    }
    .metric {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .label { font-size: 13px; }
    .value { font-size: 13px; color: #7aa2f7; }
    .bar-bg {
        width: 100%;
        height: 4px;
        background: rgba(255,255,255,0.06);
        border-radius: 2px;
        margin-top: 4px;
    }
    .bar-fill {
        height: 100%;
        border-radius: 2px;
        transition: width 0.5s ease;
    }
    .bar-fill.cpu { background: #7aa2f7; }
    .bar-fill.mem { background: #bb9af7; }
    .bar-fill.disk { background: #9ece6a; }
</style>
</head>
<body>
<div class="container">
    <div class="title">System</div>

    <div class="metric">
        <span class="label">CPU</span>
        <span class="value" id="cpu-val">0%</span>
    </div>
    <div class="bar-bg"><div class="bar-fill cpu" id="cpu-bar" style="width: 0%"></div></div>

    <div class="metric" style="margin-top: 12px;">
        <span class="label">Memory</span>
        <span class="value" id="mem-val">0%</span>
    </div>
    <div class="bar-bg"><div class="bar-fill mem" id="mem-bar" style="width: 0%"></div></div>

    <div class="metric" style="margin-top: 12px;">
        <span class="label">Disk</span>
        <span class="value" id="disk-val">0%</span>
    </div>
    <div class="bar-bg"><div class="bar-fill disk" id="disk-bar" style="width: 0%"></div></div>
</div>

<script>
function init() {
    // Subscribe to system state updates
    Pytonium.appState.registerForStateUpdates(
        "systemUpdate", ["system"], true, true
    );

    document.addEventListener("systemUpdate", (event) => {
        const { key, value } = event.detail;

        if (key === "cpu_avg") {
            const pct = Math.round(value);
            document.getElementById("cpu-val").textContent = pct + "%";
            document.getElementById("cpu-bar").style.width = pct + "%";
        }
        if (key === "mem_percent") {
            const pct = Math.round(value);
            document.getElementById("mem-val").textContent = pct + "%";
            document.getElementById("mem-bar").style.width = pct + "%";
        }
        if (key === "disk_percent") {
            const pct = Math.round(value);
            document.getElementById("disk-val").textContent = pct + "%";
            document.getElementById("disk-bar").style.width = pct + "%";
        }
    });
}

if (window.PytoniumReady) { init(); }
else { window.addEventListener("PytoniumReady", init); }
</script>
</body>
</html>
```

---

## 7. Hot Reload

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class WidgetFileWatcher(FileSystemEventHandler):
    """Watches a widget's directory for changes and triggers reload."""
    
    def __init__(self, widget_instance):
        self.widget = widget_instance
        self.debounce_timer = None
    
    def on_modified(self, event):
        if event.src_path.endswith(('.html', '.css', '.js')):
            # Debounce: reload after 200ms of no changes
            self._schedule_reload()
        elif event.src_path.endswith('.py'):
            # Backend changed: full widget restart
            self._schedule_restart()
    
    def _schedule_reload(self):
        """Reload the CEF view (preserves window state)."""
        self.widget.pytonium.execute_javascript("location.reload()")
    
    def _schedule_restart(self):
        """Full restart: re-import backend, rebind, reload."""
        self.widget.manager.restart_widget(self.widget.name)
```

---

## 8. Theming

Themes are JSON files injected as CSS custom properties into every widget:

```json
{
  "name": "Tokyo Night",
  "colors": {
    "background": "rgba(26, 27, 38, 0.85)",
    "foreground": "#a9b1d6",
    "accent": "#7aa2f7",
    "accent2": "#bb9af7",
    "success": "#9ece6a",
    "warning": "#e0af68",
    "error": "#f7768e",
    "muted": "#565f89",
    "border": "rgba(255, 255, 255, 0.08)"
  },
  "font": {
    "family": "'JetBrains Mono', 'Consolas', monospace",
    "size": "13px"
  },
  "border_radius": "12px"
}
```

Injected into widgets via:
```python
def inject_theme(pytonium, theme):
    css_vars = ":root {\n"
    for key, val in theme["colors"].items():
        css_vars += f"  --shell-{key}: {val};\n"
    css_vars += f"  --shell-font: {theme['font']['family']};\n"
    css_vars += f"  --shell-radius: {theme['border_radius']};\n"
    css_vars += "}"
    
    js = f"document.head.insertAdjacentHTML('beforeend', '<style>{css_vars}</style>')"
    pytonium.execute_javascript(js)
```

Widgets then use `var(--shell-accent)` etc. in their CSS for automatic theming.

---

## 9. What Pytonium Might Need (Small Additions)

| Feature | Why | Difficulty |
|---------|-----|------------|
| `get_hwnd()` | Access the Win32 HWND for window flag manipulation | Easy — CEF already has it |
| Transparent background mode | CEF off-screen rendering with alpha channel | Medium — CEF supports this, needs a flag |
| `set_window_position(x, y, w, h)` | Position widgets precisely | Easy — Win32 `SetWindowPos` |
| Multiple instances per process | Run several Pytonium windows in one process | Medium — may already work if message loop is shared |
| Window events (focus, resize, move) | Widget self-awareness | Easy — Win32 message hook |

---

## 10. Implementation Roadmap

### Phase 1 — Proof of Concept
- [ ] Single transparent, always-on-top Pytonium widget (clock)
- [ ] Verify CEF transparent background on Windows
- [ ] Test Win32 flag manipulation (`WS_EX_TOOLWINDOW`, `HWND_TOPMOST`)
- [ ] Confirm multiple Pytonium instances can coexist

### Phase 2 — Core Framework
- [ ] ShellManager + WidgetManager with manifest loading
- [ ] System services polling (psutil basics)
- [ ] State bridge: system data → widget namespaces
- [ ] Widget hot reload via watchdog

### Phase 3 — Window Modes
- [ ] `bar` mode with `SHAppBarMessage` docking
- [ ] `widget` mode with position persistence
- [ ] `wallpaper` mode (behind desktop icons)
- [ ] `dashboard` mode (hotkey toggle overlay)

### Phase 4 — Polish
- [ ] Theming system
- [ ] System tray with widget management
- [ ] Global hotkey registration
- [ ] Widget marketplace / community structure
- [ ] Per-monitor widget configuration

---

## 11. Key Design Decisions

**One process vs. many?** — Ideally a single Python process hosting multiple CEF
browser views. This keeps memory manageable and allows shared state. Pytonium may
need a small refactor to support multiple windows per instance, or we run one
Pytonium instance per widget and use IPC (less ideal but simpler).

**State as the primary data flow** — Rather than having widgets poll Python for data,
the system services push state updates that widgets subscribe to via
`Pytonium.appState`. This is reactive, efficient, and matches how Pytonium already
works.

**Permissions model** — Widgets declare what they need in `widget.json`. The shell
only binds the requested services. This keeps the JS API surface small per widget
and makes it clear what data each widget can access.

**HTML/CSS/JS for UI, Python for backends** — Widget authors use web tech for the
visual layer and optionally write a `backend.py` for custom logic. This means the
entire npm/web ecosystem is available for UI, while Python handles system access.
