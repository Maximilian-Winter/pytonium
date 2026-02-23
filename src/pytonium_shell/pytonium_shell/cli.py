"""Entry point for running PytoniumShell as a module.

Usage:
    pytonium-shell                              # run bundled example widgets
    pytonium-shell --widgets-dir ./my_widgets   # run custom widgets
    pytonium-shell --shell ./my_desktop         # run desktop compositor mode
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


def pythonium_shell_main():
    parser = argparse.ArgumentParser(
        description="PytoniumShell - Desktop Widget & Shell Framework"
    )
    parser.add_argument(
        "--widgets-dir",
        default=None,
        help="Path to the widgets directory (default: bundled examples)"
    )
    parser.add_argument(
        "--shell",
        default=None,
        help="Path to a shell directory containing shell.json (desktop compositor mode)"
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to config.json (optional, for widget mode)"
    )
    parser.add_argument(
        "--theme",
        default="default",
        help="Theme name to use (default: 'default')"
    )
    args = parser.parse_args()

    if args.shell:
        # Desktop compositor mode: load shell.json with layer definitions
        if not os.path.isdir(args.shell):
            print(f"Error: Shell directory not found: {args.shell}")
            sys.exit(1)

        shell_json = os.path.join(args.shell, "shell.json")
        if not os.path.isfile(shell_json):
            print(f"Error: shell.json not found in {args.shell}")
            sys.exit(1)

        from .desktop_shell_manager import DesktopShellManager
        shell = DesktopShellManager(
            shell_dir=args.shell,
            config_path=args.config,
            theme_name=args.theme,
        )
    else:
        # Widget mode (original PytoniumShell behavior)
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
    pythonium_shell_main()
