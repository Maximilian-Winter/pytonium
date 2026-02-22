"""WidgetManager - discovers, loads, and manages widget instances."""

import importlib.util
import json
import os

from Pytonium import Pytonium

from .widget_instance import WidgetInstance
from .win32_window_helper import Win32WindowHelper
from .hot_reload import start_watching


class WidgetManager:
    """Manages the lifecycle of all widget instances."""

    def __init__(self, shell):
        self.shell = shell
        self.active_widgets = []

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
                    print(f"  Loaded widget: {entry}")
                except Exception as e:
                    print(f"  Failed to load widget '{entry}': {e}")

    def _load_widget(self, name, widget_path, manifest_path):
        """Load a single widget from its directory."""
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        window_config = manifest.get("window", {})
        entry_file = manifest.get("entry", "index.html")
        backend_file = manifest.get("backend", None)

        # Create Pytonium instance
        p = Pytonium()

        # Enable OSR for transparent backgrounds
        if window_config.get("transparent_background", False):
            p.set_osr_mode(True)

        # All shell widgets are frameless
        p.set_frameless_window(True)

        # Register custom scheme to serve widget files
        p.add_custom_scheme("widget", widget_path)

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

        # Get dimensions
        width = window_config.get("width", 300)
        height = window_config.get("height", 200)

        # Initialize the browser
        p.initialize(f"widget://{entry_file}", width, height)

        # Apply Win32 window flags after initialization
        hwnd = p.get_native_window_handle()
        if hwnd:
            if window_config.get("always_on_top", False):
                Win32WindowHelper.make_always_on_top(hwnd)

            if not window_config.get("show_in_taskbar", True):
                Win32WindowHelper.hide_from_taskbar(hwnd)

            if window_config.get("click_through", False):
                Win32WindowHelper.make_click_through(hwnd)

            # Position the window
            position = window_config.get("position", None)
            if position:
                Win32WindowHelper.set_position(
                    hwnd,
                    position.get("x", 0),
                    position.get("y", 0),
                    width,
                    height,
                )

        # Inject theme
        self.shell.theme.inject(p)

        # Set up hot reload if enabled
        widget_inst = WidgetInstance(name, p, manifest, backend_module)
        if manifest.get("hot_reload", False):
            widget_inst.watcher = start_watching(widget_path, widget_inst)

        return widget_inst

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

    def update(self):
        """Pump the message loop. Only one instance needs to call this."""
        if self.active_widgets:
            self.active_widgets[0].pytonium.update_message_loop()

    def any_running(self):
        """Check if any widget is still running."""
        return any(w.pytonium.is_running() for w in self.active_widgets)

    def shutdown_all(self):
        """Close and shut down all widgets."""
        # Stop file watchers
        for w in self.active_widgets:
            if w.watcher:
                w.watcher.stop()
                w.watcher.join()

        # Shutdown Pytonium instances
        for w in self.active_widgets:
            if w.pytonium.is_running():
                w.pytonium.close_browser()

        # Shut down CEF via the first instance
        if self.active_widgets:
            self.active_widgets[0].pytonium.shutdown()

        self.active_widgets.clear()
