"""DesktopShellManager — main orchestrator for desktop compositor mode.

Parallel to ShellManager (widget mode). Manages layers instead of widgets,
and integrates the DesktopMirror for OS introspection.

Usage:
    pytonium-shell --shell ./my_desktop
"""

import json
import os
import time

from .layer_instance import LayerType
from .layer_manager import LayerManager
from .desktop_mirror import DesktopMirror
from .system_services import SystemServices
from .theme import Theme
from .hotkey_listener import HotkeyListener
from .system_tray import SystemTray


def _load_shell_config(shell_dir: str) -> dict:
    """Load shell.json from a shell directory."""
    shell_json = os.path.join(shell_dir, "shell.json")
    if os.path.isfile(shell_json):
        with open(shell_json, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


class DesktopShellManager:
    """Manages the lifecycle of a desktop shell (layer-based mode).

    Instead of loading individual widgets from a directory, loads a shell.json
    that defines ordered layers (wallpaper, widgets, taskbar, overlays), each
    rendered by its own fullscreen Pytonium instance.
    """

    def __init__(self, shell_dir: str, config_path=None, theme_name="default"):
        self.shell_dir = os.path.abspath(shell_dir)
        self.shell_config = _load_shell_config(self.shell_dir)
        self.running = True

        # Theme — from shell.json or CLI override
        effective_theme = theme_name
        shell_meta = self.shell_config.get("shell", {})
        if shell_meta.get("theme") and theme_name == "default":
            effective_theme = shell_meta["theme"]
        self.theme = Theme(effective_theme)

        # Core managers
        self.layer_manager = LayerManager(self)
        self.desktop_mirror = DesktopMirror(
            poll_interval=self.shell_config.get("desktop_mirror", {}).get(
                "poll_interval", 0.5
            )
        )
        self.system_services = SystemServices(self)

        # Hotkeys
        self.hotkey_listener = HotkeyListener()

        # Register global hotkeys from shell config
        panic_hotkey = self.shell_config.get("panic_hotkey", "ctrl+alt+shift+escape")
        self.hotkey_listener.register("panic_quit", panic_hotkey)

        quit_hotkey = self.shell_config.get("quit_hotkey")
        if quit_hotkey:
            self.hotkey_listener.register("quit", quit_hotkey)

        reload_hotkey = self.shell_config.get("reload_hotkey")
        if reload_hotkey:
            self.hotkey_listener.register("reload_all", reload_hotkey)

        # System tray fallback (always present for safety)
        self.system_tray = SystemTray(self)

        # Expose the widget_manager attribute so SystemServices can find widgets
        # (it pushes state to shell.widget_manager.active_widgets)
        # For desktop mode, we redirect this to layer_manager
        self.widget_manager = _LayerManagerAdapter(self.layer_manager)

    def run(self):
        """Load all layers and enter the main loop."""
        shell_name = self.shell_config.get("shell", {}).get("name", "Desktop Shell")
        print(f"PytoniumShell Desktop: Starting '{shell_name}'...")

        # Load layers
        self.layer_manager.load_shell(self.shell_dir)

        # Collect HWNDs of our own layer windows so DesktopMirror skips them
        shell_hwnds = []
        for layer in self.layer_manager._ordered_layers:
            if layer.pytonium:
                hwnd = layer.pytonium.get_native_window_handle()
                if hwnd:
                    shell_hwnds.append(hwnd)
        self.desktop_mirror.set_excluded_hwnds(shell_hwnds)

        # Start system services (CPU, memory, etc.)
        self.system_services.start()

        # Register per-layer hotkeys (for overlay toggles, etc.)
        for layer in self.layer_manager._ordered_layers:
            hotkey = layer.config.get("hotkey")
            if hotkey:
                self.hotkey_listener.register(
                    f"layer_toggle:{layer.id}", hotkey
                )

        # Start hotkey listener
        self.hotkey_listener.start()

        # Print registered hotkeys
        for name, hk_str in self.hotkey_listener.registered_hotkeys.items():
            label = hk_str.upper().replace("+", " + ")
            print(f"  Hotkey: {label} -> {name}")

        # Start system tray
        self.system_tray.start()

        n_layers = len(self.layer_manager._ordered_layers)
        print(f"PytoniumShell Desktop: {n_layers} layer(s) loaded.")
        for layer in self.layer_manager._ordered_layers:
            ns = layer.config.get("state_namespaces", [])
            hwnd = layer.pytonium.get_native_window_handle() if layer.pytonium else None
            print(f"  Layer '{layer.id}': hwnd={hwnd}, namespaces={ns}")
        print(f"PytoniumShell Desktop: Excluded {len(shell_hwnds)} shell HWNDs from mirror.")
        print("PytoniumShell Desktop: Running. Panic hotkey or tray icon to exit.")

        try:
            while self.running and self.layer_manager.any_running():
                # Process hotkeys
                for name in self.hotkey_listener.poll_triggered():
                    self._handle_hotkey(name)

                # Process tray actions
                for action_name, args in self.system_tray.poll_actions():
                    self._handle_tray_action(action_name, args)

                # Pump CEF message loop
                self.layer_manager.update()

                # Poll system services (pushes to layers via state system)
                self.system_services.poll()

                # Poll desktop mirror (window list, pushes to layers)
                self.desktop_mirror.poll(self.layer_manager)

                time.sleep(0.016)  # ~60 fps
        except KeyboardInterrupt:
            print("\nPytoniumShell Desktop: Interrupted.")

        self.shutdown()

    def _handle_hotkey(self, name: str):
        """Dispatch a triggered hotkey by name."""
        if name in ("panic_quit", "quit"):
            self.running = False
        elif name == "reload_all":
            self._reload_all_layers()
        elif name.startswith("layer_toggle:"):
            layer_id = name[len("layer_toggle:"):]
            self.layer_manager.toggle_overlay(layer_id)

    def _handle_tray_action(self, action_name: str, args):
        """Dispatch a tray menu action."""
        if action_name == "quit":
            self.running = False
        elif action_name == "reload_all":
            self._reload_all_layers()
        elif action_name == "toggle_dashboard":
            # In desktop mode, toggle the first overlay layer
            for layer in self.layer_manager._ordered_layers:
                if layer.type == LayerType.OVERLAY:
                    self.layer_manager.toggle_overlay(layer.id)
                    break
        elif action_name == "toggle_widget":
            # In desktop mode, treat widget toggles as layer toggles
            if args:
                self.layer_manager.toggle_overlay(args[0])

    def _reload_all_layers(self):
        """Reload all layer web views."""
        print("PytoniumShell Desktop: Reloading all layers...")
        for layer in self.layer_manager._ordered_layers:
            if layer.pytonium and layer.pytonium.is_running():
                try:
                    layer.pytonium.execute_javascript("location.reload()")
                except Exception:
                    pass

    def shutdown(self):
        """Shut down all layers and services."""
        print("PytoniumShell Desktop: Shutting down...")
        self.system_tray.stop()
        self.hotkey_listener.stop()
        self.system_services.stop()
        self.layer_manager.shutdown_all()
        print("PytoniumShell Desktop: Done.")


class _LayerManagerAdapter:
    """Adapter so SystemServices can push state using the same interface.

    SystemServices expects shell.widget_manager.active_widgets where each
    widget has a .pytonium attribute and a .manifest with state_namespaces.
    This adapter maps layers to that interface.
    """

    def __init__(self, layer_manager: LayerManager):
        self._lm = layer_manager

    @property
    def active_widgets(self):
        """Return layers wrapped as widget-like objects."""
        return [_LayerAsWidget(l) for l in self._lm._ordered_layers]

    @property
    def dashboard_widgets(self):
        return []


class _PytoniumStateProxy:
    """Wraps a Pytonium instance to use execute_javascript for state push.

    The CEF IPC-based set_state() doesn't reliably deliver complex data
    (lists of dicts) or large ints (>2^31) through CefValueWrapper.
    This proxy serializes data as JSON and dispatches a CustomEvent
    via execute_javascript, which is more reliable for desktop mode.
    """

    def __init__(self, pytonium):
        self._p = pytonium

    def set_state(self, namespace, key, value):
        """Push state via execute_javascript instead of CEF IPC."""
        if not self._p or not self._p.is_running():
            return
        try:
            json_value = json.dumps(value)
        except (TypeError, ValueError):
            json_value = json.dumps(str(value))
        # Dispatch the same 'shell-state' CustomEvent the JS already listens for
        js = (
            f"window.dispatchEvent(new CustomEvent('shell-state', "
            f"{{detail: {{namespace: '{namespace}', key: '{key}', "
            f"value: {json_value}}}}}));"
        )
        try:
            self._p.execute_javascript(js)
        except Exception:
            pass

    def is_running(self):
        return self._p.is_running() if self._p else False

    def __getattr__(self, name):
        """Delegate all other calls to the real Pytonium instance."""
        return getattr(self._p, name)


class _LayerAsWidget:
    """Wraps a LayerInstance to look like a WidgetInstance for SystemServices."""

    def __init__(self, layer):
        self._layer = layer
        # Use the state proxy so set_state goes through execute_javascript
        self.pytonium = _PytoniumStateProxy(layer.pytonium)
        self.name = layer.id
        self.manifest = {
            "state_namespaces": layer.config.get("state_namespaces", []),
        }
        self.visible = layer.visible
        self.mode = layer.type.value
