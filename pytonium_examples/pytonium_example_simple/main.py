"""Pytonium Simple Example — Getting Started

Demonstrates all core Pytonium features in a single script:
- JavaScript function bindings (with and without return values)
- State management (Python ↔ JavaScript)
- Context menus (entries, separators, check items, radio items, submenus)
- Dynamic context menu behavior (on_before_context_menu, ContextMenuParams)
- TypeScript definition generation
"""

import os
import time
from datetime import datetime

from Pytonium import Pytonium, ContextMenuParams, returns_value_to_javascript


# ============================================================================
# JavaScript Bindings — Python functions callable from JavaScript
# ============================================================================

class MyApi:
    """Example API exposed to JavaScript via bind_object_methods_to_javascript."""

    def __init__(self):
        self.data = []

    @returns_value_to_javascript("number")
    def test_one(self, arg1: int):
        """Called from JS with one argument, returns a value (as a JS Promise)."""
        print(f"Python: test_one({arg1}) called from JavaScript")
        return arg1

    def test_two(self, arg1: str, arg2: int, arg3: int):
        """Called from JS with multiple arguments, no return value."""
        self.data.extend([arg1, arg2, arg3])
        print(f"Python: test_two() called — data: {self.data}")


@returns_value_to_javascript("any")
def testfunc():
    """Standalone function binding, returns a JS object."""
    return {"Answer": 42}


# ============================================================================
# State Handler — receives state updates from JavaScript
# ============================================================================

class MyStateHandler:
    """Receives state updates pushed from JavaScript."""

    def update_state(self, namespace, key, value):
        print(f"State Update: {namespace}/{key} = {value}")


# ============================================================================
# Context Menus — entries, separators, check items, submenus
# ============================================================================

class MyContextMenu:
    """Context menu entries exposed via add_context_menu_entries_from_object."""

    def test_context_menu_one(self):
        print("Hello Context Menu 1")

    def test_context_menu_two(self):
        print("Hello Context Menu 2")
        # Switch to a different context menu namespace at runtime
        pytonium.set_context_menu_namespace("test")


def test_context_menu_three():
    print("Hello Context Menu 3")


def test_context_menu_four():
    print("Hello Context Menu 4")


def toggle_dark_mode():
    """Check item: toggleable option in the context menu."""
    print("Dark mode toggled!")


def set_size_small():
    pytonium.execute_javascript("document.body.style.fontSize = '12px'")


def set_size_medium():
    pytonium.execute_javascript("document.body.style.fontSize = '16px'")


def set_size_large():
    pytonium.execute_javascript("document.body.style.fontSize = '20px'")


def inspect_click(params: ContextMenuParams):
    """Context-aware handler: receives right-click context data."""
    print(f"Right-clicked at ({params.x}, {params.y})")
    if params.selection_text:
        print(f"  Selected text: {params.selection_text}")
    if params.link_url:
        print(f"  Link URL: {params.link_url}")
    if params.is_editable:
        print(f"  In editable field")


def before_menu(params: ContextMenuParams):
    """Called before the context menu is shown — modify items dynamically."""
    has_selection = bool(params.selection_text)
    # Example: enable/disable items based on selection state
    pytonium.set_context_menu_item_enabled(0, has_selection)


# ============================================================================
# Main
# ============================================================================

def main():
    global pytonium

    pytonium = Pytonium()

    myApi = MyApi()
    myContextMenu = MyContextMenu()
    myStateHandler = MyStateHandler()

    # --- State handler ---
    pytonium.add_state_handler(myStateHandler, ["user"])

    # --- JavaScript bindings ---
    pytonium.bind_function_to_javascript(testfunc, javascript_object="test_function_binding")
    pytonium.bind_object_methods_to_javascript(myApi, javascript_object="test_class_methods_binding")

    # --- Context menu: standard entries from object ---
    pytonium.add_context_menu_entries_from_object(myContextMenu)
    pytonium.add_context_menu_separator()

    # Additional entries in a second namespace (shown after switching)
    pytonium.add_context_menu_entry(test_context_menu_three, "Test Context Menu 3!", "test")
    pytonium.add_context_menu_entry(test_context_menu_four, "Test Context Menu 4!", "test")

    # --- Check item ---
    pytonium.add_context_menu_check_item(toggle_dark_mode, "Dark Mode", checked=False)

    # --- Submenu with radio items ---
    pytonium.add_context_menu_submenu("Font Size", sub_namespace="fontsize")
    pytonium.add_context_menu_radio_item(set_size_small, "Small", group_id=1,
                                         context_menu_namespace="fontsize")
    pytonium.add_context_menu_radio_item(set_size_medium, "Medium", group_id=1,
                                         context_menu_namespace="fontsize")
    pytonium.add_context_menu_radio_item(set_size_large, "Large", group_id=1,
                                         context_menu_namespace="fontsize")

    # --- Context-aware entry + accelerator ---
    pytonium.add_context_menu_separator()
    pytonium.add_context_menu_entry(inspect_click, "Inspect Click")
    pytonium.set_context_menu_item_accelerator(0, ord('1'), ctrl=True)

    # --- Dynamic menu behavior ---
    pytonium.on_before_context_menu(before_menu)

    # --- TypeScript definitions ---
    pytonium.generate_typescript_definitions("test.d.ts")

    # --- Initialize and run ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "index.html")

    pytonium.set_custom_icon_path("radioactive.ico")
    pytonium.initialize(f"file:///{html_path}", 1920, 1080)

    while pytonium.is_running():
        pytonium.update_message_loop()
        time.sleep(0.01)

        now = datetime.now()
        date_time = now.strftime("%d.%m.%Y, %H:%M:%S")
        pytonium.set_state("app-general", "date", date_time)


if __name__ == "__main__":
    main()
