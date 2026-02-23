"""Taskbar layer backend — provides window control and app launching."""

import os
import socket
from Pytonium import returns_value_to_javascript


class LayerBackend:
    """Exposed to JavaScript as Pytonium.layer.*

    The _layer_manager attribute is injected by LayerManager after construction,
    enabling inter-layer communication (e.g. toggling the overlay launcher).
    """

    @returns_value_to_javascript("string")
    def get_hostname(self):
        """Get the system hostname."""
        return socket.gethostname()

    @returns_value_to_javascript("string")
    def get_username(self):
        """Get the current username."""
        return os.environ.get("USERNAME", os.environ.get("USER", "user"))

    def focus_window(self, hwnd):
        """Bring a window to the foreground."""
        import ctypes
        user32 = ctypes.windll.user32
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)

    def minimize_window(self, hwnd):
        """Minimize a window."""
        import ctypes
        ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE

    def close_window(self, hwnd):
        """Close a window."""
        import ctypes
        ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE

    def launch_app(self, path):
        """Launch an application."""
        os.startfile(path)

    def toggle_launcher(self):
        """Toggle the app launcher overlay."""
        if hasattr(self, "_layer_manager"):
            self._layer_manager.toggle_overlay("launcher")
