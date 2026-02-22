"""ShellManager - the main entry point for PytoniumShell."""

import json
import os
import time

from .widget_manager import WidgetManager
from .system_services import SystemServices
from .theme import Theme
from .hotkey_listener import HotkeyListener
from .position_store import PositionStore
from .system_tray import SystemTray


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
    - Manages system services, theming, hotkeys, tray icon, and position persistence
    """

    def __init__(self, widgets_dir, config_path=None, theme_name="default"):
        self.config = load_config(config_path)
        self.widgets_dir = widgets_dir
        self.widget_manager = WidgetManager(self)
        self.system_services = SystemServices(self)
        self.theme = Theme(theme_name)
        self.running = True

        # Position persistence: store next to the widgets directory
        store_path = os.path.join(
            os.path.dirname(os.path.abspath(widgets_dir)),
            "widget_positions.json",
        )
        self.position_store = PositionStore(store_path)

        # Hotkey listener (multi-hotkey)
        self.hotkey_listener = HotkeyListener()

        # Register hotkeys from config
        dashboard_hotkey = self.config.get("dashboard_hotkey", "ctrl+alt+d")
        self.hotkey_listener.register("dashboard_toggle", dashboard_hotkey)

        quit_hotkey = self.config.get("quit_hotkey")
        if quit_hotkey:
            self.hotkey_listener.register("quit", quit_hotkey)

        reload_hotkey = self.config.get("reload_hotkey")
        if reload_hotkey:
            self.hotkey_listener.register("reload_all", reload_hotkey)

        # System tray
        self.system_tray = SystemTray(self)

    def run(self):
        """Load all widgets and enter the main loop."""
        print("PytoniumShell: Starting...")
        self.widget_manager.load_all(self.widgets_dir)
        self.system_services.start()

        # Register per-widget hotkeys from manifests
        for w in self.widget_manager.active_widgets:
            widget_hotkey = w.manifest.get("hotkey")
            if widget_hotkey:
                self.hotkey_listener.register(
                    f"widget_toggle:{w.name}", widget_hotkey
                )

        # Start hotkey listener
        self.hotkey_listener.start()

        # Print registered hotkeys
        for name, hk_str in self.hotkey_listener.registered_hotkeys.items():
            label = hk_str.upper().replace("+", " + ")
            print(f"  Hotkey: {label} -> {name}")

        # Start system tray
        self.system_tray.start()

        n_widgets = len(self.widget_manager.active_widgets)
        n_dashboard = len(self.widget_manager.dashboard_widgets)
        print(f"PytoniumShell: {n_widgets} widget(s) loaded ({n_dashboard} dashboard).")
        print("PytoniumShell: Running. Close all widgets or press Ctrl+C to exit.")

        try:
            while self.running and self.widget_manager.any_running():
                # Process hotkeys
                for name in self.hotkey_listener.poll_triggered():
                    self._handle_hotkey(name)

                # Process tray actions
                for action_name, args in self.system_tray.poll_actions():
                    self._handle_tray_action(action_name, args)

                self.widget_manager.update()
                self.system_services.poll()
                self.position_store.poll_save()
                time.sleep(0.016)  # ~60 fps
        except KeyboardInterrupt:
            print("\nPytoniumShell: Interrupted.")

        self.shutdown()

    def _handle_hotkey(self, name):
        """Dispatch a triggered hotkey by name."""
        if name == "dashboard_toggle":
            self.widget_manager.toggle_dashboard()
        elif name == "quit":
            self.running = False
        elif name == "reload_all":
            self._reload_all_widgets()
        elif name.startswith("widget_toggle:"):
            widget_name = name[len("widget_toggle:"):]
            self.widget_manager.toggle_widget(widget_name)

    def _handle_tray_action(self, action_name, args):
        """Dispatch a tray menu action."""
        if action_name == "toggle_widget":
            self.widget_manager.toggle_widget(args[0])
        elif action_name == "toggle_dashboard":
            self.widget_manager.toggle_dashboard()
        elif action_name == "reload_all":
            self._reload_all_widgets()
        elif action_name == "quit":
            self.running = False

    def _reload_all_widgets(self):
        """Reload all widget web views."""
        print("PytoniumShell: Reloading all widgets...")
        for w in self.widget_manager.active_widgets:
            if w.pytonium.is_running():
                try:
                    w.pytonium.execute_javascript("location.reload()")
                except Exception:
                    pass

    def shutdown(self):
        """Shut down all widgets and services."""
        print("PytoniumShell: Shutting down...")

        # Collect and save widget positions
        self.position_store.collect_positions(self.widget_manager.active_widgets)
        self.position_store.save()

        self.system_tray.stop()
        self.hotkey_listener.stop()
        self.system_services.stop()
        self.widget_manager.shutdown_all()
        print("PytoniumShell: Done.")
