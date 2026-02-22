"""Global hotkey listener using Win32 RegisterHotKey API.

Supports multiple named hotkeys registered before start().
The main thread polls for triggered hotkey names via poll_triggered().
"""

import ctypes
import ctypes.wintypes
import queue
import threading

# Win32 constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

WM_HOTKEY = 0x0312

# PostThreadMessageW — used to send WM_QUIT to the hotkey thread
_user32 = ctypes.windll.user32
_user32.PostThreadMessageW.argtypes = [
    ctypes.wintypes.DWORD,
    ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
]
_user32.PostThreadMessageW.restype = ctypes.wintypes.BOOL

# Virtual key codes for common keys
_VK_MAP = {
    "a": 0x41, "b": 0x42, "c": 0x43, "d": 0x44, "e": 0x45,
    "f": 0x46, "g": 0x47, "h": 0x48, "i": 0x49, "j": 0x4A,
    "k": 0x4B, "l": 0x4C, "m": 0x4D, "n": 0x4E, "o": 0x4F,
    "p": 0x50, "q": 0x51, "r": 0x52, "s": 0x53, "t": 0x54,
    "u": 0x55, "v": 0x56, "w": 0x57, "x": 0x58, "y": 0x59,
    "z": 0x5A,
    "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
    "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    "space": 0x20, "tab": 0x09, "escape": 0x1B, "esc": 0x1B,
}

_MOD_MAP = {
    "ctrl": MOD_CONTROL,
    "control": MOD_CONTROL,
    "alt": MOD_ALT,
    "shift": MOD_SHIFT,
    "win": MOD_WIN,
    "super": MOD_WIN,
}


def _parse_hotkey(hotkey_str):
    """Parse a hotkey string like 'ctrl+alt+d' into (modifiers, vk_code)."""
    parts = [p.strip().lower() for p in hotkey_str.split("+")]
    modifiers = MOD_NOREPEAT  # prevent repeated WM_HOTKEY while held
    vk_code = 0

    for part in parts:
        if part in _MOD_MAP:
            modifiers |= _MOD_MAP[part]
        elif part in _VK_MAP:
            vk_code = _VK_MAP[part]
        else:
            raise ValueError(f"Unknown hotkey component: '{part}'")

    if vk_code == 0:
        raise ValueError(f"No key specified in hotkey: '{hotkey_str}'")

    return modifiers, vk_code


class HotkeyListener:
    """Listens for multiple global hotkeys on a background thread.

    Each hotkey has a unique name (e.g., "dashboard_toggle", "widget_toggle:clock").
    The main thread polls for triggered hotkey names.

    Usage:
        listener = HotkeyListener()
        listener.register("dashboard_toggle", "ctrl+alt+d")
        listener.register("widget_toggle:clock", "ctrl+alt+c")
        listener.start()

        # In main loop:
        for name in listener.poll_triggered():
            handle(name)

        listener.stop()
    """

    def __init__(self):
        self._hotkeys = {}  # id -> {"name": str, "modifiers": int, "vk": int, "str": str}
        self._next_id = 1
        self._thread = None
        self._stop_event = threading.Event()
        self._triggered = queue.Queue()
        self._started = False

    def register(self, name, hotkey_str):
        """Register a hotkey. Must be called before start().

        Args:
            name: Unique name for this hotkey.
            hotkey_str: Key combination (e.g., "ctrl+alt+d").

        Returns:
            The hotkey ID.

        Raises:
            ValueError: If hotkey_str is invalid.
            RuntimeError: If called after start().
        """
        if self._started:
            raise RuntimeError("Cannot register hotkeys after start()")

        modifiers, vk_code = _parse_hotkey(hotkey_str)
        hotkey_id = self._next_id
        self._next_id += 1
        self._hotkeys[hotkey_id] = {
            "name": name,
            "modifiers": modifiers,
            "vk": vk_code,
            "str": hotkey_str,
        }
        return hotkey_id

    @property
    def registered_hotkeys(self):
        """Return a dict of name -> hotkey_str for all registered hotkeys."""
        return {info["name"]: info["str"] for info in self._hotkeys.values()}

    def start(self):
        """Start listening for all registered hotkeys."""
        if not self._hotkeys:
            return
        self._started = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="HotkeyListener"
        )
        self._thread.start()

    def stop(self):
        """Stop the hotkey listener and unregister all hotkeys."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            thread_id = self._thread.ident
            if thread_id:
                _user32.PostThreadMessageW(
                    thread_id, 0x0012, 0, 0  # WM_QUIT
                )
            self._thread.join(timeout=2.0)
        self._thread = None
        self._started = False

    def poll_triggered(self):
        """Return a list of hotkey names triggered since last poll.

        Non-blocking. Returns an empty list if none triggered.
        """
        triggered = []
        while True:
            try:
                triggered.append(self._triggered.get_nowait())
            except queue.Empty:
                break
        return triggered

    def check_and_clear(self):
        """Check if any hotkey was triggered. Returns the name, or None.

        Backward-compatible convenience method.
        """
        triggered = self.poll_triggered()
        return triggered[0] if triggered else None

    def _run(self):
        """Background thread: register all hotkeys, pump messages, unregister on exit."""
        user32 = ctypes.windll.user32
        registered_ids = []

        for hk_id, info in self._hotkeys.items():
            if user32.RegisterHotKey(None, hk_id, info["modifiers"], info["vk"]):
                registered_ids.append(hk_id)
            else:
                print(
                    f"HotkeyListener: Failed to register '{info['name']}' "
                    f"({info['str']}) — error {ctypes.GetLastError()}. "
                    f"It may be in use by another application."
                )

        msg = ctypes.wintypes.MSG()
        try:
            while not self._stop_event.is_set():
                # PeekMessage with PM_REMOVE — non-blocking
                if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                    if msg.message == WM_HOTKEY and msg.wParam in self._hotkeys:
                        name = self._hotkeys[msg.wParam]["name"]
                        self._triggered.put(name)
                    elif msg.message == 0x0012:  # WM_QUIT
                        break
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                else:
                    # Sleep briefly to avoid busy-waiting
                    self._stop_event.wait(0.05)
        finally:
            for hk_id in registered_ids:
                user32.UnregisterHotKey(None, hk_id)
