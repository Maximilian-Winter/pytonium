"""Theme system - loads theme JSON and injects CSS variables into widgets."""

import json
import os

# Default Tokyo Night theme
DEFAULT_THEME = {
    "name": "Tokyo Night",
    "colors": {
        "background": "rgba(26, 27, 38, 0.85)",
        "foreground": "#a9b1d6",
        "accent": "#7aa2f7",
        "accent2": "#bb9af7",
        "success": "#9ece6a",
        "warning": "#e0af68",
        "error": "#f7768e",
        "muted": "#565f89",
        "border": "rgba(255, 255, 255, 0.08)",
    },
    "font": {
        "family": "'Segoe UI', 'JetBrains Mono', 'Consolas', monospace",
        "size": "13px",
    },
    "border_radius": "12px",
}


class Theme:
    """Loads a theme and injects it as CSS custom properties."""

    def __init__(self, theme_name="default", themes_dir=None):
        self.data = DEFAULT_THEME

        if theme_name != "default" and themes_dir:
            theme_path = os.path.join(themes_dir, f"{theme_name}.json")
            if os.path.isfile(theme_path):
                with open(theme_path, "r") as f:
                    self.data = json.load(f)

    def inject(self, pytonium):
        """Inject theme CSS variables into a Pytonium instance.

        Should be called after initialize() when the browser is ready.
        """
        parts = []
        for key, val in self.data.get("colors", {}).items():
            parts.append(f"--shell-{key}: {val}")

        font = self.data.get("font", {})
        if "family" in font:
            parts.append(f"--shell-font: {font['family']}")
        if "size" in font:
            parts.append(f"--shell-font-size: {font['size']}")

        radius = self.data.get("border_radius", "12px")
        parts.append(f"--shell-radius: {radius}")

        css_vars = ":root { " + "; ".join(parts) + " }"
        # Escape for JS string
        css_vars = css_vars.replace("'", "\\'")

        js = f"document.head.insertAdjacentHTML('beforeend', '<style>{css_vars}</style>')"
        pytonium.execute_javascript(js)
