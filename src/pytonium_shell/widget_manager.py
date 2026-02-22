"""WidgetManager - discovers, loads, and manages widget instances."""

import importlib.util
import json
import os
import time

from Pytonium import Pytonium

from .widget_instance import WidgetInstance
from .win32_window_helper import Win32WindowHelper, MonitorInfo
from .hot_reload import start_watching


class WidgetManager:
    """Manages the lifecycle of all widget instances."""

    def __init__(self, shell):
        self.shell = shell
        self.active_widgets = []
        self.dashboard_widgets = []
        self._dashboard_visible = False
        self._pending_hide_time = None
        self._wallpaper_check_counter = 0

    # -- Widget discovery & loading --------------------------------------------

    def load_all(self, widgets_dir):
        """Discover and load all widgets from the given directory."""
        if not os.path.isdir(widgets_dir):
            print(f"WidgetManager: Directory not found: {widgets_dir}")
            return

        for entry in sorted(os.listdir(widgets_dir)):
            widget_path = os.path.join(widgets_dir, entry)
            manifest_path = os.path.join(widget_path, "widget.json")
            if os.path.isdir(widget_path) and os.path.isfile(manifest_path):
                try:
                    widget = self._load_widget(entry, widget_path, manifest_path)
                    self.active_widgets.append(widget)
                    print(f"  Loaded widget: {entry} (mode: {widget.mode})")
                except Exception as e:
                    print(f"  Failed to load widget '{entry}': {e}")

    def _load_widget(self, name, widget_path, manifest_path):
        """Load a single widget from its directory."""
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        window_config = manifest.get("window", {})
        entry_file = manifest.get("entry", "index.html")
        backend_file = manifest.get("backend", None)
        mode = window_config.get("mode", "widget")

        # Create Pytonium instance
        p = Pytonium()

        # Enable OSR for transparent backgrounds
        if window_config.get("transparent_background", False):
            p.set_osr_mode(True)

        # All shell widgets are frameless
        p.set_frameless_window(True)

        # Load and bind backend module if specified
        backend_module = None
        if backend_file:
            backend_path = os.path.join(widget_path, backend_file)
            if os.path.isfile(backend_path):
                backend_module = self._load_backend(backend_path, name)
                if backend_module and hasattr(backend_module, "WidgetBackend"):
                    backend_obj = backend_module.WidgetBackend()
                    p.bind_object_methods_to_javascript(
                        backend_obj, javascript_object="widget"
                    )

        # Build file:/// URL for the entry point
        entry_path = os.path.abspath(os.path.join(widget_path, entry_file))
        entry_url = "file:///" + entry_path.replace("\\", "/")

        # Create the widget instance (before mode setup, so we can attach metadata)
        widget_inst = WidgetInstance(name, p, manifest, backend_module)

        # Dispatch to mode-specific setup
        if mode == "widget":
            self._setup_widget_mode(widget_inst, window_config, entry_url)
        elif mode == "dashboard":
            self._setup_dashboard_mode(widget_inst, window_config, entry_url)
        elif mode == "bar":
            self._setup_bar_mode(widget_inst, window_config, entry_url)
        elif mode == "wallpaper":
            self._setup_wallpaper_mode(widget_inst, window_config, entry_url)
        else:
            raise ValueError(f"Unknown widget mode: '{mode}'")

        # Inject theme
        self.shell.theme.inject(p)

        # Set up hot reload if enabled
        if manifest.get("hot_reload", False):
            widget_inst.watcher = start_watching(widget_path, widget_inst)

        return widget_inst

    # -- Mode-specific setup methods -------------------------------------------

    def _setup_widget_mode(self, widget, window_config, entry_url):
        """Set up a floating widget window."""
        p = widget.pytonium
        width = window_config.get("width", 300)
        height = window_config.get("height", 200)

        p.initialize(entry_url, width, height)

        hwnd = p.get_native_window_handle()
        if hwnd:
            if window_config.get("always_on_top", False):
                Win32WindowHelper.make_always_on_top(hwnd)

            if not window_config.get("show_in_taskbar", True):
                Win32WindowHelper.hide_from_taskbar(hwnd)

            if window_config.get("click_through", False):
                Win32WindowHelper.make_click_through(hwnd)

            # Apply position from manifest
            position = window_config.get("position", None)
            if position:
                Win32WindowHelper.set_position(
                    hwnd,
                    position.get("x", 0),
                    position.get("y", 0),
                    width,
                    height,
                )

            # Override with saved position if available
            if hasattr(self.shell, "position_store") and self.shell.position_store:
                saved = self.shell.position_store.get_position(widget.name)
                if saved:
                    Win32WindowHelper.set_position(
                        hwnd,
                        saved["x"], saved["y"],
                        saved["width"], saved["height"],
                    )

    def _setup_dashboard_mode(self, widget, window_config, entry_url):
        """Set up a full-screen dashboard overlay (hidden by default)."""
        p = widget.pytonium
        monitor = self._resolve_monitor(window_config.get("monitor", "primary"))
        width = monitor.width
        height = monitor.height

        p.initialize(entry_url, width, height)

        hwnd = p.get_native_window_handle()
        if hwnd:
            Win32WindowHelper.make_always_on_top(hwnd)
            Win32WindowHelper.hide_from_taskbar(hwnd)
            Win32WindowHelper.set_position(hwnd, monitor.x, monitor.y, width, height)
            Win32WindowHelper.hide_window(hwnd)

        widget.visible = False
        self.dashboard_widgets.append(widget)

    def _setup_bar_mode(self, widget, window_config, entry_url):
        """Set up a bar docked to a screen edge using SHAppBarMessage."""
        p = widget.pytonium
        anchor = window_config.get("anchor", "top")
        bar_size = window_config.get("height", 36)
        reserve_space = window_config.get("reserve_space", True)
        monitor = self._resolve_monitor(window_config.get("monitor", "primary"))

        # Calculate dimensions based on anchor edge
        if anchor in ("top", "bottom"):
            width = monitor.width
            height = bar_size
        else:  # left, right
            width = bar_size
            height = monitor.height

        p.initialize(entry_url, width, height)

        hwnd = p.get_native_window_handle()
        if hwnd:
            Win32WindowHelper.make_always_on_top(hwnd)
            Win32WindowHelper.hide_from_taskbar(hwnd)

            if reserve_space:
                # Register as AppBar to reserve screen space
                abd = Win32WindowHelper.register_appbar(hwnd, anchor, bar_size, monitor)
                if abd:
                    widget.appbar_data = abd
                else:
                    # Fallback: just position without reserving space
                    self._position_bar_fallback(hwnd, anchor, bar_size, monitor)
            else:
                self._position_bar_fallback(hwnd, anchor, bar_size, monitor)

    def _setup_wallpaper_mode(self, widget, window_config, entry_url):
        """Set up a wallpaper widget behind desktop icons."""
        p = widget.pytonium
        monitor = self._resolve_monitor(window_config.get("monitor", "primary"))
        width = monitor.width
        height = monitor.height

        p.initialize(entry_url, width, height)

        hwnd = p.get_native_window_handle()
        if hwnd:
            Win32WindowHelper.hide_from_taskbar(hwnd)

            success = Win32WindowHelper.make_wallpaper(hwnd, monitor)
            if success:
                widget.is_wallpaper = True
            else:
                print(f"  Warning: wallpaper mode failed for '{widget.name}', "
                      f"falling back to visible widget mode")
                # Don't apply click-through on fallback — window would be a ghost
                return

            # Wallpaper widgets are click-through by default
            if window_config.get("click_through", True):
                Win32WindowHelper.make_click_through(hwnd)

    # -- Helpers ---------------------------------------------------------------

    @staticmethod
    def _position_bar_fallback(hwnd, anchor, bar_size, monitor):
        """Position a bar window without AppBar space reservation."""
        if anchor == "top":
            Win32WindowHelper.set_position(
                hwnd, monitor.x, monitor.y, monitor.width, bar_size)
        elif anchor == "bottom":
            Win32WindowHelper.set_position(
                hwnd, monitor.x, monitor.y + monitor.height - bar_size,
                monitor.width, bar_size)
        elif anchor == "left":
            Win32WindowHelper.set_position(
                hwnd, monitor.x, monitor.y, bar_size, monitor.height)
        elif anchor == "right":
            Win32WindowHelper.set_position(
                hwnd, monitor.x + monitor.width - bar_size, monitor.y,
                bar_size, monitor.height)

    def _resolve_monitor(self, spec):
        """Resolve a monitor spec to a MonitorInfo.

        Args:
            spec: "primary", an integer index, or None.

        Returns:
            MonitorInfo for the requested monitor.
        """
        monitors = Win32WindowHelper.enumerate_monitors()
        if not monitors:
            # Fallback: synthesize from GetSystemMetrics
            w, h = Win32WindowHelper.get_primary_monitor_size()
            return MonitorInfo(0, 0, 0, 0, w, h, 0, 0, w, h, True)

        if spec == "primary" or spec is None:
            for m in monitors:
                if m.is_primary:
                    return m
            return monitors[0]

        if isinstance(spec, int):
            if 0 <= spec < len(monitors):
                return monitors[spec]
            return monitors[0]

        return monitors[0]  # fallback

    def _load_backend(self, backend_path, widget_name):
        """Dynamically import a widget's backend.py module."""
        spec = importlib.util.spec_from_file_location(
            f"pytonium_shell_widget_{widget_name}_backend", backend_path
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        return None

    # -- Dashboard toggle ------------------------------------------------------

    def toggle_dashboard(self):
        """Toggle visibility of all dashboard-mode widgets."""
        if self._dashboard_visible:
            self.hide_dashboard()
        else:
            self.show_dashboard()

    def show_dashboard(self):
        """Show all dashboard widgets with a fade-in animation."""
        self._dashboard_visible = True
        for w in self.dashboard_widgets:
            hwnd = w.pytonium.get_native_window_handle()
            if hwnd:
                # Show the window first, then trigger CSS fade-in
                Win32WindowHelper.show_window(hwnd)
                w.pytonium.execute_javascript(
                    "document.body.classList.remove('fade-out');"
                    "document.body.classList.add('fade-in');"
                )
            w.visible = True

    def hide_dashboard(self):
        """Hide all dashboard widgets with a fade-out animation."""
        self._dashboard_visible = False
        for w in self.dashboard_widgets:
            hwnd = w.pytonium.get_native_window_handle()
            if hwnd:
                # Trigger CSS fade-out, then hide the window after transition
                w.pytonium.execute_javascript(
                    "document.body.classList.remove('fade-in');"
                    "document.body.classList.add('fade-out');"
                )
        # Schedule actual window hide after animation (300ms)
        self._pending_hide_time = time.time() + 0.3

    def _check_pending_hide(self):
        """Hide dashboard windows after fade-out animation completes."""
        if self._pending_hide_time and time.time() >= self._pending_hide_time:
            self._pending_hide_time = None
            if not self._dashboard_visible:
                for w in self.dashboard_widgets:
                    hwnd = w.pytonium.get_native_window_handle()
                    if hwnd:
                        Win32WindowHelper.hide_window(hwnd)
                    w.visible = False

    # -- Widget toggle (for hotkeys / tray) ------------------------------------

    def toggle_widget(self, widget_name):
        """Toggle visibility of a specific widget by name."""
        for w in self.active_widgets:
            if w.name == widget_name:
                hwnd = w.pytonium.get_native_window_handle()
                if hwnd:
                    if w.visible:
                        Win32WindowHelper.hide_window(hwnd)
                        w.visible = False
                    else:
                        Win32WindowHelper.show_window(hwnd)
                        w.visible = True
                break

    # -- Wallpaper health check ------------------------------------------------

    def _check_wallpaper_health(self):
        """Re-parent wallpaper widgets if explorer.exe restarted.

        Called periodically (every ~5 seconds) from update().
        """
        for w in self.active_widgets:
            if w.is_wallpaper:
                hwnd = w.pytonium.get_native_window_handle()
                if hwnd and not Win32WindowHelper.is_wallpaper_parent_valid(hwnd):
                    monitor_spec = w.manifest.get("window", {}).get("monitor", "primary")
                    monitor = self._resolve_monitor(monitor_spec)
                    Win32WindowHelper.make_wallpaper(hwnd, monitor)

    # -- Update loop -----------------------------------------------------------

    def update(self):
        """Pump the message loop. Only one instance needs to call this."""
        self._check_pending_hide()

        # Wallpaper health check every ~5 seconds (300 frames at 60fps)
        self._wallpaper_check_counter += 1
        if self._wallpaper_check_counter >= 300:
            self._wallpaper_check_counter = 0
            self._check_wallpaper_health()

        if self.active_widgets:
            self.active_widgets[0].pytonium.update_message_loop()

    def any_running(self):
        """Check if any widget is still running."""
        return any(w.pytonium.is_running() for w in self.active_widgets)

    # -- Shutdown --------------------------------------------------------------

    def shutdown_all(self):
        """Close and shut down all widgets."""
        # Stop file watchers
        for w in self.active_widgets:
            if w.watcher:
                w.watcher.stop()
                w.watcher.join()

        # Unregister appbars
        for w in self.active_widgets:
            if w.appbar_data is not None:
                Win32WindowHelper.unregister_appbar(w.appbar_data)
                w.appbar_data = None

        # Restore wallpaper windows
        for w in self.active_widgets:
            if w.is_wallpaper:
                hwnd = w.pytonium.get_native_window_handle()
                if hwnd:
                    Win32WindowHelper.restore_from_wallpaper(hwnd)

        # Shutdown Pytonium instances
        for w in self.active_widgets:
            if w.pytonium.is_running():
                w.pytonium.close_browser()

        # Shut down CEF via the first instance
        if self.active_widgets:
            self.active_widgets[0].pytonium.shutdown()

        self.active_widgets.clear()
