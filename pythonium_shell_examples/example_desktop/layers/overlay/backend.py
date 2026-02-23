"""Overlay layer backend — provides app search and launching."""

import os
import json
from Pytonium import returns_value_to_javascript


class LayerBackend:
    """Exposed to JavaScript as Pytonium.layer.*"""

    def __init__(self):
        self._apps_cache = None

    @returns_value_to_javascript("any")
    def get_installed_apps(self):
        """Return list of installed apps from Start Menu."""
        if self._apps_cache is not None:
            return self._apps_cache

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
        seen = set()

        for base_dir in search_dirs:
            if not os.path.isdir(base_dir):
                continue
            for root, _dirs, files in os.walk(base_dir):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = os.path.splitext(f)[0]
                        key = name.lower()
                        if key in seen:
                            continue
                        # Skip uninstallers and helpers
                        if any(skip in key for skip in
                               ("uninstall", "readme", "help", "license",
                                "changelog", "release notes")):
                            continue
                        seen.add(key)
                        full_path = os.path.join(root, f)
                        apps.append({
                            "name": name,
                            "path": full_path,
                        })

        apps.sort(key=lambda a: a["name"].lower())
        self._apps_cache = apps
        return apps

    def launch_app(self, path):
        """Launch an application by shortcut path."""
        try:
            os.startfile(path)
        except Exception as e:
            print(f"Failed to launch {path}: {e}")
