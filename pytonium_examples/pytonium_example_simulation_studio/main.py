"""Run with python main.py [--workspace PATH]."""
import argparse
import multiprocessing
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description="Murmuration: a local flocking observatory")
    parser.add_argument("--workspace", type=Path, default=Path.home() / ".pytonium" / "murmuration")
    parser.add_argument("--devtools", action="store_true")
    args = parser.parse_args()
    # Import CEF only in the UI process, never during multiprocessing spawn.
    from Pytonium import Pytonium, returns_value_to_javascript
    from controller import Controller

    root = Path(__file__).resolve().parent
    controller = Controller(args.workspace)
    app = Pytonium()

    @returns_value_to_javascript("object")
    def command(action: str, args: dict):
        return controller.command(action, args)

    app.bind_function_to_javascript(command, "command", "studio")
    # A directory as URL host gives relative module/CSS URLs a stable base.
    app.add_custom_scheme("murmuration", root.parent.as_posix() + "/")
    app.set_cache_path(str(args.workspace.resolve() / "browser-cache"))
    app.set_show_debug_context_menu(args.devtools)
    app.generate_typescript_definitions(str(root / "studio.d.ts"))
    try:
        app.initialize("murmuration://pytonium_example_simulation_studio/index.html", 1440, 900)
        while app.is_running():
            app.update_message_loop()
            for update in controller.poll():
                for key in ("status", "config", "frame", "metrics", "library", "experiments"):
                    if key in update:
                        app.set_state("studio", key, update[key])
                if update["type"] in ("completed", "error", "fatal"):
                    app.set_state("studio", "event", update)
            time.sleep(.005)
    finally:
        controller.close()
        app.shutdown()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
