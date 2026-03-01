import os
import time
from datetime import datetime

# Import the Pytonium class
from Pytonium import Pytonium, ContextMenuParams, returns_value_to_javascript


# This class expose two methods as an endpoint of a javascript binding, and they get called on the test website.
# The first method gets called with one argument and returns a value.
class MyApi:

    def __init__(self):
        self.data = []

    # Needed decorator to mark the method as returning values as Promises in Javascript, optional with return type in Javascript to generate typescript d.ts file of all exposed Python methods and functions.
    @returns_value_to_javascript("number")
    def test_one(self, arg1: int):
        print("Python Method called from Javascript with one argument and returns a value!")
        print(arg1)
        return arg1

    def test_two(self, arg1: str, arg2: int, arg3: int):
        print("Python Method called from Javascript!")
        self.data.append(arg1)
        self.data.append(arg2)
        self.data.append(arg3)
        print(self.data)

# This class get later bind to the context menu of the Pytonium app.
class MyContextMenu:
    def test_context_menu_one(self):
        print("Hello Context Menu 1")

    def test_context_menu_two(self):
        print("Hello Context Menu 2")
        # Here we change the context menu to another namespace, this allows multiple context menus, each under a different namespace.
        pytonium.set_context_menu_namespace("test")


# An example class to handle app state updates from Javascript.
# The update_state method is mandatory and gets called automatically from Pytonium.
class MyStateHandler:

    def update_state(self, namespace, key, value):
        print(f"State Update:\nNamespace={namespace}\nKey={key}\nValue={str(value)}")


# Create a Pytonium instance.
pytonium = Pytonium()

# Create a MyApi instance.
myApi = MyApi()
myContextMenu = MyContextMenu()

# Create a MyStateHandler instance.
myStateHandler = MyStateHandler()


# This function is the endpoint of a javascript binding, and it's get called on the test website and returns a Javascript object.
@returns_value_to_javascript("any")
def testfunc():
    return {"Answer": 42}


# --- Enhanced Context Menu Demo ---

# Standard context menu entries from an object (original behavior, still works)
pytonium.add_context_menu_entries_from_object(myContextMenu)

# Add a separator between sections
pytonium.add_context_menu_separator()

# Additional items in the "test" namespace (shown after switching)
def test_context_menu_three():
    print("Hello Context Menu 3")

def test_context_menu_four():
    print("Hello Context Menu 4")

pytonium.add_context_menu_entry(test_context_menu_three, "Test Context Menu 3!", "test")
pytonium.add_context_menu_entry(test_context_menu_four, "Test Context Menu 4!", "test")

# --- Check item: toggleable option ---
def toggle_dark_mode():
    print("Dark mode toggled!")

pytonium.add_context_menu_check_item(toggle_dark_mode, "Dark Mode", checked=False)

# --- Submenu with radio items ---
def set_size_small():
    pytonium.execute_javascript("document.body.style.fontSize = '12px'")

def set_size_medium():
    pytonium.execute_javascript("document.body.style.fontSize = '16px'")

def set_size_large():
    pytonium.execute_javascript("document.body.style.fontSize = '20px'")

pytonium.add_context_menu_submenu("Font Size", sub_namespace="fontsize")
pytonium.add_context_menu_radio_item(set_size_small, "Small", group_id=1,
                                     context_menu_namespace="fontsize")
pytonium.add_context_menu_radio_item(set_size_medium, "Medium", group_id=1,
                                     context_menu_namespace="fontsize")
pytonium.add_context_menu_radio_item(set_size_large, "Large", group_id=1,
                                     context_menu_namespace="fontsize")

# --- Context-aware handler: receives ContextMenuParams ---
def inspect_click(params: ContextMenuParams):
    print(f"Right-clicked at ({params.x}, {params.y})")
    if params.selection_text:
        print(f"  Selected text: {params.selection_text}")
    if params.link_url:
        print(f"  Link URL: {params.link_url}")
    if params.is_editable:
        print(f"  In editable field")

pytonium.add_context_menu_separator()
pytonium.add_context_menu_entry(inspect_click, "Inspect Click")

# --- Accelerator on first item ---
pytonium.set_context_menu_item_accelerator(0, ord('1'), ctrl=True)  # Ctrl+1 label on first item

# --- Dynamic menu: on_before_context_menu callback ---
def before_menu(params: ContextMenuParams):
    # Example: could enable/disable items based on context
    has_selection = bool(params.selection_text)
    # Items at index 0 and 1 are the context menu object methods
    # (they always stay enabled in this demo)

pytonium.on_before_context_menu(before_menu)


# Add a state handler for the 'user' namespace and receive updates. 'user' is just an example used on the test website.
pytonium.add_state_handler(myStateHandler, ["user"])

# Bind the MyApi instance and the test function to javascript.
pytonium.bind_function_to_javascript(testfunc, javascript_object="test_function_binding")
pytonium.bind_object_methods_to_javascript(myApi, javascript_object="test_class_methods_binding")

# Generate a typescript d.ts file, of the Python bindings, for the IDE to support auto-completetion etc.
pytonium.generate_typescript_definitions("test.d.ts")

# To load a html file, on start up from disk, we need the absolute path to it, so we get it here.
pytonium_test_path = os.path.abspath(__file__)
pytonium_test_path = os.path.dirname(pytonium_test_path)

# Set a custom icon for the window.
pytonium.set_custom_icon_path(f"radioactive.ico")


# Start Pytonium and pass it the start-up URL or file and the width and height of the Window.
pytonium.initialize(f"file://{pytonium_test_path}\\index.html", 1920, 1080)
#pytonium.set_fullscreen(True)
# Start a loop to update the Pytonium message loop and execute some javascript.
while pytonium.is_running():
    time.sleep(0.01)

    # Update the message loop.
    pytonium.update_message_loop()

    # Get the current time and date for displaying it on the test website.
    now = datetime.now()

    # Format the date and time string.
    date_time = now.strftime("%d.%m.%Y, %H:%M:%S")

    # Set an app state to a specific value.
    pytonium.set_state("app-general", "date", date_time)

    # Example on how to execute Javascript from Python:

    # Save the needed Javascript, to call a function and update a ticker with the current date and time.
    # We created and exposed this function in Javascript on the HTML site.
    # code = f"CallFromPythonExample.setTicker('{date_time}')"

    # Execute the javascript.
    # pytonium.execute_javascript(code)
