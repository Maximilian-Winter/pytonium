"""
Pytonium Frameless Window Example

This example demonstrates:
- Frameless window with custom HTML/CSS title bar
- Draggable window (click and drag title bar)
- Resizable window (drag edges/corners)
- Window controls (minimize, maximize, close)
- Python-JavaScript bidirectional communication
- UI feedback display
"""

import os
import time
from datetime import datetime

from Pytonium import Pytonium, returns_value_to_javascript


# ============================================================================
# Python Functions Exposed to JavaScript
# ============================================================================

@returns_value_to_javascript("any")
def testfunc():
    """Returns an object to JavaScript."""
    print("Python: testfunc() called from JavaScript!")
    return {"Answer": 42, "Message": "Hello from Python!"}


@returns_value_to_javascript("number")
def test_one(arg1: int):
    """Returns a value to JavaScript."""
    print(f"Python: test_one({arg1}) called from JavaScript!")
    return arg1 * 2


def test_two(arg1: str, arg2: int, arg3: int):
    """No return value - just prints."""
    print(f"Python: test_two() called from JavaScript!")
    print(f"  arg1 (str): {arg1}")
    print(f"  arg2 (int): {arg2}")
    print(f"  arg3 (int): {arg3}")


# ============================================================================
# Window Control Functions (called from JavaScript)
# ============================================================================

@returns_value_to_javascript("boolean")
def window_is_maximized() -> bool:
    """Check if window is maximized."""
    return pytonium.is_maximized()


@returns_value_to_javascript("object")
def window_get_position():
    """Get window position as {x, y}."""
    x, y = pytonium.get_window_position()
    return {"x": x, "y": y}


@returns_value_to_javascript("object")
def window_get_size():
    """Get window size as {width, height}."""
    width, height = pytonium.get_window_size()
    return {"width": width, "height": height}


def window_minimize():
    """Minimize the window."""
    print("Python: Minimizing window...")
    pytonium.minimize_window()


def window_maximize():
    """Toggle maximize/restore."""
    print("Python: Toggling maximize/restore...")
    if pytonium.is_maximized():
        pytonium.restore_window()
        print("Python: Window restored")
    else:
        pytonium.maximize_window()
        print("Python: Window maximized")


def window_close():
    """Close the application."""
    print("Python: Closing application...")
    pytonium.close_window()


def window_drag(delta_x: int, delta_y: int):
    """Drag the window by delta."""
    pytonium.drag_window(delta_x, delta_y)


def window_set_position(x: int, y: int):
    """Set window position."""
    pytonium.set_window_position(x, y)


def window_set_size(width: int, height: int):
    """Set window size."""
    pytonium.set_window_size(width, height)


def window_resize(new_width: int, new_height: int, anchor: int):
    """Resize the window from an anchor point."""
    pytonium.resize_window(new_width, new_height, anchor)


# ============================================================================
# State Handler
# ============================================================================

class MyStateHandler:
    """Handles state updates from JavaScript."""
    
    def update_state(self, namespace: str, key: str, value):
        print(f"\nState Update from JavaScript:")
        print(f"  Namespace: {namespace}")
        print(f"  Key: {key}")
        print(f"  Value: {value}\n")


# ============================================================================
# Main Application
# ============================================================================

def main():
    global pytonium
    
    # Create Pytonium instance
    pytonium = Pytonium()
    
    # =========================================================================
    # Configure Window
    # =========================================================================
    
    # Enable frameless window (custom title bar)
    pytonium.set_frameless_window(True)
    
    # Set custom icon (optional)
    # pytonium.set_custom_icon_path("icon.ico")
    
    # =========================================================================
    # Bind Python Functions to JavaScript
    # =========================================================================
    
    # Test functions
    pytonium.bind_function_to_javascript(testfunc, "testfunc", "test_function_binding")
    pytonium.bind_function_to_javascript(test_one, "test_one", "test_class_methods_binding")
    pytonium.bind_function_to_javascript(test_two, "test_two", "test_class_methods_binding")
    
    # Window control functions
    pytonium.bind_function_to_javascript(window_is_maximized, "isMaximized", "window")
    pytonium.bind_function_to_javascript(window_get_position, "getPosition", "window")
    pytonium.bind_function_to_javascript(window_get_size, "getSize", "window")
    pytonium.bind_function_to_javascript(window_minimize, "minimize", "window")
    pytonium.bind_function_to_javascript(window_maximize, "maximize", "window")
    pytonium.bind_function_to_javascript(window_close, "close", "window")
    pytonium.bind_function_to_javascript(window_drag, "drag", "window")
    pytonium.bind_function_to_javascript(window_set_position, "setPosition", "window")
    pytonium.bind_function_to_javascript(window_set_size, "setSize", "window")
    pytonium.bind_function_to_javascript(window_resize, "resize", "window")
    
    # Add state handler
    state_handler = MyStateHandler()
    pytonium.add_state_handler(state_handler, ["user"])
    
    # Generate TypeScript definitions (optional, for IDE support)
    pytonium.generate_typescript_definitions("test.d.ts")
    
    # =========================================================================
    # Initialize and Start
    # =========================================================================
    
    # Get path to HTML file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "index.html")
    
    # Initialize Pytonium with the HTML file
    pytonium.initialize(f"file://{html_path}", 1200, 800)
    
    print("\n" + "=" * 60)
    print("Pytonium Frameless Window Example Started!")
    print("=" * 60)
    print("Features:")
    print("  - Frameless window with custom title bar")
    print("  - Draggable (click and drag title bar)")
    print("  - Resizable (drag edges/corners)")
    print("  - Window controls (minimize, maximize, close)")
    print("  - Python-JavaScript bindings")
    print("=" * 60 + "\n")
    
    # =========================================================================
    # Main Message Loop
    # =========================================================================
    
    counter = 0
    while pytonium.is_running():
        time.sleep(0.01)
        pytonium.update_message_loop()
        
        counter += 1
        
        # Update date/time display every loop
        now = datetime.now()
        date_time = now.strftime("%d.%m.%Y, %H:%M:%S")
        pytonium.set_state("app-general", "date", date_time)
        
        # Set user age at counter == 500 (demonstrates state updates)
        if counter == 500:
            print("Python: Setting user age to 123...")
            pytonium.set_state("user", "age", 123)


if __name__ == "__main__":
    main()
