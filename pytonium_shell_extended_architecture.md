# PytoniumShell — Extended Architecture

## A Full Desktop Environment Framework for Windows (and Linux)

Instead of fighting OS-specific APIs for wallpaper injection, taskbar docking, and
window management — all of which break across OS versions — PytoniumShell takes a
different approach: go fullscreen and *become* the desktop.

The OS becomes a headless backend. Pytonium renders the entire visual layer.
Python queries the real desktop state. HTML/CSS/JS draws whatever you want.

---

## 1. Core Concept: Virtual Desktop Compositor

```
┌──────────────────────────────────────────────────────────────────┐
│                        SCREEN (MONITOR)                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Layer 4: OVERLAYS         (notifications, popups, menus)   │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ Layer 3: TASKBAR / DOCK   (app launcher, window list, tray)│  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ Layer 2: WIDGETS          (clock, monitor, weather, etc.)  │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ Layer 1: DESKTOP ICONS    (mirrored filesystem / shortcuts)│  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ Layer 0: WALLPAPER        (static, animated, or live)      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Real OS windows appear ABOVE all layers (managed by OS)         │
└──────────────────────────────────────────────────────────────────┘
```

Each layer is a Pytonium instance (or a logical division within fewer instances).
The Python + C++ backend mirrors the real OS desktop state and feeds it to the
JS rendering layer through the existing state/binding system.

**Key principle:** The OS handles window management, process lifecycle, and input
routing as normal. PytoniumShell only replaces the *visual shell* — wallpaper,
taskbar, desktop icons, widgets. Real application windows float above everything
and work exactly as they normally would.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PytoniumShell Process                          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Shell Manager (Python)                    │   │
│  │  - Loads shell configuration and theme                      │   │
│  │  - Manages layer lifecycle                                  │   │
│  │  - Routes OS events to appropriate layers                   │   │
│  │  - Handles global hotkeys                                   │   │
│  │  - System tray fallback icon                                │   │
│  └────────────┬────────────────────────────────────────────────┘   │
│               │                                                     │
│  ┌────────────▼────────────────────────────────────────────────┐   │
│  │                  Layer Manager (Python)                      │   │
│  │  - Creates/destroys Pytonium instances per layer            │   │
│  │  - Manages z-ordering and input routing                     │   │
│  │  - Handles layer visibility toggling                        │   │
│  │  - Per-monitor layer configuration                          │   │
│  └────────────┬────────────────────────────────────────────────┘   │
│               │                                                     │
│  ┌────────────▼────────────────────────────────────────────────┐   │
│  │               OS Integration Layer (C++)                     │   │
│  │                                                              │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌─────────────────────┐ │   │
│  │  │ Window       │ │ Shell        │ │ Input               │ │   │
│  │  │ Monitor      │ │ Integration  │ │ Management          │ │   │
│  │  │              │ │              │ │                     │ │   │
│  │  │ - EnumWindows│ │ - Tray icons │ │ - Global hotkeys   │ │   │
│  │  │ - Shell hooks│ │ - App index  │ │ - Mouse passthru   │ │   │
│  │  │ - DWM thumbs │ │ - File ops   │ │ - Focus mgmt       │ │   │
│  │  │ - WndProc    │ │ - Clipboard  │ │ - Drag & drop      │ │   │
│  │  │   intercept  │ │ - Notif hook │ │ - CBT hooks        │ │   │
│  │  └──────────────┘ └──────────────┘ └─────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │            Pytonium Instances (C++ / CEF)                    │   │
│  │                                                              │   │
│  │  [Wallpaper]  [Desktop]  [Widgets]  [Taskbar]  [Overlays]  │   │
│  │   HWND_BOTTOM  ───── z-order managed by C++ ─────  TOPMOST │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Real OS Windows   │
                    │  (managed by Win32) │
                    │                     │
                    │  Appear above the   │
                    │  desktop layers,    │
                    │  below overlays     │
                    └────────────────────┘
```

---

## 3. Layer System

### 3.1 Layer Configuration (`shell.json`)

```json
{
  "shell": {
    "name": "My Custom Desktop",
    "theme": "tokyo-night",
    "monitors": "all"
  },

  "layers": [
    {
      "id": "wallpaper",
      "type": "wallpaper",
      "z_order": 0,
      "entry": "layers/wallpaper/index.html",
      "backend": "layers/wallpaper/backend.py",
      "config": {
        "mode": "animated",
        "source": "layers/wallpaper/assets/particles.js"
      }
    },
    {
      "id": "desktop-icons",
      "type": "desktop",
      "z_order": 1,
      "entry": "layers/desktop/index.html",
      "backend": "layers/desktop/backend.py",
      "input": "passthrough_when_inactive",
      "config": {
        "icon_size": 64,
        "grid_spacing": 90,
        "show_labels": true,
        "folders": ["Desktop", "Documents"]
      }
    },
    {
      "id": "widgets",
      "type": "widget_host",
      "z_order": 2,
      "entry": "layers/widgets/index.html",
      "backend": "layers/widgets/backend.py",
      "input": "passthrough_when_inactive",
      "config": {
        "widgets": [
          { "widget": "clock", "x": 20, "y": 20 },
          { "widget": "system-monitor", "x": 20, "y": 160 },
          { "widget": "weather", "x": 20, "y": 400 }
        ]
      }
    },
    {
      "id": "taskbar",
      "type": "taskbar",
      "z_order": 3,
      "entry": "layers/taskbar/index.html",
      "backend": "layers/taskbar/backend.py",
      "input": "always_active",
      "config": {
        "position": "top",
        "height": 40,
        "auto_hide": false,
        "components": ["app_menu", "window_list", "system_tray", "clock"]
      }
    },
    {
      "id": "overlays",
      "type": "overlay",
      "z_order": 4,
      "entry": "layers/overlays/index.html",
      "backend": "layers/overlays/backend.py",
      "input": "passthrough_when_inactive",
      "config": {
        "notifications": true,
        "app_launcher": { "hotkey": "Super+Space" },
        "dashboard": { "hotkey": "Super+D" }
      }
    }
  ]
}
```

### 3.2 Layer Types and Behavior

| Type           | Z-Order    | Input Behavior        | Fullscreen | Purpose                          |
|----------------|------------|-----------------------|------------|----------------------------------|
| `wallpaper`    | Bottom     | Click-through always  | Yes        | Background visuals               |
| `desktop`      | Low        | Active on click       | Yes        | File icons, shortcuts            |
| `widget_host`  | Mid        | Per-widget hit areas  | Yes        | Contains positioned widgets      |
| `taskbar`      | High       | Always active         | Partial    | Bar docked to edge               |
| `overlay`      | Top        | Active when shown     | Yes        | Popups, notifications, launcher  |

### 3.3 Layer Instance Management

```python
class LayerManager:
    """
    Creates and manages Pytonium instances for each layer.
    Handles z-ordering via the C++ OS integration layer.
    """

    def __init__(self, shell_config: dict):
        self.layers: dict[str, LayerInstance] = {}
        self.os_integration = OSIntegration()

    def load_layers(self, layer_configs: list[dict]):
        for config in sorted(layer_configs, key=lambda c: c["z_order"]):
            layer = LayerInstance(config)
            layer.pytonium = Pytonium()
            layer.pytonium.set_frameless_window(True)

            # Load optional backend
            if config.get("backend"):
                layer.backend = self._load_backend(config["backend"])
                layer.pytonium.bind_object_methods_to_javascript(
                    layer.backend, javascript_object="layer"
                )

            # Bind OS integration based on layer type
            self._bind_layer_services(layer)

            # Bind theme
            self._inject_theme(layer)

            # Custom scheme for layer assets
            layer.pytonium.add_custom_scheme(
                f"shell-{config['id']}",
                os.path.dirname(os.path.abspath(config["entry"]))
            )

            # Initialize fullscreen or partial
            if config.get("type") == "taskbar":
                layer.pytonium.initialize_positioned(
                    config["entry"],
                    x=0, y=0,
                    width=monitor_width,
                    height=config["config"]["height"]
                )
            else:
                layer.pytonium.initialize_fullscreen(config["entry"])

            # Apply z-ordering and window flags via C++ layer
            self.os_integration.configure_layer_window(
                layer.pytonium.get_hwnd(),
                layer_type=config["type"],
                z_order=config["z_order"],
                input_mode=config.get("input", "passthrough_when_inactive")
            )

            self.layers[config["id"]] = layer

    def update_all(self):
        for layer in self.layers.values():
            layer.pytonium.update_message_loop()
```

---

## 4. OS Integration Layer (C++)

This is the core of what makes it work. Implemented in C++ inside the Pytonium
library, exposed to Python via Cython bindings.

### 4.1 Window Monitor

Tracks all real OS windows and exposes their state to the taskbar/overlay layers.

```cpp
class WindowMonitor {
public:
    // Start monitoring with a shell hook
    void Start() {
        // RegisterShellHookWindow gives us notifications for:
        // - HSHELL_WINDOWCREATED
        // - HSHELL_WINDOWDESTROYED
        // - HSHELL_WINDOWACTIVATED
        // - HSHELL_REDRAW (title changes)
        // - HSHELL_FLASH (window requesting attention)

        shellHookMsg_ = RegisterWindowMessage(L"SHELLHOOK");
        RegisterShellHookWindow(monitorHwnd_);

        // Initial enumeration
        EnumWindows(EnumCallback, reinterpret_cast<LPARAM>(this));
    }

    // Called from WndProc when shell hook messages arrive
    void OnShellHook(WPARAM event, LPARAM lParam) {
        HWND hwnd = reinterpret_cast<HWND>(lParam);

        switch (event) {
            case HSHELL_WINDOWCREATED:
                AddWindow(hwnd);
                NotifyListeners("window_created", GetWindowInfo(hwnd));
                break;
            case HSHELL_WINDOWDESTROYED:
                RemoveWindow(hwnd);
                NotifyListeners("window_destroyed", hwnd);
                break;
            case HSHELL_WINDOWACTIVATED:
                SetActiveWindow(hwnd);
                NotifyListeners("window_activated", GetWindowInfo(hwnd));
                break;
            case HSHELL_FLASH:
                NotifyListeners("window_flash", hwnd);
                break;
        }
    }

    // Get structured info about a window
    WindowInfo GetWindowInfo(HWND hwnd) {
        WindowInfo info;
        info.hwnd = hwnd;

        // Title
        wchar_t title[256];
        GetWindowText(hwnd, title, 256);
        info.title = WideToUtf8(title);

        // Process name and icon
        DWORD pid;
        GetWindowThreadProcessId(hwnd, &pid);
        info.pid = pid;
        info.exe = GetProcessName(pid);
        info.icon = ExtractWindowIcon(hwnd);  // As base64 PNG

        // Geometry
        RECT rect;
        GetWindowRect(hwnd, &rect);
        info.x = rect.left;
        info.y = rect.top;
        info.width = rect.right - rect.left;
        info.height = rect.bottom - rect.top;

        // State
        info.minimized = IsIconic(hwnd);
        info.maximized = IsZoomed(hwnd);
        info.visible = IsWindowVisible(hwnd);

        return info;
    }

    // Get DWM live thumbnail for window preview
    void RegisterThumbnail(HWND source, HWND destination, int x, int y,
                           int width, int height) {
        HTHUMBNAIL thumb;
        DwmRegisterThumbnail(destination, source, &thumb);

        DWM_THUMBNAIL_PROPERTIES props;
        props.dwFlags = DWM_TNP_RECTDESTINATION | DWM_TNP_VISIBLE;
        props.rcDestination = { x, y, x + width, y + height };
        props.fVisible = TRUE;
        DwmUpdateThumbnailProperties(thumb, &props);
    }

    // Window control actions (called from JS via Python)
    void MinimizeWindow(HWND hwnd) { ShowWindow(hwnd, SW_MINIMIZE); }
    void MaximizeWindow(HWND hwnd) { ShowWindow(hwnd, SW_MAXIMIZE); }
    void RestoreWindow(HWND hwnd)  { ShowWindow(hwnd, SW_RESTORE); }
    void CloseWindow(HWND hwnd)    { PostMessage(hwnd, WM_CLOSE, 0, 0); }
    void FocusWindow(HWND hwnd)    { SetForegroundWindow(hwnd); }

private:
    std::vector<WindowInfo> windows_;
    UINT shellHookMsg_;
    HWND monitorHwnd_;  // Hidden helper window for receiving shell hooks
};
```

### 4.2 Layer Window Manager

Controls z-ordering and input behavior for PytoniumShell layer windows.

```cpp
class LayerWindowManager {
public:
    // Configure a Pytonium HWND as a specific layer type
    void ConfigureLayerWindow(HWND hwnd, LayerType type, int zOrder,
                              InputMode inputMode) {
        // Remove from taskbar and Alt-Tab
        LONG exStyle = GetWindowLong(hwnd, GWL_EXSTYLE);
        exStyle |= WS_EX_TOOLWINDOW;    // No taskbar entry
        exStyle &= ~WS_EX_APPWINDOW;    // No Alt-Tab entry

        switch (type) {
            case LayerType::Wallpaper:
                // Sit at the very bottom, always click-through
                exStyle |= WS_EX_TRANSPARENT | WS_EX_LAYERED;
                SetWindowLong(hwnd, GWL_EXSTYLE, exStyle);
                SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0,
                            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
                break;

            case LayerType::Desktop:
            case LayerType::WidgetHost:
                // Above wallpaper, below real windows
                // Input: passthrough except on widget hit areas
                SetWindowLong(hwnd, GWL_EXSTYLE, exStyle);
                SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0,
                            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
                if (inputMode == InputMode::PassthroughWhenInactive) {
                    InstallInputFilter(hwnd);
                }
                break;

            case LayerType::Taskbar:
                // Above desktop layers, below real windows
                // Always receives input in its area
                SetWindowLong(hwnd, GWL_EXSTYLE, exStyle);
                // Reserve screen space so real windows don't overlap
                RegisterAppBar(hwnd);
                break;

            case LayerType::Overlay:
                // Topmost, but only when active
                exStyle |= WS_EX_TOPMOST;
                exStyle |= WS_EX_TRANSPARENT | WS_EX_LAYERED;
                SetWindowLong(hwnd, GWL_EXSTYLE, exStyle);
                break;
        }

        layerWindows_[zOrder] = { hwnd, type, inputMode };
    }

    // Handle z-ordering when real windows appear/disappear
    void OnRealWindowActivated(HWND realHwnd) {
        // Ensure our layers maintain correct z-order:
        // Wallpaper < Desktop < Widgets < [Real Windows] < Taskbar < Overlays
        //
        // The trick: wallpaper/desktop/widgets stay at HWND_BOTTOM
        // Taskbar uses AppBar reservation
        // Overlays only go TOPMOST when explicitly shown
        //
        // Real windows naturally sit in the middle without any intervention.
    }

private:
    struct LayerWindow {
        HWND hwnd;
        LayerType type;
        InputMode inputMode;
    };

    std::map<int, LayerWindow> layerWindows_;

    // AppBar registration for taskbar space reservation
    void RegisterAppBar(HWND hwnd) {
        APPBARDATA abd = {};
        abd.cbSize = sizeof(abd);
        abd.hWnd = hwnd;
        abd.uCallbackMessage = WM_USER + 0x100;
        SHAppBarMessage(ABM_NEW, &abd);

        // Set position (top of screen example)
        abd.uEdge = ABE_TOP;
        abd.rc = { 0, 0, GetSystemMetrics(SM_CXSCREEN), 40 };
        SHAppBarMessage(ABM_SETPOS, &abd);
    }

    // Subclass the layer window to filter input
    void InstallInputFilter(HWND hwnd) {
        // Subclass WndProc to intercept WM_NCHITTEST
        // Return HTTRANSPARENT for areas that should pass through
        // Return HTCLIENT for areas that should receive input
        // The JS layer communicates hit-test regions via shared memory
        // or a callback that checks element positions
        SetWindowSubclass(hwnd, InputFilterProc, 0,
                         reinterpret_cast<DWORD_PTR>(this));
    }

    static LRESULT CALLBACK InputFilterProc(
        HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam,
        UINT_PTR subclassId, DWORD_PTR refData
    ) {
        if (msg == WM_NCHITTEST) {
            auto* self = reinterpret_cast<LayerWindowManager*>(refData);
            POINT pt = { GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam) };
            ScreenToClient(hwnd, &pt);

            // Ask the JS layer if this point hits any interactive element
            if (!self->IsPointInteractive(hwnd, pt.x, pt.y)) {
                return HTTRANSPARENT;  // Pass input to window below
            }
        }
        return DefSubclassProc(hwnd, msg, wParam, lParam);
    }
};
```

### 4.3 Input Hit-Testing Bridge

The critical mechanism that allows click-through on empty areas while keeping
widgets and taskbar interactive.

```cpp
class HitTestBridge {
    // Two approaches, use whichever fits better:

    // Approach A: Region-based (simpler, less granular)
    // JS sends a list of interactive rectangles to C++ via binding.
    // Fast to check, but needs updating when widgets move/resize.
    struct InteractiveRegion {
        int x, y, width, height;
        std::string elementId;
    };
    std::vector<InteractiveRegion> regions_;

    void UpdateRegions(const std::vector<InteractiveRegion>& regions) {
        regions_ = regions;
    }

    bool IsPointInRegion(int px, int py) {
        for (const auto& r : regions_) {
            if (px >= r.x && px < r.x + r.width &&
                py >= r.y && py < r.y + r.height) {
                return true;
            }
        }
        return false;
    }

    // Approach B: Pixel-based (precise, works with any shape)
    // Use CEF's off-screen rendering to check the alpha channel at a point.
    // If the pixel is transparent, pass through. If opaque, handle input.
    // This is elegant because it means the CSS itself defines the hit area.
    bool IsPointOnContent(HWND hwnd, int px, int py) {
        // Query the CEF OSR buffer for alpha at (px, py)
        // Return true if alpha > threshold (e.g., > 10)
        return GetAlphaAtPoint(hwnd, px, py) > 10;
    }
};
```

### 4.4 System Tray Integration

```cpp
class TrayMonitor {
public:
    void Start() {
        // Method 1: Read tray icons from the toolbar control
        // inside Shell_TrayWnd > TrayNotifyWnd > SysPager > ToolbarWindow32
        //
        // This involves:
        // 1. FindWindow to get the toolbar HWND
        // 2. TB_BUTTONCOUNT to get icon count
        // 3. TB_GETBUTTON to read each entry
        // 4. ReadProcessMemory (since the toolbar is in explorer.exe's space)
        //
        // Dirty but well-documented and widely used.

        // Method 2: Use the INotificationAreaSink COM interface (Windows 10+)
        // Cleaner but less documented.

        // Method 3: Register our own tray icons and hook the notification
        // callback to intercept messages meant for the real tray.
    }

    struct TrayIcon {
        HWND ownerHwnd;
        UINT id;
        std::string tooltip;
        std::string iconBase64;  // Icon as base64 PNG for rendering in HTML
        bool visible;
    };

    std::vector<TrayIcon> GetTrayIcons() {
        // Enumerate and return all current tray icons
    }

    void TrayIconClick(HWND owner, UINT id, int button) {
        // Forward click to the real tray icon owner
        // Simulate the notification callback message
    }
};
```

### 4.5 Notification Interception

```cpp
class NotificationMonitor {
public:
    void Start() {
        // Option A: UI Automation
        // Use Windows UI Automation API to monitor the Action Center
        // for new notification elements.

        // Option B: WNF (Windows Notification Facility)
        // Subscribe to WNF state changes for toast notifications.
        // Undocumented but stable across Windows 10/11.

        // Option C: User Notification Listener API (WinRT)
        // UserNotificationListener::Current().GetNotificationsAsync()
        // Cleanest approach, requires declaring the capability.
    }

    struct Notification {
        std::string appName;
        std::string title;
        std::string body;
        std::string iconBase64;
        std::string timestamp;
        std::string id;
    };

    void OnNotificationReceived(const Notification& notification) {
        // Push to Python via callback, which then pushes to
        // the overlay layer via state system
    }

    void DismissNotification(const std::string& id) {
        // Dismiss the real OS notification
    }
};
```

---

## 5. Python Service Layer

Bridges the C++ OS integration with the layer system via Pytonium state management.

```python
class DesktopServices:
    """
    High-level Python API that wraps the C++ OS integration
    and feeds data into layer state namespaces.
    """

    def __init__(self, os_integration, layer_manager):
        self.os = os_integration
        self.layers = layer_manager

    def start(self):
        # Register callbacks from C++ to Python
        self.os.window_monitor.on_event(self._on_window_event)
        self.os.tray_monitor.on_event(self._on_tray_event)
        self.os.notification_monitor.on_event(self._on_notification)

        # Start polling services
        self.system_poller = SystemPoller(interval=1.0)
        self.system_poller.start()

    def _on_window_event(self, event_type: str, window_info: dict):
        """Window created/destroyed/activated/flashed."""
        # Update the window list state
        windows = self.os.window_monitor.get_all_windows()
        self.layers.push_state("windows", "list", windows)
        self.layers.push_state("windows", "active", window_info.get("hwnd"))
        self.layers.push_state("windows", "event", {
            "type": event_type,
            "window": window_info
        })

    def _on_tray_event(self, event_type: str, icon_info: dict):
        """Tray icon added/removed/updated."""
        icons = self.os.tray_monitor.get_all_icons()
        self.layers.push_state("tray", "icons", icons)

    def _on_notification(self, notification: dict):
        """OS notification received."""
        self.layers.push_state("notifications", "new", notification)


class SystemPoller:
    """Periodic system data collection via psutil."""

    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self._running = False

    def poll(self):
        import psutil

        # CPU
        cpu_percent = psutil.cpu_percent(percpu=True)
        cpu_avg = sum(cpu_percent) / len(cpu_percent)
        cpu_freq = psutil.cpu_freq()

        # Memory
        mem = psutil.virtual_memory()

        # Disk
        disk = psutil.disk_usage("/")

        # Network
        net = psutil.net_io_counters()

        # Battery
        battery = psutil.sensors_battery()

        # GPU (if GPUtil available)
        gpu = self._get_gpu_info()

        return {
            "cpu": {
                "percent": cpu_percent,
                "avg": cpu_avg,
                "freq": cpu_freq.current if cpu_freq else 0,
                "cores": psutil.cpu_count()
            },
            "memory": {
                "total": mem.total,
                "used": mem.used,
                "percent": mem.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "percent": disk.percent
            },
            "network": {
                "sent": net.bytes_sent,
                "recv": net.bytes_recv
            },
            "battery": {
                "percent": battery.percent,
                "charging": battery.power_plugged
            } if battery else None,
            "gpu": gpu
        }
```

---

## 6. JS API for Layers

Each layer gets access to both the `Pytonium` namespace and a `Shell` namespace
that provides the desktop integration API.

```typescript
declare namespace Shell {

    // ── Window Management ──────────────────────────────────

    namespace windows {
        /** List of all real OS windows */
        function getAll(): Promise<WindowInfo[]>;

        /** Currently focused window */
        function getActive(): Promise<WindowInfo | null>;

        /** Window control */
        function minimize(hwnd: number): void;
        function maximize(hwnd: number): void;
        function restore(hwnd: number): void;
        function close(hwnd: number): void;
        function focus(hwnd: number): void;

        /** Request a DWM thumbnail of a window, rendered into an HTML element */
        function requestThumbnail(hwnd: number, elementId: string,
                                  width: number, height: number): void;

        /** Subscribe to window events */
        function onWindowEvent(
            callback: (event: WindowEvent) => void
        ): void;
    }

    interface WindowInfo {
        hwnd: number;
        title: string;
        exe: string;
        pid: number;
        iconBase64: string;
        x: number; y: number;
        width: number; height: number;
        minimized: boolean;
        maximized: boolean;
        visible: boolean;
    }

    interface WindowEvent {
        type: "created" | "destroyed" | "activated" | "flash" | "title_changed";
        window: WindowInfo;
    }

    // ── System Tray ────────────────────────────────────────

    namespace tray {
        function getIcons(): Promise<TrayIcon[]>;
        function click(ownerHwnd: number, id: number, button: number): void;
        function onChanged(callback: (icons: TrayIcon[]) => void): void;
    }

    interface TrayIcon {
        ownerHwnd: number;
        id: number;
        tooltip: string;
        iconBase64: string;
        visible: boolean;
    }

    // ── Desktop / File System ──────────────────────────────

    namespace desktop {
        /** List files/folders on the user's desktop */
        function getItems(): Promise<DesktopItem[]>;

        /** Open a file or folder */
        function open(path: string): void;

        /** Get icon for a file type */
        function getFileIcon(path: string): Promise<string>;

        /** Watch for changes */
        function onChanged(callback: (items: DesktopItem[]) => void): void;
    }

    interface DesktopItem {
        name: string;
        path: string;
        isDirectory: boolean;
        iconBase64: string;
        size: number;
        modified: string;
    }

    // ── App Launcher ───────────────────────────────────────

    namespace apps {
        /** Search installed applications */
        function search(query: string): Promise<AppInfo[]>;

        /** Get all installed applications */
        function getAll(): Promise<AppInfo[]>;

        /** Launch an application */
        function launch(path: string): void;

        /** Get recently used apps */
        function getRecent(): Promise<AppInfo[]>;
    }

    interface AppInfo {
        name: string;
        path: string;
        iconBase64: string;
        category: string;
    }

    // ── Notifications ──────────────────────────────────────

    namespace notifications {
        function getAll(): Promise<Notification[]>;
        function dismiss(id: string): void;
        function dismissAll(): void;
        function onNew(callback: (n: Notification) => void): void;
    }

    interface Notification {
        id: string;
        appName: string;
        title: string;
        body: string;
        iconBase64: string;
        timestamp: string;
    }

    // ── System Data (via state subscriptions) ──────────────

    namespace system {
        function getCpu(): Promise<CpuInfo>;
        function getMemory(): Promise<MemoryInfo>;
        function getDisk(): Promise<DiskInfo>;
        function getNetwork(): Promise<NetworkInfo>;
        function getBattery(): Promise<BatteryInfo | null>;
    }

    // ── Audio ──────────────────────────────────────────────

    namespace audio {
        function getVolume(): Promise<number>;
        function setVolume(level: number): void;
        function toggleMute(): void;
        function isMuted(): Promise<boolean>;

        /** Per-application audio (Windows audio mixer) */
        function getAppVolumes(): Promise<AppAudio[]>;
        function setAppVolume(pid: number, level: number): void;
    }

    interface AppAudio {
        pid: number;
        name: string;
        iconBase64: string;
        volume: number;
        muted: boolean;
    }

    // ── Virtual Desktops ───────────────────────────────────

    namespace desktops {
        function getCurrent(): Promise<number>;
        function getCount(): Promise<number>;
        function switchTo(index: number): void;
        function create(): void;
        function remove(index: number): void;
        function getWindowsOnDesktop(index: number): Promise<WindowInfo[]>;
    }

    // ── Clipboard ──────────────────────────────────────────

    namespace clipboard {
        function getText(): Promise<string>;
        function setText(text: string): void;
        function getImage(): Promise<string | null>;  // base64
        function onChanged(callback: (content: ClipboardContent) => void): void;
    }

    // ── Layer Self-Control ─────────────────────────────────

    namespace layer {
        function show(): void;
        function hide(): void;
        function setOpacity(alpha: number): void;
        function isVisible(): Promise<boolean>;

        /** Update interactive regions for hit-testing */
        function setInteractiveRegions(regions: InteractiveRegion[]): void;
    }

    interface InteractiveRegion {
        x: number; y: number;
        width: number; height: number;
        id: string;
    }

    // ── Theme ──────────────────────────────────────────────

    namespace theme {
        function getColors(): Promise<ThemeColors>;
        function onChanged(callback: (colors: ThemeColors) => void): void;
    }

    // ── Global Hotkeys ─────────────────────────────────────

    namespace hotkeys {
        function register(combo: string, callback: () => void): void;
        function unregister(combo: string): void;
    }
}
```

---

## 7. Input Flow and Hit-Testing

The most critical technical challenge: letting clicks pass through to real windows
on empty areas, while keeping layer UI elements interactive.

```
User clicks at screen position (x, y)
           │
           ▼
┌──────────────────────────────────┐
│  Win32 dispatches to topmost     │
│  window at (x, y)                │
│           │                      │
│           ▼                      │
│  Is it a PytoniumShell layer?    │
│     │              │             │
│    YES             NO            │
│     │              └──► Normal   │
│     ▼                  window    │
│  WndProc subclass                │
│  calls WM_NCHITTEST              │
│     │                            │
│     ▼                            │
│  Check hit-test:                 │
│  ┌───────────────────────┐       │
│  │ Pixel alpha > 0?      │       │
│  │ OR in interactive     │       │
│  │ region list?          │       │
│  │     │          │      │       │
│  │    YES         NO     │       │
│  │     │          │      │       │
│  │  HTCLIENT  HTTRANSPARENT     │
│  │  (handle)  (pass through)    │
│  └───────────────────────┘       │
│           │          │           │
│           ▼          ▼           │
│    CEF handles    Win32 finds    │
│    the click      next window    │
│                   below and      │
│                   dispatches     │
│                   there          │
└──────────────────────────────────┘
```

The alpha-based approach is elegant because the CSS/HTML itself defines the
interactive areas. If a widget has a semi-transparent background panel, it catches
clicks. If an area is fully transparent (the gaps between widgets), clicks fall
through automatically. No manual region management needed.

---

## 8. Multi-Monitor Support

```python
class MonitorManager:
    """
    Handles per-monitor layer instances.
    Each monitor can have its own set of layers or share them.
    """

    def __init__(self):
        self.monitors = self._enumerate_monitors()

    def _enumerate_monitors(self) -> list[MonitorInfo]:
        """Use EnumDisplayMonitors via C++ to get all monitors."""
        # Returns: position, size, DPI, primary flag, name
        pass

    def create_layers_for_monitor(self, monitor: MonitorInfo,
                                  layer_configs: list[dict]):
        """
        Create a set of layer instances positioned on a specific monitor.

        Options per shell.json config:
        - "monitors": "all"       → duplicate layers on every monitor
        - "monitors": "primary"   → only primary monitor
        - "monitors": [0, 2]      → specific monitor indices
        - Per-layer overrides possible
        """
        for config in layer_configs:
            # Offset the layer window position to the target monitor
            layer = self.layer_manager.create_layer(
                config,
                offset_x=monitor.x,
                offset_y=monitor.y,
                width=monitor.width,
                height=monitor.height
            )

    def on_monitor_change(self):
        """Handle monitor connect/disconnect/resolution change."""
        # WM_DISPLAYCHANGE notification from Win32
        # Re-enumerate monitors and recreate/reposition layers
        pass
```

---

## 9. Fallback and Safety

Since we're replacing the visual shell, we need safety mechanisms:

```python
class ShellSafety:
    """
    Ensures the user can always recover if something goes wrong.
    """

    # 1. Panic hotkey: Ctrl+Alt+Shift+Escape
    #    Kills PytoniumShell and restores the default Windows shell.
    #    Registered as a low-level keyboard hook that can't be blocked.

    # 2. Watchdog: Separate lightweight process that monitors the main
    #    shell process. If it crashes, the watchdog restarts it or
    #    falls back to the default shell.

    # 3. Graceful degradation: If a single layer crashes, only that
    #    layer is restarted. Other layers continue working.

    # 4. Config validation: shell.json is validated before loading.
    #    If invalid, fall back to a minimal default configuration.

    # 5. System tray fallback: Even in full desktop mode, a hidden
    #    system tray icon is registered in the real Windows tray.
    #    Right-click provides: Restart, Reload Config, Disable, Quit.

    # 6. First-run: On first launch, don't hide the Windows taskbar.
    #    Show PytoniumShell alongside the normal desktop so users can
    #    evaluate it safely before committing.
```

---

## 10. Theme System

Themes are JSON files that get injected as CSS custom properties into every layer:

```json
{
  "name": "Tokyo Night",
  "variant": "dark",

  "colors": {
    "bg-primary": "rgba(26, 27, 38, 0.92)",
    "bg-secondary": "rgba(36, 40, 59, 0.88)",
    "bg-tertiary": "rgba(52, 59, 88, 0.85)",
    "fg-primary": "#a9b1d6",
    "fg-secondary": "#565f89",
    "fg-muted": "#3b4261",
    "accent": "#7aa2f7",
    "accent2": "#bb9af7",
    "success": "#9ece6a",
    "warning": "#e0af68",
    "error": "#f7768e",
    "info": "#0db9d7",
    "border": "rgba(255, 255, 255, 0.08)"
  },

  "blur": {
    "enabled": true,
    "radius": "12px"
  },

  "typography": {
    "font-family": "'JetBrains Mono', 'Consolas', monospace",
    "font-family-display": "'Inter', 'Segoe UI', sans-serif",
    "font-size-base": "13px",
    "font-size-small": "11px",
    "font-size-large": "16px",
    "font-size-xl": "24px"
  },

  "spacing": {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px"
  },

  "radius": {
    "sm": "6px",
    "md": "12px",
    "lg": "16px",
    "full": "9999px"
  },

  "shadows": {
    "sm": "0 2px 4px rgba(0, 0, 0, 0.2)",
    "md": "0 4px 12px rgba(0, 0, 0, 0.3)",
    "lg": "0 8px 24px rgba(0, 0, 0, 0.4)"
  },

  "animations": {
    "duration-fast": "150ms",
    "duration-normal": "250ms",
    "duration-slow": "400ms",
    "easing": "cubic-bezier(0.4, 0, 0.2, 1)"
  }
}
```

Widgets use `var(--shell-accent)` etc. and automatically adapt to any theme.

---

## 11. Implementation Roadmap

### Phase 1 — Foundation (DONE ✓)
- [x] Multi-instance Pytonium support
- [x] OSR transparency
- [x] Frameless windows
- [x] Basic widget loading (clock, system monitor)
- [x] Fullscreen mode
- [x] Dashboard mode

### Phase 2 — Layer System
- [ ] Layer configuration format (shell.json)
- [ ] Layer manager with ordered Pytonium instances
- [ ] Z-ordering via C++ (HWND_BOTTOM for lower layers)
- [ ] Basic input passthrough (WM_NCHITTEST / HTTRANSPARENT)
- [ ] Alpha-based or region-based hit-testing

### Phase 3 — OS Integration (C++)
- [ ] Window monitor (RegisterShellHookWindow)
- [ ] Window info extraction (title, icon, geometry, state)
- [ ] Window control actions (minimize, maximize, close, focus)
- [ ] Basic tray icon reading
- [ ] Desktop file enumeration and launching

### Phase 4 — Desktop Replacement
- [ ] Taskbar layer with window list
- [ ] Desktop icons layer mirroring real desktop
- [ ] App launcher overlay (search + launch)
- [ ] DWM thumbnail previews for window hover
- [ ] System tray rendering

### Phase 5 — Polish and Safety
- [ ] Notification interception and custom rendering
- [ ] Audio mixer integration (per-app volume)
- [ ] Virtual desktop switching
- [ ] Multi-monitor support
- [ ] Panic hotkey and watchdog process
- [ ] Theme system with hot-swapping
- [ ] Clipboard manager widget

### Phase 6 — Ecosystem
- [ ] Widget/layer marketplace or community repo
- [ ] Plugin API for third-party OS integrations
- [ ] Linux support (separate OS integration layer for X11/Wayland)
- [ ] Configuration GUI (settings layer)
- [ ] Documentation and widget authoring guide

---

## 12. Key Design Decisions

**Fullscreen as desktop, not window manipulation**
The core architectural insight. By owning the entire screen, we avoid all
OS-specific shell integration quirks. The OS manages real windows normally;
we just provide the visual backdrop and tools around them.

**C++ for OS, Python for glue, HTML/CSS/JS for visuals**
Clean separation. Dirty Win32 tricks happen in C++ where they're natural.
Python provides the comfortable scripting layer. Web tech provides the
infinitely flexible visual layer. Each does what it's best at.

**Alpha-based hit-testing over region lists**
Let the CSS define interactive areas implicitly. If a pixel is opaque,
it catches clicks. If transparent, clicks pass through. No manual
region management, no synchronization between JS layout and C++ hit areas.

**State system as the universal data bus**
Pytonium's existing namespace-based state system is the perfect
event bus between C++ OS events → Python services → JS rendering layers.
No need to invent a new IPC mechanism.

**Safety first**
Panic hotkey, watchdog process, graceful degradation per-layer, first-run
alongside the normal desktop. Users should never feel trapped.

**Layers as independent instances**
Each layer is its own Pytonium/CEF instance. If one crashes, others survive.
Each can be reloaded independently. This costs more memory than a single
instance with CSS z-index layers, but gains isolation and robustness.
