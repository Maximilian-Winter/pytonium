"""Compatibility shim — the real implementation now lives in Pytonium.win32_helpers.

All imports from ``pytonium_shell.win32_window_helper`` continue to work
via this re-export.
"""
from Pytonium.win32_helpers import *  # noqa: F401,F403
