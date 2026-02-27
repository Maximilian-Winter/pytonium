---
title: Changelog
---

# Changelog

All notable changes to Pytonium are documented on this page.

---

## v0.0.13 (February 2026)

This is a major feature release that adds multi-instance browser support, off-screen rendering with transparent windows, fullscreen mode, and numerous improvements to the build system and developer experience.

### Multi-Instance Browser

- **`create_browser(url, width, height)`** -- Create additional browser windows within the same process
- **`close_browser(browser_id)`** -- Close a specific browser window by ID
- **`get_browser_id()`** -- Get the browser ID of the current instance
- **`is_cef_initialized()`** -- Check whether the CEF runtime has been initialized
- **`run_pytonium_multi_async(instances)`** -- Run multiple Pytonium instances concurrently with asyncio

### Off-Screen Rendering

- **`set_osr_mode(enabled)`** -- Enable off-screen rendering for transparent window support
- Per-pixel alpha transparency via CEF's off-screen rendering pipeline
- Win32 layered windows with `UpdateLayeredWindow` compositing

### Fullscreen Mode

- **`set_fullscreen(enabled)`** -- Enter or exit fullscreen mode programmatically
- **`toggle_fullscreen()`** -- Toggle between fullscreen and windowed mode
- **`is_fullscreen()`** -- Query the current fullscreen state
- Win32 borderless fullscreen implementation with saved/restored window state

### Window Event Callbacks

- **`on_title_change(callback)`** -- Called when the page title changes
- **`on_address_change(callback)`** -- Called when the URL changes
- **`on_fullscreen_change(callback)`** -- Called when fullscreen state changes (e.g., HTML5 fullscreen API)

### Async Integration

- **`run_pytonium_async(instance)`** -- Run a single Pytonium instance within an asyncio event loop
- **`run_pytonium_multi_async(instances)`** -- Run multiple instances concurrently

### Window Control

- **`get_native_window_handle()`** -- Access the native HWND (Windows) or X11 window handle
- **`set_window_position(x, y)`** / **`get_window_position()`** -- Control window position
- **`set_window_size(w, h)`** / **`get_window_size()`** -- Control window size
- **`minimize_window()`** / **`maximize_window()`** / **`restore_window()`** -- Window state control
- **`drag_window()`** -- Initiate a native window drag operation
- **`set_frameless_window(enabled)`** -- Remove native window chrome for custom titlebar designs

### Custom Schemes and MIME Types

- **`add_custom_scheme(name, path)`** -- Register custom URL protocols for local file serving
- **`add_mime_type_mapping(extension, mime_type)`** -- Map file extensions to MIME types for custom schemes

### TypeScript Definitions

- **`generate_typescript_definitions(path)`** -- Auto-generate `.d.ts` files for bound Python functions

### Developer Experience

- GIL-safe callbacks throughout the Cython bridge (`with gil` + try/except on all 6 callback types)
- JavaScript string injection hardening via `EscapeJsString`
- Promise timeout and cleanup for bound function calls
- Comprehensive type stubs (`.pyi`) for IDE auto-completion
- Input validation and docstrings on all public methods
- Mutable default argument fixes

### Platform Improvements

- DPI awareness on Windows (per-monitor DPI support)
- Unicode path support on Windows (`GetModuleFileNameW`)
- Atomic singleton pattern for CEF initialization
- `RemoveState` guard for safe state cleanup
- Cross-platform build system improvements (`prepare_build.py` script)

### Build System

- **`prepare_build.py`** -- Unified build preparation script with `--platform`, `--dry-run`, `--verbose`, and skip options
- CMake paths cleaned up to use `${CMAKE_SOURCE_DIR}/`
- Automated subprocess copy and CEF binary staging
- Linux `.so` symbol stripping for smaller wheel size

### Supported Platforms

- Windows 11 (x86_64)
- Linux with X11 (x86_64)
- Python 3.10+

---

## Previous Versions

Pytonium was in early development prior to v0.0.13. The project history is available in the [git log](https://github.com/Maximilian-Winter/pytonium/commits/master).
