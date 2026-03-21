"""
Pytonium Termux — Standalone terminal multiplexer

A lightweight, tmux-style terminal multiplexer built with Pytonium.
Manages multiple terminal sessions (PTY on Unix, pipe on Windows)
displayed in xterm.js panes inside a single frameless CEF window.

Usage:
    python main.py [working_dir]

Dependencies:
    pip install Pytonium
"""

import asyncio
import base64
import json
import os
import sys
import time
from pathlib import Path

from Pytonium import Pytonium, run_pytonium_async, returns_value_to_javascript
from terminal_manager import terminal_manager


# ============================================================================
# Globals
# ============================================================================

pytonium: Pytonium = None  # type: ignore
DEFAULT_CWD = os.getcwd()

# ============================================================================
# Window Controls (frameless)
# ============================================================================

@returns_value_to_javascript("boolean")
def window_is_maximized() -> bool:
    return pytonium.is_maximized()

def window_minimize():
    pytonium.minimize_window()

def window_maximize():
    if pytonium.is_maximized():
        pytonium.restore_window()
    else:
        pytonium.maximize_window()

def window_close():
    pytonium.close_window()

def window_start_drag():
    pytonium.start_window_drag()

def window_resize(new_width: int, new_height: int, anchor: int):
    pytonium.resize_window(new_width, new_height, anchor)


# ============================================================================
# Terminal API — bound to Pytonium.terminal.*
# ============================================================================

@returns_value_to_javascript("object")
def create_terminal(working_dir: str = "", cols: int = 80, rows: int = 24) -> dict:
    """Create a new terminal session. Returns session info dict."""
    cwd = working_dir or DEFAULT_CWD
    try:
        session = terminal_manager.create_session(cwd, cols, rows)
        return session.to_dict()
    except Exception as e:
        return {"error": str(e)}


@returns_value_to_javascript("object")
def list_terminals() -> list:
    """List all terminal sessions."""
    return terminal_manager.list_sessions()


@returns_value_to_javascript("boolean")
def kill_terminal(session_id: str) -> bool:
    """Kill a terminal session."""
    return terminal_manager.kill_session(session_id)


def write_terminal(session_id: str, data: str):
    """Write string data to a terminal session (called from JS)."""
    terminal_manager.write(session_id, data.encode("utf-8"))


def write_terminal_bytes(session_id: str, b64_data: str):
    """Write base64-encoded bytes to a terminal (for binary data)."""
    raw = base64.b64decode(b64_data)
    terminal_manager.write(session_id, raw)


@returns_value_to_javascript("boolean")
def resize_terminal(session_id: str, cols: int, rows: int) -> bool:
    """Resize a terminal session."""
    return terminal_manager.resize(session_id, cols, rows)


# ============================================================================
# Output polling — push terminal output to xterm.js
# ============================================================================

def poll_terminal_output():
    """Called from the main loop.  Drains output buffers and pushes
    base64-encoded chunks to the browser via execute_javascript().
    """
    for info in terminal_manager.list_sessions():
        sid = info["id"]
        data = terminal_manager.drain_output(sid)
        if data:
            # Encode as base64 so we can safely embed in JS string
            b64 = base64.b64encode(data).decode("ascii")
            pytonium.execute_javascript(
                f'window.__termux_onData("{sid}", "{b64}");'
            )
        # Notify JS if session exited
        if info["status"] != "running":
            pytonium.execute_javascript(
                f'window.__termux_onExit("{sid}");'
            )


# ============================================================================
# Async main loop
# ============================================================================

async def output_poller(p: Pytonium):
    """Async task: poll terminal output at ~60fps."""
    while p.is_running():
        poll_terminal_output()
        await asyncio.sleep(0.016)


async def main():
    global pytonium, DEFAULT_CWD

    # Optional: first arg is the default working directory
    if len(sys.argv) > 1:
        candidate = Path(sys.argv[1]).resolve()
        if candidate.is_dir():
            DEFAULT_CWD = str(candidate)

    pytonium = Pytonium()
    pytonium.set_frameless_window(True)

    # ── Window controls ──
    pytonium.bind_function_to_javascript(
        window_is_maximized, name="isMaximized", javascript_object="win"
    )
    pytonium.bind_function_to_javascript(
        window_minimize, name="minimize", javascript_object="win"
    )
    pytonium.bind_function_to_javascript(
        window_maximize, name="maximize", javascript_object="win"
    )
    pytonium.bind_function_to_javascript(
        window_close, name="close", javascript_object="win"
    )
    pytonium.bind_function_to_javascript(
        window_start_drag, name="startDrag", javascript_object="win"
    )
    pytonium.bind_function_to_javascript(
        window_resize, name="resize", javascript_object="win"
    )

    # ── Terminal API ──
    pytonium.bind_function_to_javascript(
        create_terminal, name="create", javascript_object="terminal"
    )
    pytonium.bind_function_to_javascript(
        list_terminals, name="list", javascript_object="terminal"
    )
    pytonium.bind_function_to_javascript(
        kill_terminal, name="kill", javascript_object="terminal"
    )
    pytonium.bind_function_to_javascript(
        write_terminal, name="write", javascript_object="terminal"
    )
    pytonium.bind_function_to_javascript(
        write_terminal_bytes, name="writeBytes", javascript_object="terminal"
    )
    pytonium.bind_function_to_javascript(
        resize_terminal, name="resize", javascript_object="terminal"
    )

    # ── TypeScript definitions (dev mode) ──
    if os.environ.get("DEV_MODE"):
        pytonium.generate_typescript_definitions("./pytonium.d.ts")

    # ── Launch ──
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "index.html")

    pytonium.initialize(f"file:///{html_path}", 1400, 900)

    print("=" * 56)
    print("  Pytonium Termux — Terminal Multiplexer")
    print("=" * 56)
    print(f"  Default CWD: {DEFAULT_CWD}")
    print(f"  Platform:    {sys.platform}")
    print("  Shortcuts:   Ctrl+T = New  |  Ctrl+W = Kill")
    print("=" * 56)

    # Run Pytonium loop + output poller concurrently
    await asyncio.gather(
        run_pytonium_async(pytonium),
        output_poller(pytonium),
    )

    # Cleanup
    terminal_manager.cleanup()
    pytonium.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
