"""Entry point for running PytoniumShell as a module.

Usage:
    python -m pytonium_shell --widgets-dir ./example_widgets
"""

import argparse
import os
import sys

from .shell_manager import ShellManager


def main():
    parser = argparse.ArgumentParser(description="PytoniumShell - Desktop Widget Framework")
    parser.add_argument(
        "--widgets-dir",
        default=os.path.join(os.getcwd(), "widgets"),
        help="Path to the widgets directory (default: ./widgets)"
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

    if not os.path.isdir(args.widgets_dir):
        print(f"Error: Widgets directory not found: {args.widgets_dir}")
        sys.exit(1)

    shell = ShellManager(
        widgets_dir=args.widgets_dir,
        config_path=args.config,
        theme_name=args.theme,
    )
    shell.run()


if __name__ == "__main__":
    main()
