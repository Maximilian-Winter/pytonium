# Pytonium Codebase Status Report — Instructions for Claude Code

## Objective

Perform a comprehensive audit of the Pytonium codebase to assess its current state, identify issues, and determine readiness for a new release. The end goal is to prepare Pytonium for both a pip package update and as the foundation for PytoniumShell (a desktop widget framework).

---

## Step 1: Repository Overview

- Map out the full directory structure (all files, not just top-level)
- Identify the main components:
  - C++ CEF integration layer (the native library)
  - Python bindings / wrapper (`Pytonium` class and related)
  - Build system (CMake files, build scripts)
  - Examples
  - Tests (if any)
- Note the Python version requirements and any pinned dependency versions
- Check the CEF version being used — is it current or outdated?

**Output:** A tree of the project structure with a brief description of what each major file/directory does.

---

## Step 2: Build System Health

- Read all CMakeLists.txt files and build scripts
- Check if the build process is documented and reproducible
- Identify any hardcoded paths, platform-specific assumptions, or fragile build steps
- Verify the pip packaging setup (setup.py / pyproject.toml / setup.cfg) — is it correctly configured for distribution?
- Check if both Windows and Linux builds are properly handled
- Note any CI/CD configuration (GitHub Actions, etc.) or lack thereof

**Output:** List of build system issues, missing configurations, and recommendations.

---

## Step 3: C++ Layer Audit

- Read through all C++ source files
- Document the CEF integration architecture:
  - How is the browser process created and managed?
  - How are frameless windows implemented?
  - How does the JS ↔ C++ ↔ Python bridge work?
  - How is the message loop handled?
  - How are custom protocol schemes registered?
- Identify:
  - Any deprecated CEF API usage
  - Memory management concerns (leaks, dangling pointers, missing cleanup)
  - Thread safety issues (CEF is multi-process and multi-threaded)
  - Error handling gaps
  - Platform-specific code that might need attention

**Output:** Architecture summary of the C++ layer, with a list of issues ranked by severity.

---

## Step 4: Python Layer Audit

- Read all Python source files
- Document the public API surface:
  - All methods on the `Pytonium` class
  - The `returns_value_to_javascript` decorator
  - State management API
  - Context menu API
  - Any other public interfaces
- Check for:
  - API consistency and naming conventions
  - Missing error handling or validation
  - Type hints (present? consistent?)
  - Docstrings (present? accurate?)
  - Any Python 3.10/3.11/3.12+ compatibility issues
  - Thread safety in the Python ↔ C++ boundary

**Output:** Full public API listing with notes on completeness, consistency, and issues.

---

## Step 5: Feature Completeness Check

Cross-reference the README/documentation claims against the actual implementation. For each advertised feature, verify it actually works in the code:

- [ ] Load local HTML files
- [ ] Load remote URLs
- [ ] Bind Python functions to JavaScript
- [ ] Return values from Python to JavaScript (Promises)
- [ ] Bind entire Python objects to JavaScript
- [ ] State management (set/get/remove state, cross-language sync)
- [ ] State event subscriptions (registerForStateUpdates)
- [ ] Custom protocol schemes
- [ ] Custom context menus
- [ ] Execute JavaScript from Python
- [ ] Frameless window mode
- [ ] Custom window icon
- [ ] TypeScript definition generation
- [ ] Window controls (minimize, maximize, close) in frameless mode
- [ ] Draggable title bar regions in frameless mode
- [ ] Resizable frameless windows (drag edges/corners)
- [ ] Linux support

**Output:** Checklist with status (working / partially working / broken / not implemented) for each feature.

---

## Step 6: PytoniumShell Readiness Assessment

Evaluate whether the current codebase can support the PytoniumShell widget framework. Specifically check:

1. **Multiple windows:** Can multiple Pytonium instances run in the same process? Is there a shared message loop, or does each instance need its own? What would need to change?

2. **HWND access:** Is the Win32 window handle (HWND) accessible from Python? If not, how hard would it be to expose it?

3. **Transparent backgrounds:** Does CEF's off-screen rendering mode work? Can we get a fully transparent window background so only the HTML content is visible?

4. **Window positioning:** Can we programmatically set window position and size after initialization? Is there an API for this, or does it need to be added?

5. **Window events:** Are window events (focus, blur, resize, move, close) exposed to Python? To JavaScript?

6. **Process model:** How does CEF's multi-process model interact with this? Are there subprocess considerations?

**Output:** For each point, describe the current state and what changes (if any) are needed, with estimated difficulty (easy / medium / hard).

---

## Step 7: Code Quality Summary

- Count lines of code (C++, Python, HTML/JS, build scripts)
- Note any TODO/FIXME/HACK comments in the code
- Assess overall code organization and modularity
- Check for any security concerns (especially around JS ↔ Python bridge, arbitrary code execution, file access)
- Note any dead code or unused files

**Output:** Summary table and recommendations.

---

## Step 8: Final Report

Compile everything into a structured report with these sections:

1. **Executive Summary** — One paragraph: overall health, biggest risks, readiness level
2. **Project Structure** — From Step 1
3. **Build System** — From Step 2
4. **C++ Architecture & Issues** — From Step 3
5. **Python API & Issues** — From Step 4
6. **Feature Status** — From Step 5
7. **PytoniumShell Readiness** — From Step 6
8. **Code Quality** — From Step 7
9. **Recommended Actions** — Prioritized list of what to fix/improve before release, split into:
   - **Must fix** (blockers for a release)
   - **Should fix** (important but not blocking)
   - **Nice to have** (improvements for later)

Save the report as `PYTONIUM_STATUS_REPORT.md` in the project root.
