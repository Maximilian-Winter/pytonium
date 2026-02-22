# Pytonium Codebase Status Report

**Date:** 2026-02-22
**Version audited:** 0.0.13
**CEF version:** 145.0.26 (Chromium 145.0.7632.110)
**Python requirement:** >= 3.10

---

## 1. Executive Summary

Pytonium is a functional and architecturally sound framework for building Python desktop apps with HTML/CSS/JS UIs via the Chromium Embedded Framework. The C++ core, Cython bindings, and Python API are well-structured, with working examples demonstrating real-world use cases (data visualization, 3D graphics, system monitoring). However, **the codebase has significant issues that block a production release**: a path traversal vulnerability in the custom protocol handler, pervasive thread safety violations at the C++/Python boundary, no formal test suite, and a singleton-based architecture that prevents multiple window instances (a hard requirement for PytoniumShell). The CEF version (145.0.26) is current. The build system works but is fragile due to hardcoded relative paths. **Overall readiness: pre-production. Estimated effort to release-quality: 3-4 weeks.**

---

## 2. Project Structure

```
pytonium/
├── CMakeLists.txt                              # Root C++ build config (C++20)
├── pytonium_shell_architecture.md              # PytoniumShell design doc
├── how-to-build-from-source.md                 # Build instructions (excellent)
├── readme.md                                   # Project docs & feature overview
├── LICENSE                                     # Project license
├── test.d.ts                                   # Generated TypeScript definitions
│
├── src/
│   ├── pytonium_library/                       # C++ CEF Integration Layer (~3-5k LOC)
│   │   ├── pytonium_library.cpp/.h             # Main library: init, message loop, window mgmt
│   │   ├── cef_wrapper_app.cc/.h               # CEF app lifecycle
│   │   ├── cef_wrapper_client_handler.cc/.h     # Browser event handling, JS bridge
│   │   ├── cef_wrapper_client_handler_win.cc    # Windows: frameless resize, subclassing
│   │   ├── cef_wrapper_client_handler_linux.cc  # Linux: X11 title, no-op resize
│   │   ├── cef_wrapper_browser_process_handler.cc/.h  # Browser creation, binding setup
│   │   ├── cef_wrapper_render_process_handler.cc/.h   # Renderer: V8 bindings, state sync
│   │   ├── custom_protocol_scheme_handler.cc/.h # Custom URL schemes (pytonium://)
│   │   ├── javascript_binding.h                # JS<->C++ type conversion helpers
│   │   ├── javascript_bindings_handler.h        # Binding registration
│   │   ├── javascript_python_binding_handler.h  # Promise-based Python return values
│   │   ├── application_state_manager.h          # Namespace-based state store
│   │   ├── application_state_python.h           # Python state handler callbacks
│   │   ├── application_state_javascript_handler.h # JS state event dispatch
│   │   ├── application_context_menu_binding.h   # Context menu callbacks
│   │   ├── cef_value_wrapper.h                  # CEF value abstraction
│   │   ├── cef_custom_scheme.h                  # Scheme data model
│   │   ├── file_util.h                          # Binary file reading
│   │   ├── Logging.h                            # Logging utilities
│   │   ├── global_vars.h                        # Global running state
│   │   └── nlohmann/json.hpp                    # JSON library (header-only, 3rd party)
│   │
│   ├── pytonium_subprocess/                     # CEF subprocess handler
│   │   ├── CMakeLists.txt
│   │   ├── pytonium_subprocess.cc               # Windows subprocess
│   │   ├── pytonium_subprocess_linux.cc          # Linux subprocess
│   │   └── pytonium_subprocess.exe.manifest      # Windows manifest
│   │
│   ├── pytonium_library_test/                   # C++ test app (manual testing)
│   │   ├── CMakeLists.txt
│   │   ├── index_old.html                       # Test HTML page
│   │   └── radioactive.ico                      # Test icon
│   │
│   └── pytonium_python_framework/               # Python package & build
│       ├── setup.py                             # scikit-build packaging (172 lines)
│       ├── pyproject.toml                       # PEP 517 config
│       ├── setup.cfg                            # Package metadata
│       ├── MANIFEST.in                          # Distribution manifest
│       ├── generate_pyi.py                      # .pyi stub generator
│       ├── StateManagement.py                   # Python state manager class
│       └── Pytonium/
│           ├── __init__.py                      # Package init, DLL loading, binary extraction
│           ├── pytonium.pyi                     # Type stubs for IDE support
│           └── src/
│               ├── CMakeLists.txt               # Cython build config
│               ├── __init__.pyx                 # Cython bridge (626 lines)
│               ├── pytonium_library.pxd          # C++ declarations for Cython
│               ├── cef-binaries-windows/         # CEF Windows binaries + headers
│               └── cef-binaries-linux/           # CEF Linux binaries + headers
│
├── pytonium_examples/                           # 6 example applications
│   ├── pytonium_example_simple/                 # Basic binding & state demo
│   ├── pytonium_example_frameless/              # Frameless window with custom titlebar
│   ├── pytonium_example_babylon_js/             # 3D graphics via Babylon.js
│   ├── pytonium_example_line_graph/             # Chart visualization
│   ├── pytonium_example_control_center/         # System monitoring dashboard
│   └── pytonium_example_data_studio/            # Data analysis with pandas/matplotlib
│
├── cef-binaries-windows/                        # Full CEF Windows distribution
├── cef-binaries-linux/                          # Full CEF Linux distribution
├── cmake-build-debug/                           # Build artifacts (debug)
└── cmake-build-release/                         # Build artifacts (release)
```

---

## 3. Build System

### Current State

| Aspect | Status | Notes |
|--------|--------|-------|
| CMake configuration | Working | C++20, min CMake 3.19, 6 CMakeLists.txt files |
| Python packaging | Working | scikit-build + Cython, wheel generation |
| Windows build | Working | MSVC v143, Windows 11 SDK |
| Linux build | Working | GCC 10+, Ninja preferred, GTK3 required |
| macOS build | Not supported | No CMake or packaging support |
| CI/CD | **Missing** | No GitHub Actions or any automation |
| Build documentation | Excellent | `how-to-build-from-source.md` is thorough |

### Issues

1. **Fragile relative paths** — CMakeLists.txt files use `../../../` patterns extensively. Moving files breaks builds.
2. **CEF binary duplication** — CEF binaries exist in 3+ locations (root, src/framework, bin_win/bin_linux), increasing repo size and requiring manual sync.
3. **No CI/CD** — No automated builds, no test matrix, no release automation.
4. **Inconsistent CMake minimums** — Root requires 3.19, framework requires 3.5, CEF requires 3.21.
5. **Manual file copying** — setup.py manually copies CEF binaries with ZIP/LZMA compression/decompression.
6. **No environment variable overrides** — Only `RELEASE_SDIST` exists; no way to customize build paths.
7. **Commented-out code** — `src/pytonium_library/CMakeLists.txt` has ~50 lines of commented-out COPY_FILES commands.

### Recommendations

- Add GitHub Actions workflow for Windows + Linux builds
- Replace relative paths with `CMAKE_SOURCE_DIR`-based references
- Consolidate CEF binaries to a single location with symlinks
- Add build caching (ccache/sccache)
- Test against Python 3.10, 3.11, 3.12, 3.13

---

## 4. C++ Architecture & Issues

### Architecture Overview

```
Python (main thread)
    │
    ▼ Cython FFI
PytoniumLibrary (C++ singleton)
    │
    ├── CefWrapperApp → CEF lifecycle
    │   ├── CefWrapperBrowserProcessHandler → browser creation, binding setup
    │   └── CefWrapperRenderProcessHandler → V8 context, state sync
    │
    ├── CefWrapperClientHandler → window events, context menus, JS execution
    │   ├── PlatformSubclassWindow (Win) → frameless resize borders
    │   └── PlatformTitleChange (Linux) → X11 title updates
    │
    ├── CustomProtocolSchemeHandler → local file serving via custom URLs
    │
    └── ApplicationStateManager → namespace-based state store (shared_ptr)
```

**Key design decisions:**
- Single-process message loop via `CefDoMessageLoopWork()` called from Python
- JS→Python calls use IPC messages (renderer→browser process→Python callback)
- Python→JS return values use Promise pattern with request ID tracking
- State is shared via `ApplicationStateManager` (accessed from renderer + browser)

### Issues by Severity

#### CRITICAL

| # | Issue | Location | Description |
|---|-------|----------|-------------|
| 1 | **Path traversal vulnerability** | `custom_protocol_scheme_handler.cc:51` | URL path is concatenated without validation. `custom://../../etc/passwd` reads arbitrary files. |
| 2 | **No thread safety on global state** | `global_vars.h:4` | `g_IsRunning` is a plain `bool`, read/written from multiple threads without synchronization. |
| 3 | **Promise map race condition** | `javascript_python_binding_handler.h:59,92` | `promiseMap` accessed from renderer and browser threads without mutex. |
| 4 | **State manager not thread-safe** | `application_state_manager.h:234` | `namespaces` map accessed from renderer thread and JS callbacks without locks. |

#### HIGH

| # | Issue | Location | Description |
|---|-------|----------|-------------|
| 5 | **Memory leak: `new[]` without RAII** | `cef_wrapper_client_handler.cc:356,384` | `new CefValueWrapper[argsSize]` with manual `delete[]` — leaks on exception. |
| 6 | **Promise map grows unbounded** | `javascript_python_binding_handler.h:102` | No timeout/cleanup for unresolved promises. `nextRequestId++` can overflow. |
| 7 | **Singleton pattern prevents multi-instance** | `cef_wrapper_client_handler.h:28`, `cef_wrapper_browser_process_handler.cc` | Single `g_instance`, single `Browser` ref — blocks PytoniumShell. |
| 8 | **CefInitialize return value unchecked** | `pytonium_library.cpp:165` | If CEF init fails, no error handling. |
| 9 | **Browser creation failure unchecked** | `cef_wrapper_browser_process_handler.cc:174` | `CreateBrowserSync()` return not null-checked. |
| 10 | **No file size limit on custom scheme** | `custom_protocol_scheme_handler.cc:54` | Entire file loaded into RAM. A 10GB file causes OOM. |

#### MEDIUM

| # | Issue | Location | Description |
|---|-------|----------|-------------|
| 11 | Sandbox disabled | `pytonium_library.cpp:96-107` | `--no-sandbox`, `--disable-gpu-sandbox` for stability, but reduces isolation. |
| 12 | Windows path separator hardcoded | `custom_protocol_scheme_handler.cc:51` | Uses `\\` — breaks on Linux. |
| 13 | X11 assumption on Linux | `cef_wrapper_client_handler_linux.cc:3` | `cef_get_xdisplay()` fails on Wayland. |
| 14 | No DPI awareness | `pytonium_library.cpp` | Uses ANSI `GetModuleFileNameA`, no HiDPI support. |
| 15 | JS string injection in state events | `application_state_javascript_handler.h:180-184` | State values inserted into JS code via string concatenation. |

#### LOW

| # | Issue | Location | Description |
|---|-------|----------|-------------|
| 16 | Silent failures on window methods | Throughout | No error codes or callbacks when operations fail. |
| 17 | No window event callbacks | N/A | Focus, blur, resize, move events not exposed to Python. |
| 18 | DevTools window untracked | `cef_wrapper_client_handler.cc:124` | Multiple DevTools windows possible, no cleanup tracking. |

---

## 5. Python API & Issues

### Complete Public API

#### Pytonium Class

**Lifecycle:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `__init__` | `()` | Initializes instance |
| `initialize` | `(start_url: str, init_width: int, init_height: int)` | Starts CEF browser |
| `shutdown` | `()` | Shuts down CEF |
| `is_running` | `() -> bool` | Check if browser open |
| `update_message_loop` | `()` | Process CEF events (call in loop) |

**JavaScript Binding:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `bind_function_to_javascript` | `(function_to_bind, name="", javascript_object="")` | Bind single function |
| `bind_functions_to_javascript` | `(functions_to_bind: list, names=[], javascript_object="")` | Bind multiple |
| `bind_object_methods_to_javascript` | `(obj, names=[], javascript_object="")` | Bind object methods |
| `execute_javascript` | `(code: str)` | Run JS code in browser |
| `return_value_to_javascript` | `(message_id: int, value)` | Return value to JS Promise |

**State Management:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `set_state` | `(namespace: str, key: str, value)` | Set state value |
| `add_state_handler` | `(handler, namespaces: list[str])` | Subscribe to state changes |

**Window Control:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `set_frameless_window` | `(frameless: bool)` | Call before `initialize()` |
| `minimize_window` | `()` | Minimize |
| `maximize_window` | `()` | Maximize |
| `restore_window` | `()` | Restore from maximized |
| `close_window` | `()` | Close window |
| `is_maximized` | `() -> bool` | Check state |
| `drag_window` | `(delta_x: int, delta_y: int)` | Move frameless window |
| `get_window_position` | `() -> tuple` | Returns (x, y) |
| `set_window_position` | `(x: int, y: int)` | Set position |
| `get_window_size` | `() -> tuple` | Returns (width, height) |
| `set_window_size` | `(width: int, height: int)` | Set size |
| `resize_window` | `(new_width, new_height, anchor=0)` | Resize with anchor point |

**Configuration:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `set_custom_scheme` | `(scheme_id: str, root_folder: str)` | Register custom protocol |
| `add_mime_type_mapping` | `(extension: str, mime_type: str)` | Add MIME mapping |
| `set_cache_path` | `(path: str)` | Set browser cache dir |
| `set_custom_icon_path` | `(path: str)` | Set window icon |
| `load_url` | `(url: str)` | Navigate to URL |

**Context Menu:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `add_context_menu_entry` | `(func, display_name="", namespace="")` | Add single entry |
| `add_context_menu_entries` | `(funcs: list, names=[], namespace="")` | Add multiple |
| `add_context_menu_entries_from_object` | `(obj, names=[], namespace="")` | Add from object |
| `set_context_menu_namespace` | `(namespace: str)` | Switch active namespace |
| `set_show_debug_context_menu` | `(show: bool)` | Toggle debug menu |

**Other:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `generate_typescript_definitions` | `(filename: str)` | Generate .d.ts file |
| `set_subprocess_path` | `@classmethod (value)` | Set subprocess exe path |

#### Decorator

```python
@returns_value_to_javascript(return_type="any")  # "any"|"number"|"string"|"boolean"|"object"|"array"|"void"
def my_function():
    return {"Answer": 42}
```

### Python Layer Issues

| # | Issue | Severity | Description |
|---|-------|----------|-------------|
| 1 | **No thread safety at C++/Python boundary** | CRITICAL | Callbacks from C++ call Python without GIL management or mutex protection. Race conditions possible. |
| 2 | **No input validation on binding methods** | HIGH | `bind_function_to_javascript` doesn't verify callable, parameter count, or binding success. |
| 3 | **State handler interface unchecked** | MEDIUM | Only uses `hasattr(handler, 'update_state')` — no signature validation. |
| 4 | **Incomplete type hints** | MEDIUM | `callable` instead of `Callable`, missing return type annotations, `object` too vague. |
| 5 | **Missing docstrings** | MEDIUM | No docstrings on `Pytonium` class, `bind_function_to_javascript`, `set_state`, `add_state_handler`. |
| 6 | **Silent type conversion failures** | LOW | Unknown CEF types return `None` instead of raising exceptions. |
| 7 | **No bounds checking on window methods** | LOW | `set_window_position(-99999, -99999)` silently accepted. |
| 8 | **`_global_pytonium_subprocess_path`** | LOW | Module-level mutable state with no thread protection. |

---

## 6. Feature Status

| Feature | Status | Evidence |
|---------|--------|----------|
| Load local HTML files | **Working** | Examples use local file paths, custom schemes |
| Load remote URLs | **Working** | `pytonium.initialize("https://...")` |
| Bind Python functions to JavaScript | **Working** | All examples demonstrate this |
| Return values from Python to JS (Promises) | **Working** | `@returns_value_to_javascript` decorator + Promise pattern |
| Bind entire Python objects to JavaScript | **Working** | `bind_object_methods_to_javascript()` in examples |
| State management (set/get/remove, cross-lang sync) | **Working** | `set_state()`, `add_state_handler()`, JS `appState` API |
| State event subscriptions (registerForStateUpdates) | **Working** | JS `Pytonium.appState.registerForStateUpdates()` |
| Custom protocol schemes | **Working** | `set_custom_scheme("custom", "/path")` — but has path traversal bug |
| Custom context menus | **Working** | Namespace-based context menu system |
| Execute JavaScript from Python | **Working** | `execute_javascript(code)` |
| Frameless window mode | **Working** | `set_frameless_window(True)` with custom titlebar |
| Custom window icon | **Working** | `set_custom_icon_path()` |
| TypeScript definition generation | **Working** | `generate_typescript_definitions()` |
| Window controls (minimize, maximize, close) | **Working** | Full API available |
| Draggable title bar in frameless mode | **Working** | `drag_window(delta_x, delta_y)` |
| Resizable frameless windows (drag edges/corners) | **Working** | Win32 subclassing for resize borders (Windows only) |
| Linux support | **Partially working** | Builds and runs, but: no frameless resize, X11-only (no Wayland), path separator issues |

---

## 7. PytoniumShell Readiness

### 1. Multiple Windows

**Current:** Not supported. Architecture enforces single instance via singletons (`g_instance`, single `Browser` ref).

**Required changes:**
- Replace `CefWrapperClientHandler::g_instance` with instance map keyed by browser ID
- Replace single `Browser` CefRefPtr with `std::map<int, CefRefPtr<CefBrowser>>`
- Instance-aware message routing for bindings and state
- Thread-safe instance lookup

**Difficulty:** Hard (3-5 days). Fundamental refactor of singleton pattern.

### 2. HWND Access

**Current:** Available internally (`browser->GetHost()->GetWindowHandle()`) but not exposed to Python.

**Required changes:** Add `get_hwnd()` method to `PytoniumLibrary`, expose through Cython.

**Difficulty:** Easy (1-2 hours).

### 3. Transparent Backgrounds

**Current:** Not supported. Frameless windows are opaque. No off-screen rendering configured.

**Required changes:**
- Enable CEF off-screen rendering with alpha channel
- Configure `CefWindowInfo` with `SetAsWindowless()` + transparent flag
- Compositor integration on Windows (layered windows with per-pixel alpha)

**Difficulty:** Medium-Hard (2-3 days). CEF supports this, but integration is non-trivial.

### 4. Window Positioning

**Current:** Good support. `get/set_window_position()`, `get/set_window_size()`, `resize_window()`, `drag_window()` all implemented (Windows only).

**Required changes:** Add position constraints (min/max size), position persistence, multi-monitor awareness.

**Difficulty:** Easy (already mostly done).

### 5. Window Events

**Current:** Missing. No focus, blur, resize, move, or close events exposed to Python or JavaScript.

**Required changes:**
- Integrate `CefDisplayHandler` callbacks
- Add Python callback registration for window events
- Forward events to JavaScript via state or custom events

**Difficulty:** Medium (1-2 days).

### 6. Process Model

**Current:** CEF multi-process with sandbox disabled. Separate `pytonium_subprocess` executable handles renderer processes. GPU sandbox disabled due to stability issues.

**Impact on PytoniumShell:** Multiple Pytonium instances would share a single CEF initialization (browser process) but each gets its own renderer process. This is CEF's intended model. The main blocker is the singleton architecture, not the process model.

**Difficulty:** N/A (process model is fine; singleton refactor is the real work).

### Overall PytoniumShell Readiness: **~40%**

**Blocking items:** Multi-instance support, transparent backgrounds, window events.
**Estimated timeline to ready:** 2-3 weeks of focused development.

---

## 8. Code Quality

### Lines of Code (approximate)

| Category | Files | Lines | Notes |
|----------|-------|-------|-------|
| C++ (.cc, .h) | ~25 | ~4,500 | Core library (excl. nlohmann JSON) |
| Cython (.pyx, .pxd) | 3 | ~740 | Python-C++ bridge |
| Python (.py) | ~15 | ~1,500 | Framework + examples |
| HTML/CSS/JS | ~10 | ~2,000 | Example UIs (excl. Babylon.js) |
| Build scripts | ~8 | ~600 | CMakeLists.txt + setup.py |
| **Total project code** | **~61** | **~9,340** | Excluding 3rd party libs and CEF |

### TODO/FIXME/HACK Comments

Only **1 project-owned TODO** found:
- `cef_wrapper_client_handler_linux.cc:40`: `// TODO(erg): This is technically wrong. So XStoreName and friends expect...` — inherited from CEF example code.

No FIXME or HACK comments in project code (some exist in 3rd party Babylon.js).

### Code Organization

**Strengths:**
- Clean separation: C++ core / Cython bridge / Python API / Examples
- Platform-specific code properly separated into `_win.cc` / `_linux.cc` files
- Header-only design for many components (simple to integrate)
- Good use of CEF's `CefRefPtr` smart pointers

**Weaknesses:**
- All C++ headers in a flat directory (no subdirectories for organization)
- Singleton pattern prevents testability and multi-instance use
- No abstract interfaces (hard to mock for testing)
- `nlohmann/json.hpp` vendored directly (should use package manager or git submodule)

### Dead Code

- Deleted from staging: `src/pytonium_python_framework/Pytonium/src/pytonium_subprocess/` (4 files) — subprocess source consolidated
- `src/pytonium_library/CMakeLists.txt` has ~50 commented-out `COPY_FILES` commands
- `src/pytonium_library_test/index_old.html` — old test page

### Security Concerns

| Concern | Severity | Description |
|---------|----------|-------------|
| **Path traversal** | CRITICAL | `custom_protocol_scheme_handler.cc:51` — URL paths not validated against directory escape |
| **JS injection via state** | MEDIUM | `application_state_javascript_handler.h:180` — state values inserted into JS via string concatenation |
| **Unvalidated JS execution** | MEDIUM | `execute_javascript()` — if user input flows here, XSS-style attacks possible |
| **DLL search order** | MEDIUM | Subprocess search includes CWD — DLL hijacking risk from untrusted folders |
| **Sandbox disabled** | MEDIUM | `--no-sandbox` reduces OS-level isolation |
| **No CSP headers** | LOW | Custom scheme responses don't set Content-Security-Policy |

### Test Coverage

**Formal tests:** None. No unit tests, no integration tests, no CI test matrix.
**Manual testing:** `pytonium_library_test/` C++ test app + `test_resize_simple.py` for frameless resize.
**Example-based validation:** 6 example apps serve as smoke tests.

---

## 9. Recommended Actions

### Must Fix (blockers for release)

1. **Fix path traversal in custom protocol handler**
   - File: `custom_protocol_scheme_handler.cc:51`
   - Action: Canonicalize paths, validate they stay within content root
   - Effort: 1-2 hours

2. **Make `g_IsRunning` thread-safe**
   - File: `global_vars.h:4`
   - Action: Change to `std::atomic<bool>`
   - Effort: 15 minutes

3. **Fix `new[]` memory leak**
   - File: `cef_wrapper_client_handler.cc:356,384`
   - Action: Replace with `std::vector<CefValueWrapper>`
   - Effort: 30 minutes

4. **Check CefInitialize return value**
   - File: `pytonium_library.cpp:165`
   - Action: Check return, log error, return failure to Python
   - Effort: 30 minutes

5. **Fix Linux path separator**
   - File: `custom_protocol_scheme_handler.cc:51`
   - Action: Use `std::filesystem::path` operator `/` instead of `"\\"` concatenation
   - Effort: 15 minutes

### Should Fix (important but not blocking)

6. **Add thread safety to state manager** — mutex-protect `namespaces` map
7. **Add thread safety to promise map** — mutex or move to UI-thread-only access
8. **Add input validation to Python binding methods** — check callable, verify signatures
9. **Add docstrings to all public Python API methods**
10. **Fix type hints** — use proper `Callable`, `tuple[int, int]` annotations
11. **Add GIL management to Cython callbacks** — ensure GIL held when entering Python from C++
12. **Add file size limit to custom scheme handler** — prevent OOM from large files
13. **Validate JS string injection in state events** — escape/sanitize state values before JS insertion
14. **Add CI/CD** — GitHub Actions for Windows + Linux wheel builds
15. **Add basic unit tests** — at minimum for Python API and state management
16. **Generate and distribute .pyi stubs** — improve IDE experience

### Nice to Have (improvements for later)

17. **Refactor singletons for multi-instance** — required for PytoniumShell
18. **Expose HWND to Python** — `get_hwnd()` method
19. **Add window event callbacks** — focus, blur, resize, move events
20. **Add transparent background support** — CEF off-screen rendering with alpha
21. **Add Wayland support on Linux** — remove X11 assumption
22. **Add DPI awareness** — use Unicode APIs, handle HiDPI scaling
23. **Add promise timeout/cleanup** — prevent unbounded map growth
24. **Consolidate CEF binaries** — single location, no duplication
25. **Replace relative `../../../` paths in CMake** — use `CMAKE_SOURCE_DIR`
26. **Add macOS support** — CEF supports it, build system doesn't
27. **Add async/await Python support** — integrate with asyncio event loop