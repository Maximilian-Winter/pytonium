"""DesktopMirror — introspects the real OS desktop via Win32 APIs.

Provides structured information about running windows, desktop files,
and installed applications.  Useful for building taskbar-like UIs,
app launchers, file managers, or any Pytonium app that needs to interact
with the user's desktop environment.

This module is only functional on Windows (``os.name == "nt"``).
"""

import ctypes
import ctypes.wintypes
import os
import time
from dataclasses import dataclass, asdict
from typing import List

try:
    import psutil
except ImportError:
    psutil = None

# ---------------------------------------------------------------------------
# Win32 API declarations
# ---------------------------------------------------------------------------

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Callback type for EnumWindows
WNDENUMPROC = ctypes.WINFUNCTYPE(
    ctypes.wintypes.BOOL,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LPARAM,
)

# Window state checks
user32.IsWindowVisible.argtypes = [ctypes.wintypes.HWND]
user32.IsWindowVisible.restype = ctypes.wintypes.BOOL

user32.IsIconic.argtypes = [ctypes.wintypes.HWND]
user32.IsIconic.restype = ctypes.wintypes.BOOL

user32.IsZoomed.argtypes = [ctypes.wintypes.HWND]
user32.IsZoomed.restype = ctypes.wintypes.BOOL

user32.GetWindowTextW.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.LPWSTR, ctypes.c_int
]
user32.GetWindowTextW.restype = ctypes.c_int

user32.GetWindowTextLengthW.argtypes = [ctypes.wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int

user32.GetWindowRect.argtypes = [
    ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.RECT)
]
user32.GetWindowRect.restype = ctypes.wintypes.BOOL

user32.GetWindowThreadProcessId.argtypes = [
    ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.DWORD)
]
user32.GetWindowThreadProcessId.restype = ctypes.wintypes.DWORD

user32.GetWindowLongPtrW.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
user32.GetWindowLongPtrW.restype = ctypes.c_longlong

user32.SetForegroundWindow.argtypes = [ctypes.wintypes.HWND]
user32.SetForegroundWindow.restype = ctypes.wintypes.BOOL

user32.ShowWindow.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = ctypes.wintypes.BOOL

user32.PostMessageW.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
]
user32.PostMessageW.restype = ctypes.wintypes.BOOL

user32.GetClassNameW.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.LPWSTR, ctypes.c_int
]
user32.GetClassNameW.restype = ctypes.c_int

user32.GetWindow.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.UINT]
user32.GetWindow.restype = ctypes.wintypes.HWND

user32.EnumWindows.argtypes = [WNDENUMPROC, ctypes.wintypes.LPARAM]
user32.EnumWindows.restype = ctypes.wintypes.BOOL

# Constants
GWL_STYLE = -16
GWL_EXSTYLE = -20
WS_VISIBLE = 0x10000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
WS_EX_NOACTIVATE = 0x08000000
GW_OWNER = 4
WM_CLOSE = 0x0010
SW_MINIMIZE = 6
SW_MAXIMIZE = 3
SW_RESTORE = 9
SW_SHOW = 5

# Class names to skip (shell windows, not real apps)
_SKIP_CLASSES = frozenset({
    "Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd",
    "DV2ControlHost", "Windows.UI.Core.CoreWindow",
    "MultitaskingViewFrame", "ForegroundStaging",
    "ApplicationManager_DesktopShellWindow",
})


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class WindowInfo:
    """Information about a single visible OS window."""
    hwnd: int
    title: str
    exe: str
    pid: int
    x: int
    y: int
    width: int
    height: int
    minimized: bool
    maximized: bool
    visible: bool
    class_name: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class DesktopItem:
    """A file or folder on the user's Desktop."""
    name: str
    path: str
    is_directory: bool
    size: int = 0
    modified: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class AppInfo:
    """An installed application (from Start Menu shortcuts)."""
    name: str
    path: str
    target: str = ""

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------
# DesktopMirror
# ---------------------------------------------------------------------------

class DesktopMirror:
    """Introspects the real OS desktop via Win32 APIs.

    Provides methods to enumerate running windows, list desktop files,
    discover installed applications, and control windows (focus, minimize,
    maximize, restore, close).

    Typical usage::

        from Pytonium import DesktopMirror

        mirror = DesktopMirror()
        for win in mirror.enumerate_windows():
            print(f"{win.title} ({win.exe})")

        for item in DesktopMirror.get_desktop_items():
            print(f"  {item.name}")
    """

    def __init__(self):
        self._process_cache: dict = {}  # pid -> exe name cache
        self._cache_time = 0.0
        self._excluded_hwnds: set = set()

    def set_excluded_hwnds(self, hwnds):
        """Set HWNDs to exclude from window enumeration.

        Useful when your own Pytonium windows should not appear in
        the enumeration results.
        """
        self._excluded_hwnds = set(hwnds)

    # -- Window enumeration ----------------------------------------------------

    def enumerate_windows(self) -> List[WindowInfo]:
        """Get all taskbar-visible windows (the ones users see in Alt+Tab).

        Returns:
            A list of :class:`WindowInfo` for each visible application window.
        """
        results = []
        excluded = self._excluded_hwnds

        def _enum_callback(hwnd, _lparam):
            try:
                # Skip excluded windows
                if hwnd in excluded:
                    return True

                # Must be visible
                if not user32.IsWindowVisible(hwnd):
                    return True

                # Skip windows with no title
                title_len = user32.GetWindowTextLengthW(hwnd)
                if title_len == 0:
                    return True

                # Get class name and skip shell windows
                class_buf = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(hwnd, class_buf, 256)
                class_name = class_buf.value
                if class_name in _SKIP_CLASSES:
                    return True

                # Taskbar visibility heuristic:
                # A window appears in the taskbar if:
                # - It has no owner AND doesn't have WS_EX_TOOLWINDOW
                # - OR it has WS_EX_APPWINDOW set
                ex_style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
                owner = user32.GetWindow(hwnd, GW_OWNER)

                is_tool = bool(ex_style & WS_EX_TOOLWINDOW)
                is_app = bool(ex_style & WS_EX_APPWINDOW)
                is_noactivate = bool(ex_style & WS_EX_NOACTIVATE)

                # Skip tool windows unless they explicitly want taskbar presence
                if is_tool and not is_app:
                    return True

                # Skip owned windows unless they explicitly want taskbar presence
                if owner and not is_app:
                    return True

                # Skip NoActivate windows (overlays, popups)
                if is_noactivate and not is_app:
                    return True

                # Get title
                title_buf = ctypes.create_unicode_buffer(title_len + 1)
                user32.GetWindowTextW(hwnd, title_buf, title_len + 1)
                title = title_buf.value

                # Get geometry
                rect = ctypes.wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))

                # Get process info
                pid = ctypes.wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                pid_val = pid.value
                exe = self._get_process_name(pid_val)

                results.append(WindowInfo(
                    hwnd=hwnd,
                    title=title,
                    exe=exe,
                    pid=pid_val,
                    x=rect.left,
                    y=rect.top,
                    width=rect.right - rect.left,
                    height=rect.bottom - rect.top,
                    minimized=bool(user32.IsIconic(hwnd)),
                    maximized=bool(user32.IsZoomed(hwnd)),
                    visible=True,
                    class_name=class_name,
                ))
            except Exception:
                pass
            return True

        callback = WNDENUMPROC(_enum_callback)
        user32.EnumWindows(callback, 0)
        return results

    def _get_process_name(self, pid: int) -> str:
        """Get process executable name, with caching."""
        if psutil is None:
            return ""

        # Refresh cache every 5 seconds
        now = time.time()
        if now - self._cache_time > 5.0:
            self._process_cache.clear()
            self._cache_time = now

        if pid in self._process_cache:
            return self._process_cache[pid]

        try:
            proc = psutil.Process(pid)
            name = proc.name()
            self._process_cache[pid] = name
            return name
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return ""

    # -- Window control actions ------------------------------------------------

    @staticmethod
    def focus_window(hwnd: int):
        """Bring a window to the foreground."""
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)

    @staticmethod
    def minimize_window(hwnd: int):
        """Minimize a window."""
        user32.ShowWindow(hwnd, SW_MINIMIZE)

    @staticmethod
    def maximize_window(hwnd: int):
        """Maximize a window."""
        user32.ShowWindow(hwnd, SW_MAXIMIZE)

    @staticmethod
    def restore_window(hwnd: int):
        """Restore a window from minimized/maximized state."""
        user32.ShowWindow(hwnd, SW_RESTORE)

    @staticmethod
    def close_window(hwnd: int):
        """Send WM_CLOSE to a window."""
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

    # -- Desktop files ---------------------------------------------------------

    @staticmethod
    def get_desktop_items() -> List[DesktopItem]:
        """List files and folders on the user's Desktop."""
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        # Also check public desktop
        public_desktop = os.path.join(
            os.environ.get("PUBLIC", r"C:\Users\Public"), "Desktop"
        )

        items = []
        for base_path in (desktop_path, public_desktop):
            if not os.path.isdir(base_path):
                continue
            try:
                for entry in os.listdir(base_path):
                    full = os.path.join(base_path, entry)
                    try:
                        stat = os.stat(full)
                        items.append(DesktopItem(
                            name=entry,
                            path=full,
                            is_directory=os.path.isdir(full),
                            size=stat.st_size if not os.path.isdir(full) else 0,
                            modified=time.strftime(
                                "%Y-%m-%d %H:%M", time.localtime(stat.st_mtime)
                            ),
                        ))
                    except OSError:
                        pass
            except OSError:
                pass

        return items

    # -- Installed applications ------------------------------------------------

    @staticmethod
    def get_installed_apps() -> List[AppInfo]:
        """Scan Start Menu for application shortcuts."""
        search_dirs = [
            os.path.join(
                os.environ.get("ProgramData", r"C:\ProgramData"),
                "Microsoft", "Windows", "Start Menu", "Programs",
            ),
            os.path.join(
                os.path.expanduser("~"),
                "AppData", "Roaming", "Microsoft", "Windows",
                "Start Menu", "Programs",
            ),
        ]

        apps = []
        seen_names = set()

        for base_dir in search_dirs:
            if not os.path.isdir(base_dir):
                continue
            for root, _dirs, files in os.walk(base_dir):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = os.path.splitext(f)[0]
                        if name.lower() in seen_names:
                            continue
                        seen_names.add(name.lower())
                        full_path = os.path.join(root, f)
                        apps.append(AppInfo(
                            name=name,
                            path=full_path,
                        ))

        apps.sort(key=lambda a: a.name.lower())
        return apps

    @staticmethod
    def launch_app(path: str):
        """Launch an application by its shortcut or executable path."""
        os.startfile(path)
