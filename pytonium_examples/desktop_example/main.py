import asyncio
import os
from datetime import datetime
from Pytonium import Pytonium, run_pytonium_async, returns_value_to_javascript

# --- Data API for File Explorer ---
@returns_value_to_javascript("any")
def list_directory(path=None):
    """Reads a directory and returns its contents to JavaScript."""
    # Default to the user's home directory if no path is provided
    if not path:
        path = os.path.expanduser("~")

    # Use the error handling pattern to gracefully handle permission issues
    try:
        items = []
        for entry in os.scandir(path):
            items.append({
                "name": entry.name,
                "is_dir": entry.is_dir(),
                # Convert size to KB for files
                "size": f"{entry.stat().st_size / 1024:.1f} KB" if entry.is_file() else ""
            })

        # Sort folders first, then alphabetically
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

        return {
            "success": True,
            "current_path": path,
            "items": items
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Background Services ---
async def clock_service(p: Pytonium):
    """Push real system time to the UI every second."""
    while p.is_running():
        now = datetime.now()
        p.set_state("system", "time", now.strftime("%I:%M %p"))
        p.set_state("system", "date", now.strftime("%m/%d/%Y"))
        await asyncio.sleep(1.0)

async def main():
    p = Pytonium()
    p.set_frameless_window(True)

    # Bind window controls
    p.bind_function_to_javascript(p.close_window, name="close", javascript_object="win")

    # Bind our new file system API
    p.bind_function_to_javascript(list_directory, javascript_object="data_api")

    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web/")
    p.add_custom_scheme("app", web_dir)
    p.initialize("app://index.html", 1280, 720)

    await asyncio.gather(
        run_pytonium_async(p),
        clock_service(p),
    )
    p.shutdown()

if __name__ == "__main__":
    asyncio.run(main())