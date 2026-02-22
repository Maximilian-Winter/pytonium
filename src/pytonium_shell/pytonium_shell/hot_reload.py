"""Hot reload - watches widget directories for changes and triggers reload."""

import threading
import time

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False


class _WidgetFileHandler(FileSystemEventHandler):
    """Handles file change events for a single widget."""

    def __init__(self, widget_instance):
        super().__init__()
        self.widget = widget_instance
        self._debounce_timer = None
        self._lock = threading.Lock()

    def on_modified(self, event):
        if event.is_directory:
            return

        path = event.src_path.lower()
        if path.endswith((".html", ".css", ".js")):
            self._debounced_reload()
        elif path.endswith(".py"):
            self._debounced_reload()

    def _debounced_reload(self):
        """Reload after 200ms of no changes (debounce)."""
        with self._lock:
            if self._debounce_timer:
                self._debounce_timer.cancel()
            self._debounce_timer = threading.Timer(0.2, self._do_reload)
            self._debounce_timer.start()

    def _do_reload(self):
        """Execute the reload."""
        try:
            if self.widget.pytonium.is_running():
                self.widget.pytonium.execute_javascript("location.reload()")
        except Exception:
            pass


def start_watching(widget_path, widget_instance):
    """Start a file watcher for a widget directory.

    Returns the Observer instance (call .stop() + .join() to clean up),
    or None if watchdog is not installed.
    """
    if not HAS_WATCHDOG:
        return None

    handler = _WidgetFileHandler(widget_instance)
    observer = Observer()
    observer.schedule(handler, widget_path, recursive=True)
    observer.daemon = True
    observer.start()
    return observer
