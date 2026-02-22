"""ShellManager - the main entry point for PytoniumShell."""

import json
import os
import time

from .widget_manager import WidgetManager
from .system_services import SystemServices
from .theme import Theme
from .hotkey_listener import HotkeyListener


def load_config(config_path):
    """Load shell configuration from a JSON file, or return defaults."""
    if config_path and os.path.isfile(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {}


class ShellManager:
    """Manages the lifecycle of the entire PytoniumShell.

    - Discovers and loads widgets
    - Runs the main update loop
    - Manages system services and theming
    """

    def __init__(self, widgets_dir, config_path=None, theme_name="default"):
        self.config = load_config(config_path)
        self.widgets_dir = widgets_dir
        self.widget_manager = WidgetManager(self)
        self.system_services = SystemServices(self)
        self.theme = Theme(theme_name)
        hotkey = self.config.get("dashboard_hotkey", "ctrl+alt+d")
        self.hotkey_listener = HotkeyListener(hotkey)
        self.running = True

    def run(self):
        """Load all widgets and enter the main loop."""
        print("PytoniumShell: Starting...")
        self.widget_manager.load_all(self.widgets_dir)
        self.system_services.start()

        # Start hotkey listener if there are dashboard widgets
        if self.widget_manager.dashboard_widgets:
            self.hotkey_listener.start()
            hotkey_str = self.config.get("dashboard_hotkey", "ctrl+alt+d").upper().replace("+", " + ")
            print(f"PytoniumShell: Dashboard hotkey: {hotkey_str}")

        n_widgets = len(self.widget_manager.active_widgets)
        n_dashboard = len(self.widget_manager.dashboard_widgets)
        print(f"PytoniumShell: {n_widgets} widget(s) loaded ({n_dashboard} dashboard).")
        print("PytoniumShell: Running. Close all widgets or press Ctrl+C to exit.")

        try:
            while self.running and self.widget_manager.any_running():
                # Check for dashboard toggle hotkey
                if self.hotkey_listener.check_and_clear():
                    self.widget_manager.toggle_dashboard()

                self.widget_manager.update()
                self.system_services.poll()
                time.sleep(0.016)  # ~60 fps
        except KeyboardInterrupt:
            print("\nPytoniumShell: Interrupted.")

        self.shutdown()

    def shutdown(self):
        """Shut down all widgets and services."""
        print("PytoniumShell: Shutting down...")
        self.hotkey_listener.stop()
        self.system_services.stop()
        self.widget_manager.shutdown_all()
        print("PytoniumShell: Done.")
