---
title: Prepare Build Script
---

# Prepare Build Script

The `prepare_build.py` script automates all preparatory steps needed before building the Pytonium wheel. It syncs C++ sources, copies CEF binaries, and places the subprocess executable into the correct directory structure.

---

## Overview

The script performs these steps in order:

1. **Clean** -- Removes old build artifacts (`dist/`, `_skbuild/`, `Pytonium.egg-info/`, `bin_win/` or `bin_linux/`)
2. **Sync C++ sources** -- Copies library and subprocess source files into the pyframework directory
3. **Copy CEF binaries** -- Copies headers, cmake modules, libcef_dll wrapper, and libcef
4. **Copy CEF resources** -- Copies runtime resources and shared libraries to the bin folder
5. **Copy subprocess** -- Places the `pytonium_subprocess` executable in the bin folder
6. **Strip symbols** (Linux only) -- Strips debug symbols from `.so` files (e.g., `libcef.so` 1.5 GB -> ~250 MB)

---

## Prerequisites

!!! note "Before running the script"
    - Python 3.10+ virtual environment activated
    - CEF binaries downloaded in `cef-binaries-windows/` or `cef-binaries-linux/`
    - C++ library source in `src/pytonium_library/`
    - Subprocess source in `src/pytonium_subprocess/`
    - Subprocess executable built (see [Subprocess Build](subprocess.md))

---

## Basic Usage

### Full Preparation (All Platforms)

```bash
cd building_pythonium_core
python prepare_build.py
```

This prepares both Windows and Linux binaries.

### Windows Only

```bash
python prepare_build.py --platform windows
```

### Linux Only

```bash
python prepare_build.py --platform linux
```

---

## CLI Options

| Option | Description | Default |
|---|---|---|
| `--platform {windows,linux,all}` | Which platform to prepare | `all` |
| `--build-dir PATH` | CMake build directory to locate `pytonium_subprocess` | (auto-detect) |
| `--dry-run` | Show what would be done without making changes | off |
| `-v, --verbose` | Enable verbose output | off |
| `--skip-clean` | Skip the cleanup step | off |
| `--skip-sync` | Skip C++ source sync step | off |
| `--skip-cef` | Skip CEF binary copy step | off |

---

## Examples

### Dry Run

Preview what the script will do without making any changes:

```bash
python prepare_build.py --dry-run
```

!!! tip "Use dry run first"
    When running the script for the first time or after changing your build setup, a dry run lets you verify the paths and steps before any files are modified.

### Verbose Output

See detailed progress during execution:

```bash
python prepare_build.py -v
```

### Windows Preparation with Custom Build Directory

```bash
python prepare_build.py --platform windows --build-dir ../cmake-build-release -v
```

### Skip Specific Steps

If you have already completed certain steps, you can skip them:

```bash
# Skip cleanup if files already removed
python prepare_build.py --skip-clean

# Only copy CEF binaries (skip cleanup and sync)
python prepare_build.py --skip-clean --skip-sync

# Only sync sources (skip cleanup and CEF copy)
python prepare_build.py --skip-clean --skip-cef
```

---

## Complete Build Workflow

### Step 1: Prepare the Build

=== "Windows"

    ```bash
    cd building_pythonium_core
    python prepare_build.py --platform windows --build-dir ../cmake-build-release -v
    ```

=== "Linux"

    ```bash
    cd building_pythonium_core
    python3 prepare_build.py --platform linux --build-dir ../build_linux -v
    ```

### Step 2: Build the Wheel

=== "Windows"

    ```bash
    cd ../src/pytonium_python_framework
    python -m build --wheel
    ```

=== "Linux"

    ```bash
    cd ../src/pytonium_python_framework
    python3 -m build --wheel
    ```

### Step 3: Install the Wheel

```bash
pip install dist/pytonium-*.whl --force-reinstall
```

---

## Troubleshooting

### "Source library not found"

!!! tip "Fix"
    Ensure `src/pytonium_library/` exists in the project root. This directory contains the C++ source files that are synced into the pyframework directory.

### "CEF binaries not found"

!!! tip "Fix"
    Ensure `cef-binaries-windows/` or `cef-binaries-linux/` exists in the project root. These directories contain the CEF binary distribution.

### "pytonium_subprocess not found"

The subprocess executable must be built separately before running this script.

!!! tip "Fix"
    Build the subprocess first (see [Subprocess Build](subprocess.md)), then use `--build-dir` to point at your CMake build directory:

    ```bash
    python prepare_build.py --platform windows --build-dir ../cmake-build-release
    ```

    The script searches for the executable in these locations:

    1. The `--build-dir` path (if provided)
    2. `src/pytonium_library_test/release/bin/pytonium_subprocess.exe` (Windows)
    3. `src/pytonium_library_test/release/pytonium_subprocess` (Linux)

---

## Script Location

```
pytonium/
    building_pythonium_core/
        prepare_build.py
```

Run it from the `building_pythonium_core` directory or adjust paths accordingly.

---

## Quick Reference

```bash
cd building_pythonium_core
python prepare_build.py                             # Full prepare (all platforms)
python prepare_build.py --platform windows          # Windows only
python prepare_build.py --platform linux            # Linux only
python prepare_build.py --dry-run                   # Show what would be done
python prepare_build.py -v                          # Verbose output
python prepare_build.py --skip-clean                # Skip cleanup
python prepare_build.py --build-dir ../my-build     # Custom build directory
```

---

## See Also

- **[Build Guide](build-guide.md)** -- Complete build-from-source workflow
- **[Subprocess Build](subprocess.md)** -- How to build the `pytonium_subprocess` executable
