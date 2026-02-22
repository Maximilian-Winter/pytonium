"""Global hotkey listener using Win32 RegisterHotKey API."""

import ctypes
import ctypes.wintypes
import threading

# Win32 constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

WM_HOTKEY = 0x0312

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
    """Listens for a global hotkey and signals via a threading.Event.

    Uses Win32 RegisterHotKey on a background thread with its own message loop.
    The main thread checks `triggered` to see if the hotkey was pressed.
    """

    HOTKEY_ID = 1

    def __init__(self, hotkey="ctrl+alt+d"):
        self._modifiers, self._vk_code = _parse_hotkey(hotkey)
        self._thread = None
        self._stop_event = threading.Event()
        self.triggered = threading.Event()
        self._hotkey_str = hotkey

    def start(self):
        """Start listening for the hotkey on a background thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="HotkeyListener"
        )
        self._thread.start()

    def stop(self):
        """Stop the hotkey listener."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            # Post WM_QUIT to break the message loop
            thread_id = self._thread.ident
            if thread_id:
                ctypes.windll.user32.PostThreadMessageW(
                    thread_id, 0x0012, 0, 0  # WM_QUIT
                )
            self._thread.join(timeout=2.0)
        self._thread = None

    def check_and_clear(self):
        """Check if the hotkey was triggered and clear the event. Returns True if triggered."""
        if self.triggered.is_set():
            self.triggered.clear()
            return True
        return False

    def _run(self):
        """Background thread: register hotkey, pump messages, unregister on exit."""
        user32 = ctypes.windll.user32

        if not user32.RegisterHotKey(None, self.HOTKEY_ID, self._modifiers, self._vk_code):
            print(f"HotkeyListener: Failed to register hotkey '{self._hotkey_str}' "
                  f"(error {ctypes.GetLastError()}). It may be in use by another application.")
            return

        msg = ctypes.wintypes.MSG()
        try:
            while not self._stop_event.is_set():
                # PeekMessage with PM_REMOVE — non-blocking
                if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                    if msg.message == WM_HOTKEY and msg.wParam == self.HOTKEY_ID:
                        self.triggered.set()
                    elif msg.message == 0x0012:  # WM_QUIT
                        break
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                else:
                    # Sleep briefly to avoid busy-waiting
                    self._stop_event.wait(0.05)
        finally:
            user32.UnregisterHotKey(None, self.HOTKEY_ID)
