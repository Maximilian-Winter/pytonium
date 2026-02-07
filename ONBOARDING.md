# Pytonium Project Onboarding Guide

## What is Pytonium?

Pytonium is a Python framework for building desktop applications with a GUI based on web technologies (HTML, CSS, JavaScript). It's similar to Electron but uses Python instead of Node.js for the backend logic.

**Key Features:**
- Create desktop apps using HTML/CSS/JS for the UI
- Call Python functions from JavaScript and return values
- Execute JavaScript from Python
- Custom window layouts (frameless mode with draggable/resizable windows)
- Cross-platform (Windows & Linux)

## Project Structure

```
pytonium/
├── src/
│   ├── pytonium_library/           # Core C++ library (CEF wrapper)
│   │   ├── pytonium_library.h/.cpp # Main library API
│   │   ├── cef_wrapper_*.h/.cc     # CEF integration classes
│   │   ├── javascript_binding.h    # JS-Python binding definitions
│   │   └── ...
│   ├── pytonium_subprocess/        # CEF subprocess executable
│   │   └── pytonium_subprocess.cc  # Entry point for renderer process
│   ├── pytonium_library_test/      # C++ test/example application
│   │   ├── main.cpp                # Example usage of C++ library
│   │   └── index.html              # Test HTML page
│   └── pytonium_python_framework/  # Python package
│       ├── Pytonium/
│       │   ├── src/
│       │   │   ├── pytonium.pyx    # Cython wrapper (Python bindings)
│       │   │   ├── pytonium_library.pxd  # Cython declarations
│       │   │   └── CMakeLists.txt  # Build config for Python ext
│       │   ├── bin_win/            # CEF binaries (Windows)
│       │   └── __init__.py         # Python package entry
│       ├── setup.py                # Build script (scikit-build)
│       ├── pyproject.toml          # Modern Python build config
│       └── CMakeLists.txt          # Main CMake config
│
├── cef-binaries-windows/           # CEF binaries (Windows)
├── cef-binaries-linux/             # CEF binaries (Linux)
├── cmake-build-debug/              # Debug build output
├── cmake-build-release/            # Release build output
│
├── how-to-build-from-source.md     # Build instructions
└── readme.md                       # Main documentation
```

## Key Components

### 1. Core C++ Library (`src/pytonium_library/`)

**Main Classes:**
- `PytoniumLibrary` - Main API class for creating/managing browser windows
- `CefWrapperApp` - CEF application handler
- `CefWrapperBrowserProcessHandler` - Browser process management
- `CefWrapperClientHandler` - Client event handling
- `JavascriptPythonBindingsHandler` - JS-Python function binding

**Key Concepts:**
- **Bindings**: Register Python functions to be callable from JavaScript
- **State Management**: Sync data between Python and JavaScript
- **Custom Schemes**: Define custom protocols (e.g., `pytonium://`)

### 2. Python Framework (`src/pytonium_python_framework/`)

**Build System:**
- Uses `scikit-build` to compile Cython extension
- CMake builds the C++ code and links with Python
- Output: `pytonium.pyd` (Windows) or `pytonium.so` (Linux)

**Python API:**
```python
from Pytonium import Pytonium, returns_value_to_javascript

pytonium = Pytonium()
pytonium.set_frameless_window(True)  # Enable custom window
pytonium.initialize("index.html", 1920, 1080)

@returns_value_to_javascript("number")
def my_function(arg):
    return 42

pytonium.bind_function_to_javascript(my_function, "myFunc", "api")
```

### 3. CEF Subprocess (`src/pytonium_subprocess/`)

- Separate executable required by CEF for sandboxing
- Communicates with main process via IPC
- Automatically launched by CEF

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Python Application                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Pytonium Python Module (Cython)                      │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Core C++ Library (libpytonium_library)        │  │  │
│  │  │  ┌──────────────────────────────────────────┐  │  │  │
│  │  │  │  CEF (Chromium Embedded Framework)        │  │  │  │
│  │  │  │  ┌────────────────────────────────────┐  │  │  │  │
│  │  │  │  │  Renderer Process (Subprocess)      │  │  │  │  │
│  │  │  │  │  ┌──────────────────────────────┐  │  │  │  │  │
│  │  │  │  │  │  HTML/CSS/JS UI              │  │  │  │  │  │
│  │  │  │  │  └──────────────────────────────┘  │  │  │  │  │
│  │  │  │  └────────────────────────────────────┘  │  │  │  │
│  │  │  └──────────────────────────────────────────┘  │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Communication Flow

### Python → JavaScript
1. Python calls `pytonium.execute_javascript("someJSCode()")`
2. C++ sends message to renderer process
3. JavaScript executes in browser

### JavaScript → Python
1. JavaScript calls `Pytonium.api.myFunc()`
2. CEF V8 handler intercepts call
3. Message sent to browser process
4. C++ callback executes Python binding
5. If return value expected, promise resolved with result

## Important Files for Development

| File | Purpose |
|------|---------|
| `src/pytonium_library/pytonium_library.h` | Main C++ API header |
| `src/pytonium_library/pytonium_library.cpp` | Main C++ implementation |
| `src/pytonium_library/cef_wrapper_browser_process_handler.cc` | Browser process logic |
| `src/pytonium_library/javascript_binding.h` | Binding type definitions |
| `src/pytonium_python_framework/Pytonium/src/pytonium.pyx` | Cython Python bindings |
| `src/pytonium_library_test/main.cpp` | Example C++ usage |
| `src/pytonium_library_test/index.html` | Example HTML UI |

## Build Artifacts

After building, these files are created:

**C++ Library:**
- `cmake-build-release/src/pytonium_library/Release/pytonium_library.lib`
- `cmake-build-release/src/pytonium_library_test/Release/pytonium_library_test.exe`

**Python Extension:**
- `src/pytonium_python_framework/dist/pytonium-*.whl`
- After install: `.venv/Lib/site-packages/Pytonium/pytonium*.pyd`

**Subprocess:**
- `cmake-build-release/src/pytonium_subprocess/Release/pytonium_subprocess.exe`
- Copied to: `src/pytonium_python_framework/Pytonium/bin_win/`

## Common Development Tasks

### Adding a New C++ API Method

1. Add declaration to `pytonium_library.h`
2. Implement in `pytonium_library.cpp`
3. Add Cython binding in `pytonium.pyx`
4. Rebuild Python package

### Adding Window Controls

1. Add C++ method in `pytonium_library.h/cpp`
2. Add JavaScript binding in `main.cpp` (test) or Python
3. Call from HTML via `Pytonium.window.methodName()`

### Custom Window Features

- Frameless mode: `SetFramelessWindow(true)`
- Draggable: Handle `mousedown/mousemove/mouseup` in HTML, call C++ `DragWindow()`
- Resizable: Add resize handles in HTML, call C++ `ResizeWindow()`

## Dependencies

- **CEF**: Chromium Embedded Framework (handles browser rendering)
- **libcef_dll_wrapper**: C++ wrapper for CEF C API
- **Cython**: Generates Python C extension from .pyx files
- **CMake**: Build system
- **scikit-build**: Python packaging with CMake

## Quick Reference

**Build C++ Test App:**
```bash
cmake -B cmake-build-release -S . -DCMAKE_BUILD_TYPE=Release
cmake --build cmake-build-release --config Release
```

**Build Python Package:**
```bash
cd src/pytonium_python_framework
python -m build --wheel
pip install dist/pytonium-*.whl --force-reinstall
```

**Run Test:**
```bash
cd cmake-build-release/src/pytonium_library_test/Release
./pytonium_library_test.exe
```

## Notes for AI Assistant

- Project uses **CEF** for rendering, not a custom browser engine
- **Alloy runtime style** is used (not Chrome style) to hide Chrome UI
- Window customization is done via **Win32 API** on Windows
- Python bindings are generated with **Cython** (not pybind11)
- The **subprocess executable** is required and must be in `bin/` folder
- All CEF settings structs must have `size` field set and be zero-initialized
