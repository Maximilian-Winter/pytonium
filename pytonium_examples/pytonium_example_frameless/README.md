# Pytonium Frameless Window Example

A complete example demonstrating Pytonium's frameless window capabilities with a custom HTML/CSS title bar, draggable window, resizable window, and Python-JavaScript bidirectional communication.

## Features

- **Frameless Window**: Custom window without Chrome UI or system title bar
- **Custom Title Bar**: Beautiful gradient design with minimize/maximize/close buttons
- **Draggable Window**: Click and drag the title bar to move the window
- **Resizable Window**: Drag window edges/corners to resize (8 resize handles)
- **UI Feedback Display**: Visual feedback panel showing button click reactions
- **Python-JavaScript Bindings**: Call Python functions from JavaScript and return values
- **State Management**: Sync data between Python and JavaScript in real-time

## Screenshot

The example creates a modern-looking desktop application with:
- Gradient title bar with window controls
- Clean card-based UI sections
- Real-time feedback display
- Console-like output log

## Prerequisites

- Python 3.10+ (64-bit)
- Pytonium installed (`pip install pytonium`)
- Windows 10/11 or Linux

## Running the Example

### Option 1: Direct Run

```bash
cd pytonium_examples/pytonium_example_frameless
python main.py
```

### Option 2: From Project Root

```bash
python pytonium_examples/pytonium_example_frameless/main.py
```

## What You'll See

When you run the example:

1. **A frameless window opens** with a custom purple gradient title bar
2. **Window is draggable** - Click and hold the title bar (not buttons) to drag
3. **Window is resizable** - Drag any edge or corner to resize
4. **Click buttons** to test Python-JavaScript communication:
   - `testfunc()` - Returns an object from Python
   - `test_one(64)` - Returns a calculated value
   - `test_two()` - Executes without return value
   - `Set User State` - Demonstrates state management
5. **Watch the UI Feedback panel** - Shows visual reactions to button clicks
6. **Check the Output Log** - Detailed console output

## Code Structure

### Python (`main.py`)

```python
# 1. Create Pytonium instance
pytonium = Pytonium()

# 2. Enable frameless window (before initialize!)
pytonium.set_frameless_window(True)

# 3. Bind Python functions to JavaScript
pytonium.bind_function_to_javascript(my_function, "myFunc", "api")

# 4. Window controls
pytonium.minimize_window()
pytonium.maximize_window()
pytonium.drag_window(delta_x, delta_y)

# 5. Initialize and run
pytonium.initialize("file://index.html", width, height)
```

### HTML/CSS (`index.html`)

The HTML includes:
- Custom `.titlebar` div with gradient background
- Window control buttons (minimize, maximize, close)
- `.content` area with cards and buttons
- JavaScript for:
  - Draggable title bar (mousedown/mousemove/mouseup handlers)
  - Calling Python bindings (`Pytonium.window.minimize()`)
  - UI feedback display

## Key Concepts

### Frameless Window

```python
pytonium.set_frameless_window(True)  # Must be called BEFORE initialize()
```

This removes the system title bar, allowing you to create your own with HTML/CSS.

### Window Controls

The Python window control functions are bound to JavaScript:

```python
# In Python
def window_minimize():
    pytonium.minimize_window()

pytonium.bind_function_to_javascript(window_minimize, "minimize", "window")
```

```javascript
// In JavaScript
Pytonium.window.minimize();  // Calls Python function
```

### Draggable Window

The dragging logic is in JavaScript:

```javascript
titlebar.addEventListener('mousedown', (e) => {
    isDragging = true;
    dragStartX = e.screenX;
    dragStartY = e.screenY;
});

document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const deltaX = e.screenX - dragStartX;
    const deltaY = e.screenY - dragStartY;
    Pytonium.window.drag(deltaX, deltaY);  // Calls C++ drag
});
```

### Python-JavaScript Bindings

**Python → JavaScript (State updates):**
```python
pytonium.set_state("user", "age", 25)  # JS receives event
```

**JavaScript → Python (Function calls):**
```javascript
let result = await Pytonium.api.myFunction(arg);
```

## Customization

### Change Title Bar Color

Edit the CSS in `index.html`:

```css
.titlebar {
    background: linear-gradient(135deg, #YOUR_COLOR 0%, #OTHER_COLOR 100%);
}
```

### Add More Window Controls

In Python:
```python
def my_custom_action():
    # Your code here
    pass

pytonium.bind_function_to_javascript(my_custom_action, "customAction", "window")
```

In HTML:
```html
<button onclick="Pytonium.window.customAction()">Custom</button>
```

### Disable Resizing

Remove the resize handle CSS and JavaScript from `index.html`.

## Troubleshooting

### Window appears with system title bar
Make sure `set_frameless_window(True)` is called **before** `initialize()`.

### Window not draggable
Check that the `mousedown` event listener is attached to the titlebar and not blocked by buttons.

### Python functions not callable from JavaScript
Ensure functions are bound **before** calling `initialize()`.

## See Also

- [Pytonium Documentation](../../readme.md)
- [How to Build from Source](../../how-to-build-from-source.md)
- [API Reference](../../ONBOARDING.md)
