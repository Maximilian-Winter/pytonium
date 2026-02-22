"""Win32 window helpers for manipulating Pytonium widget windows."""

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

    # -- Wallpaper mode (WorkerW / Progman) ------------------------------------

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

    # For wallpaper debug/verification
    user32.GetClassNameW.argtypes = [HWND, ctypes.wintypes.LPWSTR, INT]
    user32.GetClassNameW.restype = INT

    user32.GetWindowRect.argtypes = [HWND, ctypes.POINTER(ctypes.wintypes.RECT)]
    user32.GetWindowRect.restype = BOOL

    user32.MoveWindow.argtypes = [HWND, INT, INT, INT, INT, BOOL]
    user32.MoveWindow.restype = BOOL

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


class Win32WindowHelper:
    """Applies Windows-specific window properties to Pytonium windows.

    Must be called after pytonium.initialize() when the HWND exists.
    All methods are static and take an HWND (as int).
    """

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

    @staticmethod
    def hide_from_taskbar(hwnd):
        """Hide the window from the taskbar."""
        ex_style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        ex_style |= WS_EX_TOOLWINDOW
        ex_style &= ~WS_EX_APPWINDOW
        user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, ex_style)

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

    @staticmethod
    def set_position(hwnd, x, y, width, height):
        """Set the window position and size."""
        user32.SetWindowPos(
            hwnd, 0,
            x, y, width, height,
            SWP_NOZORDER | SWP_NOACTIVATE,
        )

    @staticmethod
    def show_window(hwnd):
        """Show the window."""
        user32.ShowWindow(hwnd, 5)  # SW_SHOW

    @staticmethod
    def hide_window(hwnd):
        """Hide the window."""
        user32.ShowWindow(hwnd, 0)  # SW_HIDE

    @staticmethod
    def get_primary_monitor_size():
        """Returns (width, height) of the primary monitor."""
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    # -- Multi-monitor support -------------------------------------------------

    @staticmethod
    def enumerate_monitors():
        """Enumerate all display monitors.

        Returns a list of MonitorInfo sorted so the primary monitor is index 0.
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
        """Return the primary MonitorInfo (convenience)."""
        monitors = Win32WindowHelper.enumerate_monitors()
        for m in monitors:
            if m.is_primary:
                return m
        return monitors[0] if monitors else None

    @staticmethod
    def get_monitor_for_window(hwnd):
        """Return the MonitorInfo for the monitor containing the given HWND."""
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

    # -- AppBar (bar mode) -----------------------------------------------------

    @staticmethod
    def register_appbar(hwnd, edge_str, size, monitor=None):
        """Register the window as an AppBar and reserve screen space.

        Args:
            hwnd: Window handle.
            edge_str: "top", "bottom", "left", or "right".
            size: Height (for top/bottom) or width (for left/right) in pixels.
            monitor: Optional MonitorInfo. Defaults to primary monitor.

        Returns:
            APPBARDATA instance (keep reference for unregister), or None on failure.
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

    # -- Wallpaper mode (WorkerW) ----------------------------------------------

    @staticmethod
    def find_wallpaper_worker_w():
        """Find or create the WorkerW window for wallpaper embedding.

        Sends the undocumented 0x052C message to Progman to spawn WorkerW,
        then finds the correct target via EnumWindows. Supports both
        Windows 10 layout (SHELLDLL_DefView in WorkerW) and Windows 11
        layout (SHELLDLL_DefView under Progman).

        Returns:
            (parent_hwnd, strategy) — the HWND to SetParent into and a
            string describing the strategy ('worker_w' or 'progman').
            Returns (0, None) on failure.
        """
        progman = user32.FindWindowW("Progman", None)
        if not progman:
            print("Win32WindowHelper: Progman not found")
            return 0, None

        # Send undocumented message to enable wallpaper layering
        result = ctypes.wintypes.DWORD(0)
        user32.SendMessageTimeoutW(
            progman, 0x052C, 0, 0,
            SMTO_NORMAL, 1000, ctypes.byref(result),
        )

        # Enumerate all top-level windows to find:
        #   - Where SHELLDLL_DefView (desktop icons) lives
        #   - All WorkerW windows (with and without SHELLDLL_DefView)
        shell_view_parent = [0]
        worker_ws_with_shell = []
        worker_ws_without_shell = []
        sibling_worker = [0]

        def _enum_cb(hwnd, lparam):
            # Check if this window contains SHELLDLL_DefView
            shell_view = user32.FindWindowExW(
                hwnd, None, "SHELLDLL_DefView", None
            )
            if shell_view:
                shell_view_parent[0] = hwnd
                # Classic approach: find the next WorkerW sibling
                worker = user32.FindWindowExW(
                    None, hwnd, "WorkerW", None
                )
                if worker:
                    sibling_worker[0] = worker

            # Classify all WorkerW windows
            class_buf = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, class_buf, 64)
            if class_buf.value == "WorkerW":
                child_shell = user32.FindWindowExW(
                    hwnd, None, "SHELLDLL_DefView", None
                )
                if child_shell:
                    worker_ws_with_shell.append(hwnd)
                else:
                    worker_ws_without_shell.append(hwnd)

            return True  # continue

        cb = WNDENUMPROC(_enum_cb)
        user32.EnumWindows(cb, 0)

        print(f"  Wallpaper scan: Progman={progman:#x}, "
              f"SHELLDLL_DefView parent={shell_view_parent[0]:#x}, "
              f"WorkerW with icons={len(worker_ws_with_shell)}, "
              f"WorkerW empty={len(worker_ws_without_shell)}, "
              f"sibling WorkerW={sibling_worker[0]:#x}")

        # --- Strategy selection ---

        # Strategy 1: Classic (Win10) — SHELLDLL_DefView is in a WorkerW.
        # The other WorkerW (without SHELLDLL_DefView) is our wallpaper surface.
        if worker_ws_with_shell and worker_ws_without_shell:
            target = worker_ws_without_shell[0]
            print(f"  Wallpaper strategy: worker_w (classic), target={target:#x}")
            return target, "worker_w"

        # Strategy 2: SHELLDLL_DefView is under Progman (Win11 common).
        # On Windows 11, SHELLDLL_DefView stays under Progman and 0x052C
        # may spawn many WorkerW windows for various DWM purposes.
        # Parenting to Progman is more reliable — our child window sits
        # above Progman's wallpaper bitmap but below SHELLDLL_DefView
        # (using HWND_BOTTOM z-order).
        if shell_view_parent[0] == progman:
            print(f"  Wallpaper strategy: progman (win11), target={progman:#x}")
            return progman, "progman"

        # Strategy 3: Use the sibling WorkerW found via FindWindowExW.
        if sibling_worker[0]:
            target = sibling_worker[0]
            print(f"  Wallpaper strategy: worker_w (sibling), target={target:#x}")
            return target, "worker_w"

        # Strategy 4: Any available WorkerW.
        if worker_ws_without_shell:
            target = worker_ws_without_shell[0]
            print(f"  Wallpaper strategy: worker_w (any), target={target:#x}")
            return target, "worker_w"

        # Strategy 5: Fallback — parent directly to Progman.
        if progman:
            print(f"  Wallpaper strategy: progman (fallback), target={progman:#x}")
            return progman, "progman"

        print("  Wallpaper strategy: FAILED — no suitable parent found")
        return 0, None

    @staticmethod
    def make_wallpaper(hwnd, monitor=None):
        """Parent the window to the WorkerW behind desktop icons.

        Converts the window from WS_POPUP to WS_CHILD before calling
        SetParent so that it properly nests behind desktop icons
        instead of floating on top as an owned popup.

        Args:
            hwnd: The widget window handle.
            monitor: Optional MonitorInfo to position on a specific monitor.

        Returns:
            True if successful, False otherwise.
        """
        parent_hwnd, strategy = Win32WindowHelper.find_wallpaper_worker_w()
        if not parent_hwnd:
            print("Win32WindowHelper: Failed to find parent for wallpaper mode")
            return False

        if monitor is None:
            monitor = Win32WindowHelper.get_primary_monitor()

        # -- Convert WS_POPUP → WS_CHILD before SetParent --
        # CEF frameless windows use WS_POPUP. SetParent on a WS_POPUP
        # creates an "owned popup" that floats above siblings (including
        # SHELLDLL_DefView → desktop icons). Converting to WS_CHILD
        # ensures true child window z-order nesting.
        style = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
        original_style = style
        style = (style & ~WS_POPUP) | WS_CHILD
        user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style)
        print(f"  Wallpaper style: {original_style:#010x} → {style:#010x}")

        # SetParent into the target
        prev_parent = user32.SetParent(hwnd, parent_hwnd)
        print(f"  Wallpaper SetParent: hwnd={hwnd:#x} → parent={parent_hwnd:#x} "
              f"(prev={prev_parent:#x})")

        # -- Position to fill the target monitor --
        # After SetParent, coordinates are relative to the parent's
        # client area. WorkerW spans the virtual desktop, so
        # monitor.x/y are correct offsets within it.
        # Use SWP_FRAMECHANGED to force Windows to recalculate the frame
        # after the style change.
        if strategy == "progman":
            # When parented to Progman, put at BOTTOM of z-order
            # so we sit behind SHELLDLL_DefView (desktop icons).
            user32.SetWindowPos(
                hwnd, HWND_BOTTOM,
                monitor.x, monitor.y, monitor.width, monitor.height,
                SWP_NOACTIVATE | SWP_FRAMECHANGED,
            )
        else:
            user32.SetWindowPos(
                hwnd, 0,
                monitor.x, monitor.y, monitor.width, monitor.height,
                SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED,
            )

        # Force show (SetParent can hide the window on some builds)
        user32.ShowWindow(hwnd, 5)  # SW_SHOW

        # -- Verify actual position --
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        actual_w = rect.right - rect.left
        actual_h = rect.bottom - rect.top
        print(f"  Wallpaper target: {monitor.x},{monitor.y} "
              f"{monitor.width}x{monitor.height}")
        print(f"  Wallpaper actual: {rect.left},{rect.top} "
              f"{actual_w}x{actual_h}")

        # If size doesn't match (DPI mismatch), try MoveWindow as fallback
        if actual_w != monitor.width or actual_h != monitor.height:
            print(f"  Wallpaper size mismatch — retrying with MoveWindow")
            user32.MoveWindow(
                hwnd,
                monitor.x, monitor.y,
                monitor.width, monitor.height,
                True,
            )
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            actual_w = rect.right - rect.left
            actual_h = rect.bottom - rect.top
            print(f"  Wallpaper after MoveWindow: {rect.left},{rect.top} "
                  f"{actual_w}x{actual_h}")

        return True

    @staticmethod
    def restore_from_wallpaper(hwnd):
        """Unparent the window from WorkerW (restore to normal desktop).

        Restores WS_POPUP style (from WS_CHILD) before unparenting
        so the window can exist as a standalone top-level window again.
        """
        # Restore WS_POPUP before unparenting
        style = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
        style = (style & ~WS_CHILD) | WS_POPUP
        user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style)
        user32.SetParent(hwnd, None)

    @staticmethod
    def set_window_z_bottom(hwnd):
        """Place window at the bottom of its sibling z-order."""
        user32.SetWindowPos(
            hwnd, HWND_BOTTOM,
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
        )

    @staticmethod
    def reparent_wallpaper(hwnd, new_parent, strategy="worker_w"):
        """Re-parent a wallpaper widget to a new Progman/WorkerW.

        Used by the health check when explorer.exe restarts.
        The window is already WS_CHILD, so just SetParent + z-order.
        """
        user32.SetParent(hwnd, new_parent)
        if strategy == "progman":
            user32.SetWindowPos(
                hwnd, HWND_BOTTOM,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
            )

    @staticmethod
    def is_wallpaper_parent_valid(hwnd):
        """Check if a wallpaper widget's parent WorkerW is still alive."""
        parent = user32.GetParent(hwnd)
        if not parent:
            return False
        return bool(user32.IsWindow(parent))
