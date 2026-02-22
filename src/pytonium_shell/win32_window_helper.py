"""Win32 window helpers for manipulating Pytonium widget windows."""

import ctypes
import ctypes.wintypes
import os

if os.name == "nt":
    user32 = ctypes.windll.user32
    shell32 = ctypes.windll.shell32

# Window style constants
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000

# SetWindowPos constants
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_NOZORDER = 0x0004


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
        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex_style |= WS_EX_TOOLWINDOW
        ex_style &= ~WS_EX_APPWINDOW
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

    @staticmethod
    def make_click_through(hwnd):
        """Make the window click-through (mouse events pass to windows below)."""
        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex_style |= WS_EX_TRANSPARENT | WS_EX_LAYERED
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

    @staticmethod
    def remove_click_through(hwnd):
        """Remove click-through from the window."""
        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex_style &= ~WS_EX_TRANSPARENT
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

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
