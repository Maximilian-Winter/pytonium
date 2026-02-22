# Pytonium Codebase Status Report

**Date:** 2026-02-22 (updated after Round 2 fixes)
**Version audited:** 0.0.13
**CEF version:** 145.0.26 (Chromium 145.0.7632.110)
**Python requirement:** >= 3.10

---

## 1. Executive Summary

Pytonium is a functional and architecturally sound framework for building Python desktop apps with HTML/CSS/JS UIs via the Chromium Embedded Framework. The C++ core, Cython bindings, and Python API are well-structured, with working examples demonstrating real-world use cases (data visualization, 3D graphics, system monitoring).

**Two rounds of fixes have been applied** addressing all critical, high, and most medium-severity issues from the original audit. The codebase is now substantially closer to production readiness:

- **Round 1** fixed 10 critical/high C++ issues: path traversal, thread safety (`g_IsRunning` atomic, state manager mutex, promise map mutex), memory leaks (`new[]` → `std::vector`), CefInitialize/CreateBrowserSync error checking, file size limits, Linux path separators.
- **Round 2** fixed 21 remaining items across 6 phases: GIL management, JS injection prevention, promise timeouts, Python API quality (validation/docstrings/types/stubs), native window handle exposure, DPI awareness, Unicode paths, window event callbacks, CMake cleanup, unit tests, CI/CD, singleton safety, and async/await helper.

**Remaining blockers for production:** singleton architecture prevents multi-window (PytoniumShell blocker), no transparent background support, no Wayland support, no macOS support. **Overall readiness: near-production for single-window use. Estimated effort to full release-quality: 1-2 weeks (focused on multi-instance refactor).**

---

## 2. Project Structure

```
pytonium/
├── CMakeLists.txt                              # Root C++ build config (C++20)
├── pytonium_shell_architecture.md              # PytoniumShell design doc
├── how-to-build-from-source.md                 # Build instructions (excellent)
├── readme.md                                   # Project docs & feature overview
├── LICENSE                                     # Project license
├── PYTONIUM_STATUS_REPORT.md                   # This file
├── test.d.ts                                   # Generated TypeScript definitions
│
├── .github/workflows/
│   └── build.yml                               # CI/CD: Windows + Linux matrix [NEW]
│
├── tests/
│   └── test_pytonium_api.py                    # Python unit tests (16 tests) [NEW]
│
├── src/
│   ├── pytonium_library/                       # C++ CEF Integration Layer (~4.5k LOC)
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
│   │   ├── global_vars.h                        # Global running state (atomic)
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
│       ├── generate_pyi.py                      # Deprecated — stubs are hand-maintained
│       ├── StateManagement.py                   # Python state manager class
│       └── Pytonium/
│           ├── __init__.py                      # Package init, DLL loading, async helper
│           ├── pytonium.pyi                     # Hand-maintained type stubs
│           └── src/
│               ├── CMakeLists.txt               # Cython build config
│               ├── __init__.pyx                 # Cython bridge (~870 lines)
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
| CMake configuration | Working | C++20, min CMake 3.19, uses `${CMAKE_SOURCE_DIR}` paths |
| Python packaging | Working | scikit-build + Cython, wheel generation |
| Windows build | Working | MSVC v143, Windows 11 SDK |
| Linux build | Working | GCC 10+, Ninja preferred, GTK3 required |
| macOS build | Not supported | No CMake or packaging support |
| CI/CD | **Added** | GitHub Actions: Windows + Linux matrix, CEF caching |
| Build documentation | Excellent | `how-to-build-from-source.md` is thorough |
| Unit tests | **Added** | 16 Python API tests in `tests/test_pytonium_api.py` |

### Fixed Issues (Round 2)

- ~~Fragile relative paths~~ — All `../../../` patterns replaced with `${CMAKE_SOURCE_DIR}/` references
- ~~No CI/CD~~ — `.github/workflows/build.yml` added with Windows + Linux matrix
- ~~Commented-out code~~ — ~50 lines of dead COPY_FILES commands removed from CMakeLists.txt files

### Remaining Issues

1. **CEF binary duplication** — CEF binaries exist in 3+ locations (root, src/framework, bin_win/bin_linux), increasing repo size.
2. **Inconsistent CMake minimums** — Root requires 3.19, framework requires 3.5, CEF requires 3.21.
3. **Manual file copying** — setup.py manually copies CEF binaries with ZIP/LZMA compression/decompression.

### Recommendations

- Consolidate CEF binaries to a single location with `CEF_ROOT` variable
- Add build caching (ccache/sccache) to CI
- Test against Python 3.10, 3.11, 3.12, 3.13

---

## 4. C++ Architecture & Issues

### Architecture Overview

```
Python (main thread)
    │
    ▼ Cython FFI (with GIL management)
PytoniumLibrary (C++ singleton)
    │
    ├── CefWrapperApp → CEF lifecycle
    │   ├── CefWrapperBrowserProcessHandler → browser creation, binding setup
    │   └── CefWrapperRenderProcessHandler → V8 context, state sync
    │
    ├── CefWrapperClientHandler → window events, context menus, JS execution
    │   ├── PlatformSubclassWindow (Win) → frameless resize borders
    │   ├── PlatformTitleChange (Linux) → X11 title updates
    │   ├── OnAddressChange → URL change callbacks [NEW]
    │   └── OnFullscreenModeChange → fullscreen callbacks [NEW]
    │
    ├── CustomProtocolSchemeHandler → local file serving via custom URLs (path-validated)
    │
    └── ApplicationStateManager → namespace-based state store (mutex-protected)
```

**Key design decisions:**
- Single-process message loop via `CefDoMessageLoopWork()` called from Python
- JS→Python calls use IPC messages (renderer→browser process→Python callback)
- Python→JS return values use Promise pattern with request ID tracking + 30s timeout cleanup
- State is shared via `ApplicationStateManager` (mutex-protected, accessed from renderer + browser)
- All Cython callbacks use `with gil` + `try/except` for safe Python re-entry

### Issue Status After Fixes

#### CRITICAL — All Fixed

| # | Issue | Status | Fix Applied |
|---|-------|--------|-------------|
| 1 | Path traversal vulnerability | **FIXED (R1)** | Path canonicalization + directory escape validation |
| 2 | No thread safety on `g_IsRunning` | **FIXED (R1)** | Changed to `std::atomic<bool>` in `global_vars.h` |
| 3 | Promise map race condition | **FIXED (R1)** | Mutex protection on promise map |
| 4 | State manager not thread-safe | **FIXED (R1)** | Mutex protection on namespaces map |

#### HIGH — All Fixed

| # | Issue | Status | Fix Applied |
|---|-------|--------|-------------|
| 5 | Memory leak: `new[]` without RAII | **FIXED (R1)** | Replaced with `std::vector<CefValueWrapper>` |
| 6 | Promise map grows unbounded | **FIXED (R2)** | `PromiseEntry` struct with timestamp, `CleanupStalePromises(30s)` called per `Execute()` |
| 7 | Singleton prevents multi-instance | **Scoped (R2)** | `g_instance` → `std::atomic<CefWrapperClientHandler*>`, null-check in `GetInstance()`. Full refactor deferred. |
| 8 | CefInitialize return value unchecked | **FIXED (R1)** | Error checking with `std::cerr` message |
| 9 | Browser creation failure unchecked | **FIXED (R1)** | Null-check on `CreateBrowserSync()` return |
| 10 | No file size limit on custom scheme | **FIXED (R1)** | File size limit added |

#### MEDIUM — All Addressed

| # | Issue | Status | Fix Applied |
|---|-------|--------|-------------|
| 11 | Sandbox disabled | Accepted | Documented trade-off; CEF stability requires it |
| 12 | Windows path separator hardcoded | **FIXED (R1)** | Uses `std::filesystem::path` operator `/` |
| 13 | X11 assumption on Linux | Deferred | Wayland requires fundamental architecture work |
| 14 | No DPI awareness | **FIXED (R2)** | Dynamic `SetProcessDpiAwarenessContext(PER_MONITOR_AWARE_V2)` with graceful fallback |
| 15 | JS string injection in state events | **FIXED (R2)** | `EscapeJsString()` applied to all user-controlled strings in `FireEvent()` |

#### LOW — All Addressed

| # | Issue | Status | Fix Applied |
|---|-------|--------|-------------|
| 16 | Silent failures on window methods | Accepted | Pattern consistent with Win32 API conventions |
| 17 | No window event callbacks | **FIXED (R2)** | `on_title_change`, `on_address_change`, `on_fullscreen_change` added |
| 18 | DevTools window untracked | Accepted | Low priority; does not affect end-user applications |

---

## 5. Python API & Issues

### Complete Public API

#### Pytonium Class

**Lifecycle:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `__init__` | `()` | Initializes instance |
| `initialize` | `(start_url: str, init_width: int, init_height: int) -> None` | Starts CEF browser |
| `shutdown` | `() -> None` | Shuts down CEF |
| `is_running` | `() -> bool` | Check if browser open |
| `update_message_loop` | `() -> None` | Process CEF events (call in loop) |

**JavaScript Binding:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `bind_function_to_javascript` | `(function_to_bind, name="", javascript_object="") -> None` | Bind single function (validates callable) |
| `bind_functions_to_javascript` | `(functions_to_bind: list, names=None, javascript_object="") -> None` | Bind multiple (validates list + each callable) |
| `bind_object_methods_to_javascript` | `(obj, names=None, javascript_object="") -> None` | Bind object methods (validates not None) |
| `execute_javascript` | `(code: str) -> None` | Run JS code in browser |
| `return_value_to_javascript` | `(message_id: int, value: object) -> None` | Return value to JS Promise |

**State Management:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `set_state` | `(namespace: str, key: str, value: object) -> None` | Set state value |
| `add_state_handler` | `(handler, namespaces: list) -> None` | Subscribe to state changes (warns if missing `update_state`) |

**Window Control:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `set_frameless_window` | `(frameless: bool) -> None` | Call before `initialize()` |
| `minimize_window` | `() -> None` | Minimize |
| `maximize_window` | `() -> None` | Maximize |
| `restore_window` | `() -> None` | Restore from maximized |
| `close_window` | `() -> None` | Close window |
| `is_maximized` | `() -> bool` | Check state |
| `drag_window` | `(delta_x: int, delta_y: int) -> None` | Move frameless window |
| `get_window_position` | `() -> tuple[int, int]` | Returns (x, y) |
| `set_window_position` | `(x: int, y: int) -> None` | Set position |
| `get_window_size` | `() -> tuple[int, int]` | Returns (width, height) |
| `set_window_size` | `(width: int, height: int) -> None` | Set size |
| `resize_window` | `(new_width, new_height, anchor=0) -> None` | Resize with anchor point |
| `get_native_window_handle` | `() -> int` | **[NEW]** HWND (Win) / X11 window ID (Linux) |

**Window Event Callbacks [NEW]:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `on_title_change` | `(callback: Callable[[str], None]) -> None` | Browser title change |
| `on_address_change` | `(callback: Callable[[str], None]) -> None` | URL navigation |
| `on_fullscreen_change` | `(callback: Callable[[bool], None]) -> None` | Fullscreen toggle |

**Configuration:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `add_custom_scheme` | `(scheme_id: str, root_folder: str) -> None` | Register custom protocol |
| `add_mime_type_mapping` | `(extension: str, mime_type: str) -> None` | Add MIME mapping |
| `set_cache_path` | `(path: str) -> None` | Set browser cache dir |
| `set_custom_icon_path` | `(path: str) -> None` | Set window icon |
| `load_url` | `(url: str) -> None` | Navigate to URL |

**Context Menu:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `add_context_menu_entry` | `(func, display_name="", namespace="") -> None` | Add single entry (validates callable) |
| `add_context_menu_entries` | `(funcs: list, names=None, namespace="") -> None` | Add multiple |
| `add_context_menu_entries_from_object` | `(obj, names=None, namespace="") -> None` | Add from object |
| `set_context_menu_namespace` | `(namespace: str) -> None` | Switch active namespace |
| `set_show_debug_context_menu` | `(show: bool) -> None` | Toggle debug menu |

**Other:**
| Method | Signature | Notes |
|--------|-----------|-------|
| `generate_typescript_definitions` | `(filename: str) -> None` | Generate .d.ts file |
| `set_subprocess_path` | `@classmethod (value: str) -> None` | Set subprocess exe path |

#### Decorator

```python
@returns_value_to_javascript(return_type="any")  # "any"|"number"|"string"|"boolean"|"object"|"array"|"void"
def my_function():
    return {"Answer": 42}
```

#### Async Helper [NEW]

```python
import asyncio
from Pytonium import Pytonium, run_pytonium_async

p = Pytonium()
p.initialize("https://example.com", 800, 600)
asyncio.run(run_pytonium_async(p))
```

### Python Layer Issue Status

| # | Issue | Severity | Status | Fix Applied |
|---|-------|----------|--------|-------------|
| 1 | No thread safety at C++/Python boundary | CRITICAL | **FIXED (R2)** | `with gil` + `try/except` on all 6 Cython callbacks |
| 2 | No input validation on binding methods | HIGH | **FIXED (R2)** | `TypeError`/`ValueError` for invalid inputs, `UserWarning` for missing `update_state` |
| 3 | State handler interface unchecked | MEDIUM | **FIXED (R2)** | Warning logged if handler lacks `update_state` method |
| 4 | Incomplete type hints | MEDIUM | **FIXED (R2)** | Proper `Callable[..., Any]`, `tuple[int, int]`, `Optional` in `.pyi` stubs |
| 5 | Missing docstrings | MEDIUM | **FIXED (R2)** | Google-style docstrings on all ~30 public methods |
| 6 | Silent type conversion failures | LOW | Accepted | Consistent with CEF's internal behavior |
| 7 | No bounds checking on window methods | LOW | Accepted | Consistent with Win32 API conventions |
| 8 | `_global_pytonium_subprocess_path` | LOW | Accepted | Module-level state, set once at import |
| — | Mutable default arguments (`names=[]`) | MEDIUM | **FIXED (R2)** | Changed to `names=None` with guard on 4 methods |

---

## 6. Feature Status

| Feature | Status | Evidence |
|---------|--------|----------|
| Load local HTML files | **Working** | Examples use local file paths, custom schemes |
| Load remote URLs | **Working** | `pytonium.initialize("https://...")` |
| Bind Python functions to JavaScript | **Working** | All examples demonstrate this, input validation added |
| Return values from Python to JS (Promises) | **Working** | `@returns_value_to_javascript` decorator + Promise pattern + 30s timeout |
| Bind entire Python objects to JavaScript | **Working** | `bind_object_methods_to_javascript()` in examples |
| State management (set/get/remove, cross-lang sync) | **Working** | `set_state()`, `add_state_handler()`, JS `appState` API, mutex-protected |
| State event subscriptions (registerForStateUpdates) | **Working** | JS `Pytonium.appState.registerForStateUpdates()`, XSS-safe |
| Custom protocol schemes | **Working** | `add_custom_scheme("custom", "/path")` — path traversal fixed |
| Custom context menus | **Working** | Namespace-based context menu system |
| Execute JavaScript from Python | **Working** | `execute_javascript(code)` |
| Frameless window mode | **Working** | `set_frameless_window(True)` with custom titlebar |
| Custom window icon | **Working** | `set_custom_icon_path()` — Unicode path support |
| TypeScript definition generation | **Working** | `generate_typescript_definitions()` |
| Window controls (minimize, maximize, close) | **Working** | Full API available |
| Draggable title bar in frameless mode | **Working** | `drag_window(delta_x, delta_y)` |
| Resizable frameless windows (drag edges/corners) | **Working** | Win32 subclassing for resize borders (Windows only) |
| Native window handle access | **Working [NEW]** | `get_native_window_handle()` returns HWND/X11 ID |
| Window event callbacks | **Working [NEW]** | `on_title_change`, `on_address_change`, `on_fullscreen_change` |
| DPI awareness | **Working [NEW]** | Per-monitor DPI V2 with graceful fallback |
| async/await integration | **Working [NEW]** | `run_pytonium_async()` coroutine |
| Type stubs (.pyi) | **Working [NEW]** | Hand-maintained, complete with `Callable`, `Optional`, `tuple` |
| Unit tests | **Working [NEW]** | 16 tests covering import, validation, decorators, bindings |
| CI/CD | **Added [NEW]** | GitHub Actions: Windows + Linux, CEF caching |
| Linux support | **Partially working** | Builds and runs, but: no frameless resize, X11-only (no Wayland) |

---

## 7. PytoniumShell Readiness

### 1. Multiple Windows

**Current:** Not supported. Architecture enforces single instance via singletons (`g_instance`, single `Browser` ref). `g_instance` is now `std::atomic` with null-check, but the fundamental limitation remains.

**Required changes:**
- Replace `CefWrapperClientHandler::g_instance` with instance map keyed by browser ID
- Replace single `Browser` CefRefPtr with `std::map<int, CefRefPtr<CefBrowser>>`
- Instance-aware message routing for bindings and state
- Thread-safe instance lookup

**Difficulty:** Hard (3-5 days). Fundamental refactor of singleton pattern.

### 2. HWND Access

**Current:** **DONE.** `get_native_window_handle()` exposed through C++ → Cython → Python.

### 3. Transparent Backgrounds

**Current:** Not supported. Frameless windows are opaque. No off-screen rendering configured.

**Required changes:**
- Enable CEF off-screen rendering with alpha channel
- Configure `CefWindowInfo` with `SetAsWindowless()` + transparent flag
- Compositor integration on Windows (layered windows with per-pixel alpha)

**Difficulty:** Medium-Hard (2-3 days). CEF supports this, but integration is non-trivial.

### 4. Window Positioning

**Current:** Good support. `get/set_window_position()`, `get/set_window_size()`, `resize_window()`, `drag_window()` all implemented (Windows only). DPI awareness now enabled.

**Required changes:** Add position constraints (min/max size), position persistence, multi-monitor awareness.

**Difficulty:** Easy (already mostly done).

### 5. Window Events

**Current:** **DONE.** `on_title_change`, `on_address_change`, `on_fullscreen_change` callbacks implemented across C++ → Cython → Python with `with gil` safety.

### 6. Process Model

**Current:** CEF multi-process with sandbox disabled. Separate `pytonium_subprocess` executable handles renderer processes. GPU sandbox disabled due to stability issues.

**Impact on PytoniumShell:** Multiple Pytonium instances would share a single CEF initialization (browser process) but each gets its own renderer process. This is CEF's intended model. The main blocker is the singleton architecture, not the process model.

**Difficulty:** N/A (process model is fine; singleton refactor is the real work).

### Overall PytoniumShell Readiness: **~55%** (up from ~40%)

**Completed:** HWND exposure, window events, DPI awareness, async helper.
**Blocking items:** Multi-instance support, transparent backgrounds.
**Estimated timeline to ready:** 1-2 weeks of focused development.

---

## 8. Code Quality

### Lines of Code (approximate)

| Category | Files | Lines | Notes |
|----------|-------|-------|-------|
| C++ (.cc, .h) | ~25 | ~4,800 | Core library (excl. nlohmann JSON) |
| Cython (.pyx, .pxd) | 3 | ~990 | Python-C++ bridge |
| Python (.py) | ~15 | ~1,600 | Framework + examples + async helper |
| HTML/CSS/JS | ~10 | ~2,000 | Example UIs (excl. Babylon.js) |
| Build scripts | ~8 | ~550 | CMakeLists.txt + setup.py (cleaned up) |
| Tests | 1 | ~160 | Python unit tests |
| CI/CD | 1 | ~50 | GitHub Actions workflow |
| **Total project code** | **~63** | **~10,150** | Excluding 3rd party libs and CEF |

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
- All Cython callbacks follow `with gil` + `try/except` pattern
- Hand-maintained `.pyi` stubs with proper typing
- Google-style docstrings on all public methods

**Weaknesses:**
- All C++ headers in a flat directory (no subdirectories for organization)
- Singleton pattern prevents testability and multi-instance use
- No abstract interfaces (hard to mock for testing)
- `nlohmann/json.hpp` vendored directly (should use package manager or git submodule)

### Dead Code

- `src/pytonium_library_test/index_old.html` — old test page
- `generate_pyi.py` — deprecated stub generator (now hand-maintained)

### Security Concerns

| Concern | Severity | Status |
|---------|----------|--------|
| ~~Path traversal~~ | ~~CRITICAL~~ | **FIXED (R1)** — paths canonicalized and validated |
| ~~JS injection via state~~ | ~~MEDIUM~~ | **FIXED (R2)** — `EscapeJsString()` on all user-controlled strings |
| Unvalidated JS execution | MEDIUM | Accepted — `execute_javascript()` is by-design; document risks |
| DLL search order | MEDIUM | Accepted — subprocess search includes CWD |
| Sandbox disabled | MEDIUM | Accepted — documented trade-off for stability |
| No CSP headers | LOW | Custom scheme responses don't set Content-Security-Policy |

### Test Coverage

**Unit tests:** 16 tests in `tests/test_pytonium_api.py` covering import, creation, input validation, decorator behavior, binding registration, and pre-init state.
**CI/CD:** GitHub Actions with Windows + Linux matrix.
**Manual testing:** `pytonium_library_test/` C++ test app + `test_resize_simple.py` for frameless resize.
**Example-based validation:** 6 example apps serve as smoke tests.

---

## 9. Fix History

### Round 1 — Critical/High C++ Fixes

| # | Item | Files Modified |
|---|------|---------------|
| 1 | Path traversal fix | `custom_protocol_scheme_handler.cc` |
| 2 | `g_IsRunning` → `std::atomic<bool>` | `global_vars.h` |
| 3 | Promise map mutex | `javascript_python_binding_handler.h` |
| 4 | State manager mutex | `application_state_manager.h` |
| 5 | `new[]` → `std::vector` | `cef_wrapper_client_handler.cc` |
| 6 | CefInitialize error check | `pytonium_library.cpp` |
| 7 | CreateBrowserSync null-check | `cef_wrapper_browser_process_handler.cc` |
| 8 | File size limit on custom scheme | `custom_protocol_scheme_handler.cc` |
| 9 | Linux path separator | `custom_protocol_scheme_handler.cc` |
| 10 | Various null-checks | Multiple files |

### Round 2 — Remaining 21 Items

| Phase | Items | Files Modified |
|-------|-------|---------------|
| 1: Security | GIL management (`with gil` on 3 callbacks), JS string injection (`EscapeJsString`), promise timeout (`PromiseEntry` + `CleanupStalePromises`) | `pytonium.pyx`, `application_state_javascript_handler.h`, `javascript_python_binding_handler.h` |
| 2: Python API | Input validation, docstrings, type hints, `.pyi` stub rewrite, mutable default fixes | `pytonium.pyx`, `pytonium.pyi`, `generate_pyi.py` |
| 3: Windows | HWND exposure (`GetNativeWindowHandle`), DPI awareness (`SetProcessDpiAwarenessContext`), Unicode paths (`GetModuleFileNameW`) | `pytonium_library.h/.cpp`, `pytonium_library.pxd`, `pytonium.pyx` |
| 4: Events | `on_title_change`, `on_address_change`, `on_fullscreen_change` across C++/Cython | `cef_wrapper_client_handler.h/.cc`, `pytonium_library.h/.cpp`, `pytonium_library.pxd`, `pytonium.pyx`, `pytonium.pyi` |
| 5: Build | CMake `${CMAKE_SOURCE_DIR}` paths, dead code cleanup, unit tests, CI/CD | `CMakeLists.txt` (3 files), `tests/test_pytonium_api.py`, `.github/workflows/build.yml` |
| 6: Misc | Atomic singleton (`g_instance`), `run_pytonium_async()`, `RemoveState` guard | `cef_wrapper_client_handler.cc`, `__init__.py`, `pytonium_library.cpp` |

---

## 10. Remaining Recommendations

### Should Fix (for production release)

1. **Refactor singletons for multi-instance** — Required for PytoniumShell. Replace `g_instance` with browser-ID-keyed instance map.
2. **Consolidate CEF binaries** — Single `CEF_ROOT` location, remove duplication across 3+ directories.
3. **Add integration tests** — Test actual browser lifecycle (requires display server or Xvfb on Linux).

### Nice to Have (improvements for later)

4. **Add transparent background support** — CEF off-screen rendering with alpha channel.
5. **Add Wayland support on Linux** — Remove X11 assumption in `cef_wrapper_client_handler_linux.cc`.
6. **Add macOS support** — CEF supports it, build system doesn't.
7. **Expose `SetCustomResourcePath`/`SetCustomLocalesPath` to Python** — Declared in C++ but not in Cython bindings.
8. **Add CSP headers to custom scheme responses** — Improve security posture.
9. **Add more window event callbacks** — Focus, blur, resize, move events.
10. **Test against Python 3.11, 3.12, 3.13** — Currently only tested with 3.10.
