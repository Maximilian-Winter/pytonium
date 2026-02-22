"""System monitor widget backend.

This is an example backend that demonstrates the WidgetBackend pattern.
The system data is primarily pushed via SystemServices state, so this
backend is optional - it provides additional helper functions that
the widget's JavaScript can call directly.
"""

import os


class WidgetBackend:
    """Backend for the system monitor widget."""

    def get_hostname(self):
        """Return the machine hostname."""
        return os.environ.get("COMPUTERNAME", os.uname().nodename if hasattr(os, "uname") else "unknown")

    def get_username(self):
        """Return the current username."""
        return os.environ.get("USERNAME", os.environ.get("USER", "unknown"))
