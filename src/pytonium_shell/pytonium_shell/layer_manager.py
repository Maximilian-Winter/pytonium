"""LayerManager — creates and manages Pytonium instances for each desktop layer.

Handles z-ordering, input routing, layer lifecycle, and state distribution.
Analogous to WidgetManager but for the desktop compositor mode.
"""

import importlib.util
import json
import os
import time

from Pytonium import Pytonium

from .layer_instance import LayerInstance, LayerType, InputMode
from .win32_window_helper import Win32WindowHelper, MonitorInfo


class LayerManager:
    """Manages the lifecycle of all layers in a desktop shell."""

    def __init__(self, shell):
        self.shell = shell
        self.layers: dict[str, LayerInstance] = {}
        self._ordered_layers: list[LayerInstance] = []
        self._pending_hide: dict[str, float] = {}  # layer_id -> hide_time

    # -- Shell loading ---------------------------------------------------------

    def load_shell(self, shell_dir: str):
        """Load shell.json and create all layers.

        Args:
            shell_dir: Path to the shell directory containing shell.json.
        """
        shell_json = os.path.join(shell_dir, "shell.json")
        if not os.path.isfile(shell_json):
            raise FileNotFoundError(f"shell.json not found in {shell_dir}")

        with open(shell_json, "r", encoding="utf-8") as f:
            config = json.load(f)

        layer_configs = config.get("layers", [])
        if not layer_configs:
            print("LayerManager: No layers defined in shell.json")
            return

        # Sort by z_order (lowest first = loaded first)
        layer_configs.sort(key=lambda c: c.get("z_order", 0))

        for lc in layer_configs:
            try:
                layer = self._load_layer(lc, shell_dir)
                self.layers[layer.id] = layer
                self._ordered_layers.append(layer)
                print(f"  Loaded layer: {layer.id} (type: {layer.type.value}, "
                      f"z: {layer.z_order})")
            except Exception as e:
                print(f"  Failed to load layer '{lc.get('id', '?')}': {e}")

    def _load_layer(self, config: dict, shell_dir: str) -> LayerInstance:
        """Load and initialize a single layer."""
        layer_id = config["id"]
        layer_type = LayerType(config["type"])
        z_order = config.get("z_order", 0)
        layer_config = config.get("config", {})

        # Merge top-level keys into layer_config for convenience
        for key in ("input", "state_namespaces", "hotkey", "position",
                     "height", "width", "monitor"):
            if key in config:
                layer_config[key] = config[key]

        layer = LayerInstance(layer_id, layer_type, z_order, layer_config)

        # Create Pytonium instance
        p = Pytonium()
        p.set_frameless_window(True)
        layer.pytonium = p

        # Load optional backend
        backend_file = config.get("backend")
        if backend_file:
            backend_path = os.path.join(shell_dir, backend_file)
            if os.path.isfile(backend_path):
                layer.backend = self._load_backend(backend_path, layer_id)
                if layer.backend and hasattr(layer.backend, "LayerBackend"):
                    layer.backend_obj = layer.backend.LayerBackend()
                elif layer.backend and hasattr(layer.backend, "WidgetBackend"):
                    # Fallback: also accept WidgetBackend for compatibility
                    layer.backend_obj = layer.backend.WidgetBackend()

                if layer.backend_obj:
                    # Inject layer_manager reference so backends can
                    # communicate with other layers (e.g. toggle overlay)
                    layer.backend_obj._layer_manager = self
                    p.bind_object_methods_to_javascript(
                        layer.backend_obj, javascript_object="layer"
                    )

        # Build entry URL
        entry_file = config.get("entry", "index.html")
        entry_path = os.path.abspath(os.path.join(shell_dir, entry_file))
        entry_url = "file:///" + entry_path.replace("\\", "/")

        # Resolve monitor
        monitor_spec = layer_config.get("monitor", "primary")
        monitor = self._resolve_monitor(monitor_spec)

        # Dispatch to type-specific setup
        if layer_type == LayerType.WALLPAPER:
            self._setup_wallpaper_layer(layer, entry_url, monitor)
        elif layer_type in (LayerType.DESKTOP, LayerType.WIDGET_HOST):
            self._setup_desktop_layer(layer, entry_url, monitor)
        elif layer_type == LayerType.TASKBAR:
            self._setup_taskbar_layer(layer, entry_url, monitor)
        elif layer_type == LayerType.OVERLAY:
            self._setup_overlay_layer(layer, entry_url, monitor)

        # Inject theme
        if hasattr(self.shell, "theme"):
            self.shell.theme.inject(p)

        # Subscribe to state namespaces via SystemServices (if available)
        namespaces = config.get("state_namespaces", [])
        if namespaces and hasattr(self.shell, "system_services"):
            # SystemServices pushes to widgets that have state handlers
            # For layers, we just need the pytonium instance to receive states
            pass  # State is pushed via push_state() from the main loop

        return layer

    # -- Type-specific setup ---------------------------------------------------

    def _setup_wallpaper_layer(self, layer: LayerInstance, entry_url: str,
                                monitor: MonitorInfo):
        """Fullscreen, always at bottom, always click-through."""
        p = layer.pytonium
        p.initialize(entry_url, monitor.width, monitor.height)
        p.set_fullscreen(True)

        hwnd = p.get_native_window_handle()
        if hwnd:
            Win32WindowHelper.set_layer_bottom(hwnd)
            Win32WindowHelper.make_click_through(hwnd)
            Win32WindowHelper.hide_from_taskbar(hwnd)
            # Position on correct monitor
            p.set_window_position(monitor.x, monitor.y)

    def _setup_desktop_layer(self, layer: LayerInstance, entry_url: str,
                              monitor: MonitorInfo):
        """Fullscreen, at bottom (above wallpaper), click-through by default.

        Used for desktop icons and widget host layers.
        """
        p = layer.pytonium
        p.initialize(entry_url, monitor.width, monitor.height)
        p.set_fullscreen(True)

        hwnd = p.get_native_window_handle()
        if hwnd:
            Win32WindowHelper.set_layer_bottom(hwnd)
            Win32WindowHelper.hide_from_taskbar(hwnd)
            p.set_window_position(monitor.x, monitor.y)

            # Desktop/widget layers are click-through by default
            # (Phase 3 will add WM_NCHITTEST for per-element hit testing)
            if layer.input_mode == InputMode.CLICK_THROUGH_ALWAYS:
                Win32WindowHelper.make_click_through(hwnd)

    def _setup_taskbar_layer(self, layer: LayerInstance, entry_url: str,
                              monitor: MonitorInfo):
        """Partial bar, always on top, reserves screen space via AppBar."""
        p = layer.pytonium
        config = layer.config
        position = config.get("position", "bottom")
        bar_size = config.get("height", 40)
        reserve = config.get("reserve_space", True)

        # Calculate dimensions based on anchor edge
        if position in ("top", "bottom"):
            width = monitor.width
            height = bar_size
        else:
            width = bar_size
            height = monitor.height

        p.initialize(entry_url, width, height)

        hwnd = p.get_native_window_handle()
        if hwnd:
            Win32WindowHelper.make_always_on_top(hwnd)
            Win32WindowHelper.hide_from_taskbar(hwnd)

            if reserve:
                abd = Win32WindowHelper.register_appbar(
                    hwnd, position, bar_size, monitor
                )
                if abd:
                    layer.appbar_data = abd
                else:
                    self._position_bar_fallback(hwnd, position, bar_size, monitor)
            else:
                self._position_bar_fallback(hwnd, position, bar_size, monitor)

    def _setup_overlay_layer(self, layer: LayerInstance, entry_url: str,
                              monitor: MonitorInfo):
        """Fullscreen, hidden by default, TOPMOST when shown."""
        p = layer.pytonium
        p.initialize(entry_url, monitor.width, monitor.height)
        p.set_fullscreen(True)

        hwnd = p.get_native_window_handle()
        if hwnd:
            Win32WindowHelper.hide_from_taskbar(hwnd)
            Win32WindowHelper.hide_window(hwnd)
            p.set_window_position(monitor.x, monitor.y)

        layer.visible = False

    # -- Overlay toggling ------------------------------------------------------

    def toggle_overlay(self, layer_id: str):
        """Show/hide an overlay layer with fade animation."""
        layer = self.layers.get(layer_id)
        if not layer or layer.type != LayerType.OVERLAY:
            return

        if layer.visible:
            self._hide_overlay(layer)
        else:
            self._show_overlay(layer)

    def _show_overlay(self, layer: LayerInstance):
        """Show overlay: make TOPMOST, show window, trigger CSS fade-in."""
        hwnd = layer.pytonium.get_native_window_handle()
        if hwnd:
            Win32WindowHelper.set_layer_topmost(hwnd)
            Win32WindowHelper.show_window(hwnd)
            layer.pytonium.execute_javascript(
                "document.body.classList.remove('fade-out');"
                "document.body.classList.add('fade-in');"
            )
        layer.visible = True

    def _hide_overlay(self, layer: LayerInstance):
        """Start overlay hide: trigger CSS fade-out, schedule actual hide."""
        hwnd = layer.pytonium.get_native_window_handle()
        if hwnd:
            layer.pytonium.execute_javascript(
                "document.body.classList.remove('fade-in');"
                "document.body.classList.add('fade-out');"
            )
        # Schedule actual hide after animation (300ms)
        self._pending_hide[layer.id] = time.time() + 0.3
        layer.visible = False

    def _check_pending_hides(self):
        """Complete overlay hides after fade-out animation."""
        now = time.time()
        completed = []
        for layer_id, hide_time in self._pending_hide.items():
            if now >= hide_time:
                layer = self.layers.get(layer_id)
                if layer and not layer.visible:
                    hwnd = layer.pytonium.get_native_window_handle()
                    if hwnd:
                        Win32WindowHelper.hide_window(hwnd)
                        Win32WindowHelper.remove_layer_topmost(hwnd)
                completed.append(layer_id)
        for lid in completed:
            del self._pending_hide[lid]

    # -- State distribution ----------------------------------------------------

    def push_state(self, namespace: str, key: str, value):
        """Push state to all layers that subscribe to this namespace.

        Uses execute_javascript to dispatch CustomEvents directly, bypassing
        the CEF IPC set_state path which has issues with complex/large data.
        """
        try:
            json_value = json.dumps(value)
        except (TypeError, ValueError):
            json_value = json.dumps(str(value))

        js = (
            f"window.dispatchEvent(new CustomEvent('shell-state', "
            f"{{detail: {{namespace: '{namespace}', key: '{key}', "
            f"value: {json_value}}}}}));"
        )

        for layer in self._ordered_layers:
            if not layer.pytonium or not layer.pytonium.is_running():
                continue
            subscribed = layer.config.get("state_namespaces", [])
            # Push to all layers if no namespace filter, or if subscribed
            if not subscribed or namespace in subscribed:
                try:
                    layer.pytonium.execute_javascript(js)
                except Exception:
                    pass

    # -- Helpers ---------------------------------------------------------------

    @staticmethod
    def _position_bar_fallback(hwnd, position, bar_size, monitor):
        """Position a bar without AppBar reservation (fallback)."""
        if position == "top":
            Win32WindowHelper.set_position(
                hwnd, monitor.x, monitor.y, monitor.width, bar_size)
        elif position == "bottom":
            Win32WindowHelper.set_position(
                hwnd, monitor.x, monitor.y + monitor.height - bar_size,
                monitor.width, bar_size)
        elif position == "left":
            Win32WindowHelper.set_position(
                hwnd, monitor.x, monitor.y, bar_size, monitor.height)
        elif position == "right":
            Win32WindowHelper.set_position(
                hwnd, monitor.x + monitor.width - bar_size, monitor.y,
                bar_size, monitor.height)

    def _resolve_monitor(self, spec):
        """Resolve a monitor spec to a MonitorInfo."""
        monitors = Win32WindowHelper.enumerate_monitors()
        if not monitors:
            w, h = Win32WindowHelper.get_primary_monitor_size()
            return MonitorInfo(0, 0, 0, 0, w, h, 0, 0, w, h, True, "")

        if spec == "primary" or spec is None:
            for m in monitors:
                if m.is_primary:
                    return m
            return monitors[0]

        if isinstance(spec, int) and 0 <= spec < len(monitors):
            return monitors[spec]

        return monitors[0]

    @staticmethod
    def _load_backend(backend_path: str, layer_id: str):
        """Dynamically import a layer's backend module."""
        spec = importlib.util.spec_from_file_location(
            f"pytonium_shell_layer_{layer_id}_backend", backend_path
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        return None

    # -- Update loop -----------------------------------------------------------

    def update(self):
        """Pump the CEF message loop and check pending animations."""
        self._check_pending_hides()

        # Only one instance needs to pump the shared CEF message loop.
        # Find the first layer that's still running (don't assume index 0).
        for layer in self._ordered_layers:
            if layer.pytonium and layer.pytonium.is_running():
                layer.pytonium.update_message_loop()
                break

    def any_running(self) -> bool:
        """Check if any layer is still running."""
        return any(
            l.pytonium and l.pytonium.is_running()
            for l in self._ordered_layers
        )

    # -- Shutdown --------------------------------------------------------------

    def shutdown_all(self):
        """Close and shut down all layers."""
        # Unregister AppBars first
        for layer in self._ordered_layers:
            if layer.appbar_data is not None:
                try:
                    Win32WindowHelper.unregister_appbar(layer.appbar_data)
                except Exception:
                    pass
                layer.appbar_data = None

        # Close all browsers
        for layer in self._ordered_layers:
            if layer.pytonium and layer.pytonium.is_running():
                try:
                    layer.pytonium.close_browser()
                except Exception:
                    pass

        # Pump the CEF message loop a few times so close messages are processed.
        # Without this, CEF may crash during shutdown.
        pump_layer = None
        for layer in self._ordered_layers:
            if layer.pytonium:
                pump_layer = layer
                break
        if pump_layer:
            for _ in range(30):
                try:
                    pump_layer.pytonium.update_message_loop()
                except Exception:
                    break
                time.sleep(0.016)

        # Shut down CEF via the first available instance
        for layer in self._ordered_layers:
            if layer.pytonium:
                try:
                    layer.pytonium.shutdown()
                except Exception:
                    pass
                break

        self.layers.clear()
        self._ordered_layers.clear()
