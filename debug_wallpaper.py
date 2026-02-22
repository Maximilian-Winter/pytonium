#!/usr/bin/env python3
"""Diagnostic: inspect the desktop window hierarchy for wallpaper embedding.

Prints all relevant HWNDs, their classes, visibility, size, and
SHELLDLL_DefView location.  Run this to understand your Win11 desktop
structure before tweaking wallpaper mode.

Usage:
    python debug_wallpaper.py
"""

import ctypes
import ctypes.wintypes

user32 = ctypes.windll.user32

HWND = ctypes.wintypes.HWND
BOOL = ctypes.wintypes.BOOL
INT  = ctypes.c_int
UINT = ctypes.wintypes.UINT

# DPI awareness
try:
    user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except (AttributeError, OSError):
    pass

user32.FindWindowW.argtypes = [ctypes.wintypes.LPCWSTR, ctypes.wintypes.LPCWSTR]
user32.FindWindowW.restype  = HWND

user32.FindWindowExW.argtypes = [HWND, HWND, ctypes.wintypes.LPCWSTR, ctypes.wintypes.LPCWSTR]
user32.FindWindowExW.restype  = HWND

user32.GetClassNameW.argtypes = [HWND, ctypes.wintypes.LPWSTR, INT]
user32.GetClassNameW.restype  = INT

user32.GetWindowRect.argtypes = [HWND, ctypes.POINTER(ctypes.wintypes.RECT)]
user32.GetWindowRect.restype  = BOOL

user32.IsWindowVisible.argtypes = [HWND]
user32.IsWindowVisible.restype  = BOOL

user32.GetParent.argtypes = [HWND]
user32.GetParent.restype  = HWND

user32.GetWindowLongPtrW.argtypes = [HWND, INT]
user32.GetWindowLongPtrW.restype  = ctypes.c_ssize_t

SMTO_NORMAL = 0x0000
user32.SendMessageTimeoutW.argtypes = [
    HWND, UINT, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
    UINT, UINT, ctypes.POINTER(ctypes.wintypes.DWORD),
]
user32.SendMessageTimeoutW.restype = ctypes.wintypes.LPARAM

WNDENUMPROC = ctypes.WINFUNCTYPE(BOOL, HWND, ctypes.wintypes.LPARAM)
user32.EnumWindows.argtypes = [WNDENUMPROC, ctypes.wintypes.LPARAM]
user32.EnumWindows.restype  = BOOL

user32.EnumChildWindows.argtypes = [HWND, WNDENUMPROC, ctypes.wintypes.LPARAM]
user32.EnumChildWindows.restype  = BOOL


def get_class(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def get_rect(hwnd):
    r = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def get_style(hwnd):
    return user32.GetWindowLongPtrW(hwnd, -16)  # GWL_STYLE


def is_visible(hwnd):
    return bool(user32.IsWindowVisible(hwnd))


def describe(hwnd, label=""):
    cls = get_class(hwnd)
    r = get_rect(hwnd)
    w, h = r[2] - r[0], r[3] - r[1]
    vis = is_visible(hwnd)
    style = get_style(hwnd)
    parent = user32.GetParent(hwnd)
    parent_str = f"{parent:#010x}" if parent else "None"
    child_flag = "CHILD" if (style & 0x40000000) else "POPUP" if (style & 0x80000000) else "OVERLAPPED"
    vis_str = "visible" if vis else "HIDDEN"
    print(f"  {label}{hwnd:#010x}  class={cls:<20s}  {w}x{h} @ {r[0]},{r[1]}  "
          f"{vis_str}  {child_flag}  style={style:#010x}  parent={parent_str}")
    return cls, w, h, vis


def main():
    print("=== Desktop Wallpaper Diagnostic ===\n")

    # 1. Find Progman
    progman = user32.FindWindowW("Progman", None)
    print(f"Progman:")
    if progman:
        describe(progman, "")
    else:
        print("  NOT FOUND")
        return

    # 2. Check Progman's direct children
    print(f"\nProgman children:")
    progman_children = []

    def enum_progman_children(hwnd, lparam):
        progman_children.append(hwnd)
        return True

    cb1 = WNDENUMPROC(enum_progman_children)
    user32.EnumChildWindows(progman, cb1, 0)
    for ch in progman_children:
        cls, w, h, vis = describe(ch, "  ")

    # 3. Send 0x052C
    print(f"\nSending 0x052C to Progman...")
    result = ctypes.wintypes.DWORD(0)
    user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, SMTO_NORMAL, 1000, ctypes.byref(result))
    print(f"  Result: {result.value}")

    # 4. Enumerate all top-level windows
    print(f"\nAll top-level WorkerW windows (after 0x052C):")
    worker_ws = []
    shell_view_parent = [0]

    def enum_all(hwnd, lparam):
        cls = get_class(hwnd)
        # Track SHELLDLL_DefView
        shell = user32.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None)
        if shell:
            shell_view_parent[0] = hwnd

        if cls == "WorkerW":
            worker_ws.append(hwnd)
        return True

    cb2 = WNDENUMPROC(enum_all)
    user32.EnumWindows(cb2, 0)

    for i, ww in enumerate(worker_ws):
        shell = user32.FindWindowExW(ww, None, "SHELLDLL_DefView", None)
        tag = " [HAS SHELLDLL_DefView]" if shell else ""
        cls, w, h, vis = describe(ww, f"  [{i:2d}] ")
        if tag:
            print(f"        {tag}")

    print(f"\nSHELLDLL_DefView parent: {shell_view_parent[0]:#010x} "
          f"({'Progman' if shell_view_parent[0] == progman else 'WorkerW'})")

    # 5. Check Progman children AFTER 0x052C (may have changed)
    print(f"\nProgman children (after 0x052C):")
    progman_children_after = []

    def enum_progman_children_after(hwnd, lparam):
        progman_children_after.append(hwnd)
        return True

    cb3 = WNDENUMPROC(enum_progman_children_after)
    user32.EnumChildWindows(progman, cb3, 0)
    for ch in progman_children_after:
        cls, w, h, vis = describe(ch, "  ")

    # 6. Summary / recommendation
    print(f"\n=== Recommendation ===")
    visible_large_workers = []
    for ww in worker_ws:
        shell = user32.FindWindowExW(ww, None, "SHELLDLL_DefView", None)
        if shell:
            continue
        r = get_rect(ww)
        w, h = r[2] - r[0], r[3] - r[1]
        vis = is_visible(ww)
        if vis and w > 100 and h > 100:
            visible_large_workers.append((ww, w, h))

    if visible_large_workers:
        print(f"Found {len(visible_large_workers)} visible WorkerW candidate(s):")
        for ww, w, h in visible_large_workers:
            print(f"  {ww:#010x}  {w}x{h}")
        print(f"Best candidate: {visible_large_workers[0][0]:#010x}")
    else:
        print("No visible large WorkerW found.")
        print("Try: parent to Progman, or use HWND_BOTTOM top-level approach.")


if __name__ == "__main__":
    main()
