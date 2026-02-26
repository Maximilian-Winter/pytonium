"""DesktopMirror with shell-specific polling integration.

The core OS introspection lives in ``Pytonium.desktop_mirror``.
This module extends it with a ``poll()`` method that integrates into
the shell's main loop to push window state to layers.
"""

import json
import time
from typing import List

from Pytonium.desktop_mirror import (  # noqa: F401
    DesktopMirror as _CoreDesktopMirror,
    WindowInfo,
    DesktopItem,
    AppInfo,
)


class DesktopMirror(_CoreDesktopMirror):
    """Extended DesktopMirror with shell-specific polling.

    Adds a ``poll()`` method that periodically enumerates windows and
    pushes the results into a LayerManager's state namespace.
    """

    def __init__(self, poll_interval: float = 0.5):
        super().__init__()
        self.poll_interval = poll_interval
        self._last_poll = 0.0
        self._last_windows: List[dict] = []
        self._debug_first_poll = True

    # -- Polling ---------------------------------------------------------------

    def poll(self, layer_manager):
        """Called from the main loop — push window list to layers if interval elapsed."""
        now = time.time()
        if now - self._last_poll < self.poll_interval:
            return

        self._last_poll = now
        windows = self.enumerate_windows()
        window_dicts = [w.to_dict() for w in windows]

        if self._debug_first_poll:
            self._debug_first_poll = False
            print(f"DesktopMirror: First poll found {len(windows)} windows, "
                  f"excluding {len(self._excluded_hwnds)} shell HWNDs")
            for w in windows[:5]:
                print(f"  Window: hwnd={w.hwnd} title={w.title!r} exe={w.exe!r}")
            if len(windows) > 5:
                print(f"  ... and {len(windows) - 5} more")

        # Only push if the window list actually changed
        if window_dicts != self._last_windows:
            self._last_windows = window_dicts
            layer_manager.push_state("windows", "list", window_dicts)

            # Push the count separately for simple display
            layer_manager.push_state("windows", "count", len(window_dicts))
