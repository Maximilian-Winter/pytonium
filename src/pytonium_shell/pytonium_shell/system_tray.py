"""System tray icon for PytoniumShell.

Provides a right-click menu with widget toggles, dashboard control,
reload, and quit options. Uses pystray + Pillow (optional dependencies).
"""

import threading

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False


def _create_default_icon(size=64):
    """Create a simple default tray icon (blue circle with purple center)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Outer circle (accent blue)
    draw.ellipse([4, 4, size - 4, size - 4], fill=(122, 162, 247, 255))
    # Inner circle (accent purple)
    inner = size // 4
    draw.ellipse([inner, inner, size - inner, size - inner], fill=(187, 154, 247, 255))
    return img


class SystemTray:
    """System tray icon with widget management menu.

    Runs pystray on a background thread. Menu callbacks are dispatched
    back to the main thread via an action queue to avoid cross-thread
    Pytonium calls.
    """

    def __init__(self, shell_manager):
        self.shell = shell_manager
        self._icon = None
        self._thread = None
        self._actions = []
        self._lock = threading.Lock()

    def start(self):
        """Create and show the tray icon."""
        if not HAS_PYSTRAY:
            print("PytoniumShell: pystray not installed — tray icon disabled. "
                  "Install with: pip install pystray Pillow")
            return

        self._thread = threading.Thread(
            target=self._run, daemon=True, name="SystemTray"
        )
        self._thread.start()

    def stop(self):
        """Remove the tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=2.0)

    def poll_actions(self):
        """Return and clear pending tray menu actions.

        Called from the main loop. Returns a list of (action_name, args) tuples.
        """
        with self._lock:
            actions = list(self._actions)
            self._actions.clear()
        return actions

    def _queue_action(self, action_name, *args):
        """Queue an action for the main thread to process."""
        with self._lock:
            self._actions.append((action_name, args))

    def _build_menu(self):
        """Build the tray right-click menu."""
        items = []

        # Widget visibility toggles
        widgets = self.shell.widget_manager.active_widgets
        if widgets:
            for w in widgets:
                name = w.name
                mode = w.mode
                # Show mode as suffix for clarity
                label = f"{name} [{mode}]"
                items.append(
                    pystray.MenuItem(
                        label,
                        lambda icon, item, n=name: self._queue_action(
                            "toggle_widget", n
                        ),
                        checked=lambda item, n=name: self._is_widget_visible(n),
                    )
                )
            items.append(pystray.Menu.SEPARATOR)

        # Dashboard toggle
        if self.shell.widget_manager.dashboard_widgets:
            items.append(
                pystray.MenuItem(
                    "Toggle Dashboard",
                    lambda icon, item: self._queue_action("toggle_dashboard"),
                )
            )
            items.append(pystray.Menu.SEPARATOR)

        # Reload all
        items.append(
            pystray.MenuItem(
                "Reload All",
                lambda icon, item: self._queue_action("reload_all"),
            )
        )

        # Quit
        items.append(
            pystray.MenuItem(
                "Quit PytoniumShell",
                lambda icon, item: self._queue_action("quit"),
            )
        )

        return pystray.Menu(*items)

    def _is_widget_visible(self, widget_name):
        """Check if a widget is currently visible (for menu checkmarks)."""
        if not self.shell.running:
            return False
        try:
            for w in self.shell.widget_manager.active_widgets:
                if w.name == widget_name:
                    return w.visible
        except (RuntimeError, IndexError):
            pass  # list modified during iteration (shutdown)
        return False

    def _run(self):
        """Background thread: create icon and run pystray event loop."""
        icon_image = _create_default_icon()

        self._icon = pystray.Icon(
            "pytonium-shell",
            icon_image,
            "PytoniumShell",
            menu=self._build_menu(),
        )
        self._icon.run()
