cd src/pytonium_python_framework
python -m build --wheel
pip install dist/pytonium-0.0.13-cp313-cp313-win_amd64.whl --force-reinstall

New Python API Methods:

from Pytonium import Pytonium

pytonium = Pytonium()

# Enable frameless window (call before initialize())
pytonium.set_frameless_window(True)

# Window controls
pytonium.minimize_window()
pytonium.maximize_window()
pytonium.restore_window()
pytonium.close_window()

# Check state
is_max = pytonium.is_maximized()

# Drag window (for frameless mode)
pytonium.drag_window(delta_x, delta_y)

# Get/set position
x, y = pytonium.get_window_position()
pytonium.set_window_position(x, y)

# Get/set size
width, height = pytonium.get_window_size()
pytonium.set_window_size(width, height)

# Resize with anchor (0-3)
pytonium.resize_window(new_width, new_height, anchor=0)
