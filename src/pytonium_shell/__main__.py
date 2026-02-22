"""Entry point for running PytoniumShell as a module.

Usage:
    pytonium-shell                              # run bundled example widgets
    pytonium-shell --widgets-dir ./my_widgets   # run custom widgets
    python -m pytonium_shell --widgets-dir ./my_widgets
"""

import argparse
import importlib.resources
import os
import sys

from .shell_manager import ShellManager


def _bundled_widgets_dir():
    """Return the path to the bundled example widgets."""
    return str(importlib.resources.files("pytonium_shell") / "example_widgets")


def main():
    parser = argparse.ArgumentParser(description="PytoniumShell - Desktop Widget Framework")
    parser.add_argument(
        "--widgets-dir",
        default=None,
        help="Path to the widgets directory (default: bundled examples)"
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to config.json (optional)"
    )
    parser.add_argument(
        "--theme",
        default="default",
        help="Theme name to use (default: 'default')"
    )
    args = parser.parse_args()

    widgets_dir = args.widgets_dir or _bundled_widgets_dir()

    if not os.path.isdir(widgets_dir):
        print(f"Error: Widgets directory not found: {widgets_dir}")
        sys.exit(1)

    shell = ShellManager(
        widgets_dir=widgets_dir,
        config_path=args.config,
        theme_name=args.theme,
    )
    shell.run()


if __name__ == "__main__":
    main()
