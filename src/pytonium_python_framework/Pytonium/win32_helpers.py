"""Win32 window helpers for manipulating Pytonium windows.

Provides platform-level window manipulation on Windows: always-on-top,
click-through transparency, taskbar visibility, multi-monitor enumeration,
AppBar (screen-edge docking), and background-level window embedding
(behind desktop icons — useful for live wallpapers, dashboards, etc.).

All methods are static and operate on an HWND (as int).  Must be called
after ``pytonium.initialize()`` when the native window handle exists.

This module is only functional on Windows (``os.name == "nt"``).
"""

import ctypes
import ctypes.wintypes
import os
from dataclasses import dataclass

if os.name == "nt":
    user32 = ctypes.windll.user32
    shell32 = ctypes.windll.shell32

    # -- Set Per-Monitor DPI awareness BEFORE any monitor/window queries --
    # Without this, GetMonitorInfoW returns logical (scaled) coordinates
    # instead of physical pixels.  CEF also sets this during CefInitialize,
    # but we need it earlier for accurate monitor enumeration.
    try:
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 (Win10 1703+)
        user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        user32.SetProcessDpiAwarenessContext.restype = ctypes.wintypes.BOOL
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            # PROCESS_PER_MONITOR_DPI_AWARE (Win 8.1+)
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            try:
                user32.SetProcessDPIAware()
            except (AttributeError, OSError):
                pass

    HWND = ctypes.wintypes.HWND
    UINT = ctypes.wintypes.UINT
    BOOL = ctypes.wintypes.BOOL
    LONG = ctypes.wintypes.LONG
    INT = ctypes.c_int

    # -- Declare argtypes so ctypes marshals HWND / pointer-sized values
    #    correctly on 64-bit Windows (HWND is a pointer, not a 32-bit int).

    # BOOL SetWindowPos(HWND, HWND, int, int, int, int, UINT)
    user32.SetWindowPos.argtypes = [HWND, HWND, INT, INT, INT, INT, UINT]
    user32.SetWindowPos.restype = BOOL

    # LONG_PTR GetWindowLongPtrW(HWND, int) — 64-bit safe
    user32.GetWindowLongPtrW.argtypes = [HWND, INT]
    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t

    # LONG_PTR SetWindowLongPtrW(HWND, int, LONG_PTR) — 64-bit safe
    user32.SetWindowLongPtrW.argtypes = [HWND, INT, ctypes.c_ssize_t]
    user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t

    # BOOL ShowWindow(HWND, int)
    user32.ShowWindow.argtypes = [HWND, INT]
    user32.ShowWindow.restype = BOOL

    # int GetSystemMetrics(int)
    user32.GetSystemMetrics.argtypes = [INT]
    user32.GetSystemMetrics.restype = INT

    # -- Monitor enumeration ---------------------------------------------------

    class MONITORINFOEXW(ctypes.Structure):
        """Win32 MONITORINFOEXW struct for GetMonitorInfoW."""
        _fields_ = [
            ("cbSize", ctypes.wintypes.DWORD),
            ("rcMonitor", ctypes.wintypes.RECT),
            ("rcWork", ctypes.wintypes.RECT),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("szDevice", ctypes.c_wchar * 32),
        ]

    MONITORINFOF_PRIMARY = 0x00000001
    MONITOR_DEFAULTTONEAREST = 0x00000002

    MONITORENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.wintypes.BOOL,
        ctypes.wintypes.HMONITOR,
        ctypes.wintypes.HDC,
        ctypes.POINTER(ctypes.wintypes.RECT),
        ctypes.wintypes.LPARAM,
    )

    user32.EnumDisplayMonitors.argtypes = [
        ctypes.wintypes.HDC,
        ctypes.POINTER(ctypes.wintypes.RECT),
        MONITORENUMPROC,
        ctypes.wintypes.LPARAM,
    ]
    user32.EnumDisplayMonitors.restype = BOOL

    user32.GetMonitorInfoW.argtypes = [
        ctypes.wintypes.HMONITOR,
        ctypes.POINTER(MONITORINFOEXW),
    ]
    user32.GetMonitorInfoW.restype = BOOL

    user32.MonitorFromWindow.argtypes = [HWND, ctypes.wintypes.DWORD]
    user32.MonitorFromWindow.restype = ctypes.wintypes.HMONITOR

    # -- AppBar (SHAppBarMessage) ----------------------------------------------

    class APPBARDATA(ctypes.Structure):
        """Win32 APPBARDATA struct for SHAppBarMessage."""
        _fields_ = [
            ("cbSize", ctypes.wintypes.DWORD),
            ("hWnd", ctypes.wintypes.HWND),
            ("uCallbackMessage", ctypes.wintypes.UINT),
            ("uEdge", ctypes.wintypes.UINT),
            ("rc", ctypes.wintypes.RECT),
            ("lParam", ctypes.wintypes.LPARAM),
        ]

    ABM_NEW = 0x00000000
    ABM_REMOVE = 0x00000001
    ABM_QUERYPOS = 0x00000002
    ABM_SETPOS = 0x00000003

    ABE_LEFT = 0
    ABE_TOP = 1
    ABE_RIGHT = 2
    ABE_BOTTOM = 3

    _ABE_MAP = {"left": ABE_LEFT, "top": ABE_TOP, "right": ABE_RIGHT, "bottom": ABE_BOTTOM}

    WM_USER_APPBAR = 0x0400 + 100  # custom callback message

    shell32.SHAppBarMessage.argtypes = [ctypes.wintypes.DWORD, ctypes.POINTER(APPBARDATA)]
    shell32.SHAppBarMessage.restype = ctypes.c_size_t  # UINT_PTR on 64-bit

    # -- Background embedding (Progman / WorkerW) ------------------------------

    user32.FindWindowW.argtypes = [ctypes.wintypes.LPCWSTR, ctypes.wintypes.LPCWSTR]
    user32.FindWindowW.restype = HWND

    user32.FindWindowExW.argtypes = [HWND, HWND, ctypes.wintypes.LPCWSTR, ctypes.wintypes.LPCWSTR]
    user32.FindWindowExW.restype = HWND

    SMTO_NORMAL = 0x0000
    user32.SendMessageTimeoutW.argtypes = [
        HWND, UINT, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
        UINT, UINT, ctypes.POINTER(ctypes.wintypes.DWORD),
    ]
    user32.SendMessageTimeoutW.restype = ctypes.wintypes.LPARAM

    WNDENUMPROC = ctypes.WINFUNCTYPE(BOOL, HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows.argtypes = [WNDENUMPROC, ctypes.wintypes.LPARAM]
    user32.EnumWindows.restype = BOOL

    user32.SetParent.argtypes = [HWND, HWND]
    user32.SetParent.restype = HWND

    user32.GetParent.argtypes = [HWND]
    user32.GetParent.restype = HWND

    user32.IsWindow.argtypes = [HWND]
    user32.IsWindow.restype = BOOL

    user32.EnumChildWindows.argtypes = [HWND, WNDENUMPROC, ctypes.wintypes.LPARAM]
    user32.EnumChildWindows.restype = BOOL

    user32.IsWindowVisible.argtypes = [HWND]
    user32.IsWindowVisible.restype = BOOL

    # For debug/verification
    user32.GetClassNameW.argtypes = [HWND, ctypes.wintypes.LPWSTR, INT]
    user32.GetClassNameW.restype = INT

    user32.GetWindowRect.argtypes = [HWND, ctypes.POINTER(ctypes.wintypes.RECT)]
    user32.GetWindowRect.restype = BOOL

    user32.MoveWindow.argtypes = [HWND, INT, INT, INT, INT, BOOL]
    user32.MoveWindow.restype = BOOL

    # BOOL SetLayeredWindowAttributes(HWND, COLORREF, BYTE, DWORD)
    user32.SetLayeredWindowAttributes.argtypes = [
        HWND, ctypes.wintypes.COLORREF, ctypes.wintypes.BYTE, ctypes.wintypes.DWORD,
    ]
    user32.SetLayeredWindowAttributes.restype = BOOL

    # HWND GetWindow(HWND, UINT) — for z-order queries
    user32.GetWindow.argtypes = [HWND, UINT]
    user32.GetWindow.restype = HWND

# Window style constants
GWL_STYLE = -16
GWL_EXSTYLE = -20

WS_POPUP = 0x80000000
WS_CHILD = 0x40000000
WS_VISIBLE = 0x10000000
WS_CLIPCHILDREN = 0x02000000
WS_CLIPSIBLINGS = 0x04000000

WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000

# SetLayeredWindowAttributes flags
LWA_ALPHA = 0x00000002

# GetWindow constants (for z-order queries)
GW_HWNDNEXT = 2  # window below in z-order

# SetWindowPos constants
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
HWND_BOTTOM = 1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020


@dataclass
class MonitorInfo:
    """Information about a single display monitor."""
    index: int
    handle: int          # HMONITOR
    x: int               # monitor left
    y: int               # monitor top
    width: int           # full monitor width
    height: int          # full monitor height
    work_x: int          # work area left (excludes taskbar)
    work_y: int          # work area top
    work_width: int      # work area width
    work_height: int     # work area height
    is_primary: bool
    device_name: str = ""


@dataclass
class WallpaperInfo:
    """Handles discovered for background-level window embedding.

    Used to place a window behind the desktop icons — useful for live
    wallpapers, always-visible dashboards, ambient displays, etc.

    On Win11 24H2, the desktop hierarchy under Progman is::

        Progman
        ├── SHELLDLL_DefView  (desktop icons, interactive, on top)
        ├── <YOUR WINDOW>     (background surface, layered child)
        └── WorkerW           (system wallpaper image, at bottom)
    """
    progman: int       # Progman HWND — always the parent for embedded windows
    shell_view: int    # SHELLDLL_DefView HWND — z-order anchor (icons)
    worker_w: int      # WorkerW HWND — system wallpaper (pushed behind us)
    strategy: str      # "win11_24h2", "win10_toplevel", "progman_fallback"


class Win32WindowHelper:
    """Applies Windows-specific window properties to Pytonium windows.

    Must be called after ``pytonium.initialize()`` when the HWND exists.
    All methods are static and take an HWND (as int).

    Typical usage::

        from Pytonium import Pytonium, Win32WindowHelper

        p = Pytonium()
        p.initialize("https://example.com", 800, 600)
        hwnd = p.get_native_window_handle()

        Win32WindowHelper.make_always_on_top(hwnd)
        Win32WindowHelper.hide_from_taskbar(hwnd)
    """

    # -- Always-on-top ---------------------------------------------------------

    @staticmethod
    def make_always_on_top(hwnd):
        """Make the window always-on-top."""
        user32.SetWindowPos(
            hwnd, HWND_TOPMOST,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )

    @staticmethod
    def remove_always_on_top(hwnd):
        """Remove always-on-top from the window."""
        user32.SetWindowPos(
            hwnd, HWND_NOTOPMOST,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )

    # -- Taskbar visibility ----------------------------------------------------

    @staticmethod
    def hide_from_taskbar(hwnd):
        """Hide the window from the taskbar."""
        ex_style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        ex_style |= WS_EX_TOOLWINDOW
        ex_style &= ~WS_EX_APPWINDOW
        user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex_style)

    @staticmethod
    def show_on_taskbar(hwnd):
        """Show the window on the taskbar (reverse of hide_from_taskbar)."""
        ex_style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        ex_style &= ~WS_EX_TOOLWINDOW
        ex_style |= WS_EX_APPWINDOW
        user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex_style)

    # -- Click-through ---------------------------------------------------------

    @staticmethod
    def make_click_through(hwnd):
        """Make the window click-through (mouse events pass to windows below)."""
        ex_style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        ex_style |= WS_EX_TRANSPARENT | WS_EX_LAYERED
        user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex_style)

    @staticmethod
    def remove_click_through(hwnd):
        """Remove click-through from the window."""
        ex_style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        ex_style &= ~WS_EX_TRANSPARENT
        user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex_style)

    # -- Z-ordering ------------------------------------------------------------

    @staticmethod
    def set_layer_bottom(hwnd):
        """Place window at HWND_BOTTOM z-order.

        Windows at HWND_BOTTOM sit below all normal windows, so real OS
        application windows naturally float above them.  Useful for
        background-level dashboards or ambient displays.
        """
        user32.SetWindowPos(
            hwnd, HWND_BOTTOM, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )

    @staticmethod
    def set_layer_topmost(hwnd):
        """Place window at HWND_TOPMOST (above all normal windows)."""
        user32.SetWindowPos(
            hwnd, HWND_TOPMOST, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )

    @staticmethod
    def remove_layer_topmost(hwnd):
        """Remove TOPMOST flag, returning the window to normal z-order."""
        user32.SetWindowPos(
            hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )

    @staticmethod
    def set_window_z_bottom(hwnd):
        """Place window at the bottom of its sibling z-order."""
        user32.SetWindowPos(
            hwnd, HWND_BOTTOM,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )

    # -- Position / visibility -------------------------------------------------

    @staticmethod
    def set_position(hwnd, x, y, width, height):
        """Set the window position and size."""
        user32.SetWindowPos(
            hwnd, 0,
            x, y, width, height,
            SWP_NOZORDER | SWP_NOACTIVATE,
        )

    @staticmethod
    def get_window_rect(hwnd):
        """Return the window rectangle as ``(x, y, width, height)``.

        Uses physical pixel coordinates (DPI-aware).
        """
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return (rect.left, rect.top,
                rect.right - rect.left, rect.bottom - rect.top)

    @staticmethod
    def show_window(hwnd):
        """Show the window."""
        user32.ShowWindow(hwnd, 5)  # SW_SHOW

    @staticmethod
    def hide_window(hwnd):
        """Hide the window."""
        user32.ShowWindow(hwnd, 0)  # SW_HIDE

    # -- Opacity ---------------------------------------------------------------

    @staticmethod
    def set_window_opacity(hwnd, alpha):
        """Set the window opacity (0 = fully transparent, 255 = fully opaque).

        Automatically adds the ``WS_EX_LAYERED`` style if not already set.

        Args:
            hwnd: Window handle.
            alpha: Opacity value, 0–255.
        """
        ex_style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        if not (ex_style & WS_EX_LAYERED):
            ex_style |= WS_EX_LAYERED
            user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex_style)
        user32.SetLayeredWindowAttributes(hwnd, 0, alpha, LWA_ALPHA)

    # -- Monitor enumeration ---------------------------------------------------

    @staticmethod
    def get_primary_monitor_size():
        """Returns ``(width, height)`` of the primary monitor."""
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    @staticmethod
    def enumerate_monitors():
        """Enumerate all display monitors.

        Returns a list of :class:`MonitorInfo` sorted so the primary
        monitor is index 0.
        """
        handles = []

        def _enum_cb(hmonitor, hdc, lprect, lparam):
            handles.append(int(hmonitor))
            return True  # continue enumeration

        cb = MONITORENUMPROC(_enum_cb)
        user32.EnumDisplayMonitors(None, None, cb, 0)

        monitors = []
        for h in handles:
            info = MONITORINFOEXW()
            info.cbSize = ctypes.sizeof(MONITORINFOEXW)
            if user32.GetMonitorInfoW(h, ctypes.byref(info)):
                rc = info.rcMonitor
                wk = info.rcWork
                is_primary = bool(info.dwFlags & MONITORINFOF_PRIMARY)
                monitors.append(MonitorInfo(
                    index=0,  # assigned below
                    handle=h,
                    x=rc.left, y=rc.top,
                    width=rc.right - rc.left,
                    height=rc.bottom - rc.top,
                    work_x=wk.left, work_y=wk.top,
                    work_width=wk.right - wk.left,
                    work_height=wk.bottom - wk.top,
                    is_primary=is_primary,
                    device_name=info.szDevice,
                ))

        # Sort: primary first, then by x position
        monitors.sort(key=lambda m: (not m.is_primary, m.x, m.y))
        for i, m in enumerate(monitors):
            m.index = i

        return monitors

    @staticmethod
    def get_primary_monitor():
        """Return the primary :class:`MonitorInfo` (convenience)."""
        monitors = Win32WindowHelper.enumerate_monitors()
        for m in monitors:
            if m.is_primary:
                return m
        return monitors[0] if monitors else None

    @staticmethod
    def get_monitor_for_window(hwnd):
        """Return the :class:`MonitorInfo` for the monitor containing *hwnd*."""
        hmonitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
        if not hmonitor:
            return Win32WindowHelper.get_primary_monitor()

        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(MONITORINFOEXW)
        if not user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
            return Win32WindowHelper.get_primary_monitor()

        rc = info.rcMonitor
        wk = info.rcWork
        return MonitorInfo(
            index=0,
            handle=int(hmonitor),
            x=rc.left, y=rc.top,
            width=rc.right - rc.left,
            height=rc.bottom - rc.top,
            work_x=wk.left, work_y=wk.top,
            work_width=wk.right - wk.left,
            work_height=wk.bottom - wk.top,
            is_primary=bool(info.dwFlags & MONITORINFOF_PRIMARY),
            device_name=info.szDevice,
        )

    # -- AppBar (screen-edge docking) ------------------------------------------

    @staticmethod
    def register_appbar(hwnd, edge_str, size, monitor=None):
        """Register the window as a screen-edge AppBar, reserving space.

        The window is docked to a screen edge like a taskbar or dock panel.
        The OS will shift other windows' work areas to avoid overlapping.

        Args:
            hwnd: Window handle.
            edge_str: ``"top"``, ``"bottom"``, ``"left"``, or ``"right"``.
            size: Height (top/bottom) or width (left/right) in pixels.
            monitor: Optional :class:`MonitorInfo`.  Defaults to primary.

        Returns:
            APPBARDATA instance (keep reference for
            :meth:`unregister_appbar`), or ``None`` on failure.
        """
        if monitor is None:
            monitor = Win32WindowHelper.get_primary_monitor()

        edge = _ABE_MAP.get(edge_str, ABE_TOP)

        abd = APPBARDATA()
        abd.cbSize = ctypes.sizeof(APPBARDATA)
        abd.hWnd = hwnd
        abd.uCallbackMessage = WM_USER_APPBAR

        # Register with the system
        if not shell32.SHAppBarMessage(ABM_NEW, ctypes.byref(abd)):
            print("Win32WindowHelper: SHAppBarMessage ABM_NEW failed")
            return None

        # Set edge and calculate the desired rect
        abd.uEdge = edge
        if edge == ABE_TOP:
            abd.rc.left = monitor.x
            abd.rc.top = monitor.y
            abd.rc.right = monitor.x + monitor.width
            abd.rc.bottom = monitor.y + size
        elif edge == ABE_BOTTOM:
            abd.rc.left = monitor.x
            abd.rc.top = monitor.y + monitor.height - size
            abd.rc.right = monitor.x + monitor.width
            abd.rc.bottom = monitor.y + monitor.height
        elif edge == ABE_LEFT:
            abd.rc.left = monitor.x
            abd.rc.top = monitor.y
            abd.rc.right = monitor.x + size
            abd.rc.bottom = monitor.y + monitor.height
        elif edge == ABE_RIGHT:
            abd.rc.left = monitor.x + monitor.width - size
            abd.rc.top = monitor.y
            abd.rc.right = monitor.x + monitor.width
            abd.rc.bottom = monitor.y + monitor.height

        # Query the system for available position (may be adjusted by other appbars)
        shell32.SHAppBarMessage(ABM_QUERYPOS, ctypes.byref(abd))

        # Re-apply our desired size on the correct edge (system may have shifted us)
        if edge == ABE_TOP:
            abd.rc.bottom = abd.rc.top + size
        elif edge == ABE_BOTTOM:
            abd.rc.top = abd.rc.bottom - size
        elif edge == ABE_LEFT:
            abd.rc.right = abd.rc.left + size
        elif edge == ABE_RIGHT:
            abd.rc.left = abd.rc.right - size

        # Claim the space
        shell32.SHAppBarMessage(ABM_SETPOS, ctypes.byref(abd))

        # Move the window to the final position
        user32.SetWindowPos(
            hwnd, HWND_TOPMOST,
            abd.rc.left, abd.rc.top,
            abd.rc.right - abd.rc.left,
            abd.rc.bottom - abd.rc.top,
            SWP_NOACTIVATE,
        )

        return abd

    @staticmethod
    def unregister_appbar(abd):
        """Unregister an AppBar, releasing reserved screen space."""
        if abd:
            shell32.SHAppBarMessage(ABM_REMOVE, ctypes.byref(abd))

    # -- Background-level embedding (behind desktop icons) ---------------------

    @staticmethod
    def find_desktop_windows():
        """Discover the desktop window hierarchy for background embedding.

        Sends the undocumented ``0x052C`` message to Progman to ensure the
        background layer is active, then locates the key windows.

        Useful for placing a window behind the desktop icons — for live
        wallpapers, always-visible dashboards, ambient displays, etc.

        **Win11 24H2 hierarchy** (primary strategy)::

            Progman
            ├── SHELLDLL_DefView  (desktop icons, interactive)
            ├── <YOUR WINDOW>     (injected here via z-order)
            └── WorkerW           (system wallpaper image)

        **Win10 hierarchy** (fallback)::

            Top-level WorkerW siblings of Progman, one containing
            SHELLDLL_DefView.

        Returns:
            :class:`WallpaperInfo` with handles and strategy, or ``None``
            on failure.
        """
        progman = user32.FindWindowW("Progman", None)
        if not progman:
            print("  Background embed: Progman not found")
            return None

        # Send undocumented message to enable wallpaper layering
        result = ctypes.wintypes.DWORD(0)
        user32.SendMessageTimeoutW(
            progman, 0x052C, 0, 0,
            SMTO_NORMAL, 1000, ctypes.byref(result),
        )

        # --- Strategy 1 (Win11 24H2): Both as CHILDREN of Progman ---
        child_shell_view = [0]
        child_worker_w = [0]

        def _enum_progman_children(hwnd, lparam):
            class_buf = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, class_buf, 64)
            name = class_buf.value
            if name == "SHELLDLL_DefView" and not child_shell_view[0]:
                child_shell_view[0] = hwnd
            elif name == "WorkerW" and not child_worker_w[0]:
                if user32.IsWindowVisible(hwnd):
                    rect = ctypes.wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    w = rect.right - rect.left
                    h = rect.bottom - rect.top
                    if w > 100 and h > 100:
                        child_worker_w[0] = hwnd
            return True

        cb_child = WNDENUMPROC(_enum_progman_children)
        user32.EnumChildWindows(progman, cb_child, 0)

        if child_shell_view[0] and child_worker_w[0]:
            info = WallpaperInfo(
                progman=progman,
                shell_view=child_shell_view[0],
                worker_w=child_worker_w[0],
                strategy="win11_24h2",
            )
            print(f"  Background embed strategy: win11_24h2, progman={progman:#x}, "
                  f"shell_view={info.shell_view:#x}, worker_w={info.worker_w:#x}")
            return info

        if child_shell_view[0]:
            info = WallpaperInfo(
                progman=progman,
                shell_view=child_shell_view[0],
                worker_w=0,
                strategy="win11_24h2",
            )
            print(f"  Background embed strategy: win11_24h2 (no WorkerW child), "
                  f"progman={progman:#x}, shell_view={info.shell_view:#x}")
            return info

        # --- Strategy 2 (Win10): Top-level WorkerW siblings ---
        toplevel_worker_with_shell = []
        toplevel_shell_in_worker = []
        toplevel_worker_without_shell = []

        def _enum_toplevel(hwnd, lparam):
            class_buf = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, class_buf, 64)
            if class_buf.value == "WorkerW":
                shell = user32.FindWindowExW(
                    hwnd, None, "SHELLDLL_DefView", None
                )
                if shell:
                    toplevel_worker_with_shell.append(hwnd)
                    toplevel_shell_in_worker.append(shell)
                elif user32.IsWindowVisible(hwnd):
                    rect = ctypes.wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    w = rect.right - rect.left
                    h = rect.bottom - rect.top
                    if w > 100 and h > 100:
                        toplevel_worker_without_shell.append(hwnd)
            return True

        cb_top = WNDENUMPROC(_enum_toplevel)
        user32.EnumWindows(cb_top, 0)

        if toplevel_worker_with_shell and toplevel_worker_without_shell:
            info = WallpaperInfo(
                progman=progman,
                shell_view=toplevel_shell_in_worker[0],
                worker_w=toplevel_worker_without_shell[0],
                strategy="win10_toplevel",
            )
            print(f"  Background embed strategy: win10_toplevel, "
                  f"canvas={info.worker_w:#x}, "
                  f"shell_view={info.shell_view:#x}")
            return info

        # --- Strategy 3: Fallback to Progman ---
        info = WallpaperInfo(
            progman=progman,
            shell_view=0,
            worker_w=0,
            strategy="progman_fallback",
        )
        print(f"  Background embed strategy: progman_fallback, "
              f"target={progman:#x}")
        return info

    @staticmethod
    def find_wallpaper_worker_w():
        """Legacy wrapper — returns ``(parent_hwnd, strategy)`` tuple.

        Prefer :meth:`find_desktop_windows` which returns full
        :class:`WallpaperInfo`.
        """
        info = Win32WindowHelper.find_desktop_windows()
        if info is None:
            return 0, None
        if info.strategy == "win11_24h2":
            return info.progman, "progman"
        elif info.strategy == "win10_toplevel":
            return info.worker_w, "toplevel_worker"
        else:
            return info.progman, "progman"

    @staticmethod
    def setup_wallpaper_zorder(hwnd, info):
        """Apply z-order choreography for background embedding.

        After the window has been parented into the desktop hierarchy,
        this positions it between SHELLDLL_DefView (icons on top) and
        WorkerW (system wallpaper at bottom).

        Args:
            hwnd: The window handle (already parented).
            info: :class:`WallpaperInfo` from :meth:`find_desktop_windows`.
        """
        # Make window layered and fully opaque for proper compositing
        ex_style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        ex_style |= WS_EX_LAYERED | WS_EX_NOACTIVATE
        ex_style &= ~WS_EX_APPWINDOW  # no taskbar entry
        user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex_style)

        # Fully opaque — required for WS_EX_LAYERED to composite properly
        user32.SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)

        # Z-order choreography
        if info.strategy == "win11_24h2" and info.shell_view:
            # Place our window just BEHIND SHELLDLL_DefView (icons)
            user32.SetWindowPos(
                hwnd, info.shell_view,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
            )

            # Push WorkerW behind our window
            if info.worker_w:
                user32.SetWindowPos(
                    info.worker_w, hwnd,
                    0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
                )

            print(f"  Background z-order: ShellView > hwnd({hwnd:#x}) > "
                  f"WorkerW({info.worker_w:#x})")

        elif info.strategy == "win10_toplevel":
            user32.SetWindowPos(
                hwnd, 0,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE
                | SWP_FRAMECHANGED,
            )
            print(f"  Background z-order: win10 canvas mode (no z-order needed)")

        else:
            user32.SetWindowPos(
                hwnd, HWND_BOTTOM,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
            )
            print(f"  Background z-order: progman fallback (HWND_BOTTOM)")

        # Force show (SetParent can hide the window on some builds)
        user32.ShowWindow(hwnd, 5)  # SW_SHOW

    @staticmethod
    def make_wallpaper(hwnd, monitor=None):
        """Embed a window behind the desktop icons as a background surface.

        Converts the window from ``WS_POPUP`` to ``WS_CHILD``, reparents it
        into the desktop hierarchy (Progman), and applies z-order
        choreography.  Useful for live wallpapers, always-visible dashboards,
        ambient data displays, etc.

        Args:
            hwnd: The window handle.
            monitor: Optional :class:`MonitorInfo` to position on a specific
                     monitor.  Defaults to the primary monitor.

        Returns:
            :class:`WallpaperInfo` if successful, ``None`` otherwise.
        """
        info = Win32WindowHelper.find_desktop_windows()
        if info is None:
            print("Win32WindowHelper: Failed to find desktop windows")
            return None

        if monitor is None:
            monitor = Win32WindowHelper.get_primary_monitor()

        # Determine the actual parent window
        if info.strategy == "win10_toplevel":
            parent = info.worker_w  # Win10: parent to the empty WorkerW
        else:
            parent = info.progman   # Win11 24H2 / fallback: parent to Progman

        # Convert WS_POPUP → WS_CHILD before SetParent
        style = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
        original_style = style
        style = (style & ~WS_POPUP) | WS_CHILD
        user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style)
        print(f"  Background embed style: {original_style:#010x} -> {style:#010x}")

        # SetParent into the target
        prev_parent = user32.SetParent(hwnd, parent)
        print(f"  Background embed SetParent: hwnd={hwnd:#x} -> parent={parent:#x} "
              f"(prev={prev_parent:#x})")

        # Position to fill the target monitor (parent-relative coords)
        user32.SetWindowPos(
            hwnd, 0,
            monitor.x, monitor.y, monitor.width, monitor.height,
            SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED,
        )

        # Apply z-order choreography
        Win32WindowHelper.setup_wallpaper_zorder(hwnd, info)

        # Verify actual position
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        actual_w = rect.right - rect.left
        actual_h = rect.bottom - rect.top
        print(f"  Background embed target: {monitor.x},{monitor.y} "
              f"{monitor.width}x{monitor.height}")
        print(f"  Background embed actual: {rect.left},{rect.top} "
              f"{actual_w}x{actual_h}")

        # If size doesn't match (DPI mismatch), try MoveWindow as fallback
        if actual_w != monitor.width or actual_h != monitor.height:
            print(f"  Background embed size mismatch — retrying with MoveWindow")
            user32.MoveWindow(
                hwnd,
                monitor.x, monitor.y,
                monitor.width, monitor.height,
                True,
            )

        return info

    @staticmethod
    def restore_from_wallpaper(hwnd):
        """Unparent the window from the desktop (restore to normal).

        Restores ``WS_POPUP`` style (from ``WS_CHILD``) before unparenting
        so the window can exist as a standalone top-level window again.
        """
        style = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
        style = (style & ~WS_CHILD) | WS_POPUP
        user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style)

        # Remove background-specific extended styles
        ex_style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        ex_style &= ~(WS_EX_NOACTIVATE | WS_EX_LAYERED | WS_EX_TRANSPARENT)
        user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex_style)

        user32.SetParent(hwnd, None)

    @staticmethod
    def reparent_wallpaper(hwnd, info):
        """Re-parent a background-embedded window after explorer.exe restarts.

        The window is already ``WS_CHILD``, so just ``SetParent`` + z-order.

        Args:
            hwnd: The window handle.
            info: Fresh :class:`WallpaperInfo` from
                  :meth:`find_desktop_windows`.
        """
        if info.strategy == "win10_toplevel":
            parent = info.worker_w
        else:
            parent = info.progman

        user32.SetParent(hwnd, parent)
        Win32WindowHelper.setup_wallpaper_zorder(hwnd, info)

    @staticmethod
    def verify_wallpaper_zorder(hwnd, info):
        """Check and re-apply background z-order if it drifted.

        Theme changes, wallpaper transitions, or virtual-desktop switches
        can recreate WorkerW or shuffle z-order.

        Args:
            hwnd: The window handle.
            info: :class:`WallpaperInfo` with current handle references.

        Returns:
            ``True`` if z-order was correct, ``False`` if it was repaired.
        """
        if info.strategy != "win11_24h2" or not info.shell_view:
            return True  # nothing to verify for other strategies

        # Check: is our window the next sibling below SHELLDLL_DefView?
        next_after_shell = user32.GetWindow(info.shell_view, GW_HWNDNEXT)
        if next_after_shell == hwnd:
            return True  # z-order is correct

        # Z-order drifted — re-apply
        print(f"  Background z-order drifted for {hwnd:#x}, re-applying")
        Win32WindowHelper.setup_wallpaper_zorder(hwnd, info)
        return False

    @staticmethod
    def is_wallpaper_parent_valid(hwnd):
        """Check if a background-embedded window's parent is still alive."""
        parent = user32.GetParent(hwnd)
        if not parent:
            return False
        return bool(user32.IsWindow(parent))
