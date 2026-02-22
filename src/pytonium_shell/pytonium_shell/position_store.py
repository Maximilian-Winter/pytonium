"""Position persistence for widget windows.

Saves and restores widget positions to/from a JSON file so widgets
reappear at the same location across shell restarts.
"""

import json
import os
import time


class PositionStore:
    """Saves and restores widget window positions."""

    def __init__(self, store_path):
        """
        Args:
            store_path: Path to the JSON file for storing positions.
        """
        self.store_path = store_path
        self._positions = {}  # widget_name -> {"x", "y", "width", "height"}
        self._last_save_time = 0.0
        self._dirty = False
        self.save_interval = 30.0  # seconds between auto-saves
        self._load()

    def _load(self):
        """Load saved positions from disk."""
        if os.path.isfile(self.store_path):
            try:
                with open(self.store_path, "r") as f:
                    self._positions = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._positions = {}

    def save(self):
        """Save current positions to disk."""
        directory = os.path.dirname(self.store_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        try:
            with open(self.store_path, "w") as f:
                json.dump(self._positions, f, indent=2)
            self._dirty = False
            self._last_save_time = time.time()
        except IOError as e:
            print(f"PositionStore: Failed to save: {e}")

    def get_position(self, widget_name):
        """Get saved position for a widget.

        Returns:
            dict with x, y, width, height keys, or None if not saved.
        """
        return self._positions.get(widget_name)

    def update_position(self, widget_name, x, y, width, height):
        """Update the stored position for a widget."""
        self._positions[widget_name] = {
            "x": x, "y": y, "width": width, "height": height,
        }
        self._dirty = True

    def poll_save(self):
        """Called periodically. Saves to disk if dirty and interval has elapsed."""
        if self._dirty and (time.time() - self._last_save_time) >= self.save_interval:
            self.save()

    def collect_positions(self, widgets):
        """Collect current positions from all widget-mode windows.

        Args:
            widgets: list of WidgetInstance objects.
        """
        for w in widgets:
            if w.mode == "widget" and w.pytonium.is_running():
                try:
                    x, y = w.pytonium.get_window_position()
                    width, height = w.pytonium.get_window_size()
                    self.update_position(w.name, x, y, width, height)
                except Exception:
                    pass  # window may have closed
