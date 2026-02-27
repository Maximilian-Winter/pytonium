---
title: Build Guide
---

# Build Guide

This guide covers building the Pytonium Python framework from source on Windows and Linux using CLI commands.

!!! note "Most users do not need to build from source"
    If you just want to use Pytonium, install it from PyPI with `pip install Pytonium`. This guide is for contributors, developers working on Pytonium itself, or anyone who needs the latest unreleased changes.

---

## Prerequisites

=== "Windows"

    - **Python 3.10+** (64-bit) -- [python.org](https://www.python.org/downloads/)
        - Check "Add Python to PATH" during installation
    - **Visual Studio 2022 Build Tools** (or full Visual Studio)
        - Workload: **Desktop development with C++**
        - Components: MSVC v143 C++ x64/x86 build tools, Windows SDK
    - **CMake 3.19+** -- included with Visual Studio, or [cmake.org](https://cmake.org/download/)
    - **Git** -- [git-scm.com](https://git-scm.com/)

=== "Linux (Ubuntu/Debian)"

    ```bash
    sudo apt-get update
    sudo apt-get install -y build-essential cmake ninja-build python3-dev python3-venv git binutils
    ```

    `binutils` provides `strip`, used to reduce `.so` file sizes during build preparation.

!!! warning "CEF Binaries Required"
    The CEF binary distribution must be present in the project root before building:

    - Windows: `cef-binaries-windows/`
    - Linux: `cef-binaries-linux/`

    These are not included in the git repository due to their size. See the project README for download instructions.

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/Maximilian-Winter/pytonium.git
cd pytonium
```

---

## Step 2: Set Up Python Environment

=== "Windows"

    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    pip install --upgrade pip
    pip install build scikit-build cmake ninja Cython
    ```

=== "Linux"

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install build scikit-build cmake ninja Cython
    ```

---

## Step 3: Build the C++ Subprocess

CEF uses a multi-process architecture and requires a separate `pytonium_subprocess` executable.

=== "Windows"

    ```bash
    cmake -B cmake-build-release -DCMAKE_BUILD_TYPE=Release
    cmake --build cmake-build-release --target pytonium_subprocess --config Release
    ```

=== "Linux"

    ```bash
    cmake -B build_linux -DCMAKE_BUILD_TYPE=Release
    cmake --build build_linux --target pytonium_subprocess
    ```

This also builds the `pytonium_library` and `libcef_dll_wrapper` dependencies automatically.

!!! info "First Build Time"
    The first build compiles the CEF wrapper library (~200 source files) and may take several minutes. Subsequent builds are significantly faster.

For more details on the subprocess, see the [Subprocess Build](subprocess.md) page.

---

## Step 4: Prepare Build Files

The `prepare_build.py` script syncs C++ sources, copies CEF binaries, and places the subprocess executable into the correct locations for the Python wheel build.

=== "Windows"

    ```bash
    cd building_pythonium_core
    python prepare_build.py --platform windows --build-dir ../cmake-build-release
    ```

=== "Linux"

    ```bash
    cd building_pythonium_core
    python3 prepare_build.py --platform linux --build-dir ../build_linux
    ```

The script performs the following steps:

1. Cleans old build artifacts (`dist/`, `_skbuild/`, `Pytonium.egg-info/`, `bin_win/` or `bin_linux/`)
2. Syncs C++ library source files into the pyframework directory
3. Syncs subprocess source files
4. Copies CEF binaries (headers, cmake modules, libcef_dll wrapper, libcef)
5. Copies CEF runtime resources and shared libraries to the bin folder
6. Copies the `pytonium_subprocess` executable to the bin folder
7. On Linux: strips debug symbols from `.so` files (e.g., `libcef.so` 1.5 GB -> ~250 MB)

For the full options reference, see [Prepare Build Script](prepare-build.md).

---

## Step 5: Build the Wheel

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

This creates a wheel file in `src/pytonium_python_framework/dist/`, for example:

- Windows: `pytonium-0.0.13-cp310-cp310-win_amd64.whl`
- Linux: `pytonium-0.0.13-cp310-cp310-linux_x86_64.whl`

!!! tip "Build Duration"
    The build compiles Cython extensions and links against CEF. It typically takes 5-15 minutes depending on your hardware.

---

## Step 6: Install the Package

```bash
pip install dist/pytonium-*.whl --force-reinstall
```

---

## Quick Reference (Full Workflow)

=== "Windows"

    ```bash
    git clone https://github.com/Maximilian-Winter/pytonium.git
    cd pytonium
    python -m venv .venv
    .venv\Scripts\activate
    pip install --upgrade pip build scikit-build cmake ninja Cython

    cmake -B cmake-build-release -DCMAKE_BUILD_TYPE=Release
    cmake --build cmake-build-release --target pytonium_subprocess --config Release

    cd building_pythonium_core
    python prepare_build.py --platform windows --build-dir ../cmake-build-release
    cd ../src/pytonium_python_framework
    python -m build --wheel
    pip install dist/pytonium-*.whl --force-reinstall
    ```

=== "Linux"

    ```bash
    git clone https://github.com/Maximilian-Winter/pytonium.git
    cd pytonium
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip build scikit-build cmake ninja Cython

    cmake -B build_linux -DCMAKE_BUILD_TYPE=Release
    cmake --build build_linux --target pytonium_subprocess

    cd building_pythonium_core
    python3 prepare_build.py --platform linux --build-dir ../build_linux
    cd ../src/pytonium_python_framework
    python3 -m build --wheel
    pip install dist/pytonium-*.whl --force-reinstall
    ```

---

## Verification

```python
from Pytonium import Pytonium

print("Pytonium imported successfully!")
p = Pytonium()
print("Pytonium instance created successfully!")
```

If both messages print without errors, your build is working.

---

## Troubleshooting

### "pytonium_subprocess not found at expected locations"

The subprocess executable has not been built, or was built to a non-standard directory.

!!! tip "Fix"
    Build the subprocess (Step 3), then use `--build-dir` to point at your CMake build directory.

### "CMake Error: Could not find package configuration file provided by 'CEF'"

The CEF binary distribution is missing.

!!! tip "Fix"
    Ensure `cef-binaries-windows/` (or `cef-binaries-linux/`) exists in the project root.

### "libcef.so missing" or ninja error about missing .so file

On Linux, `libcef.so` (~1.5 GB) must be copied to `bin_linux/` and then into the CEF build directory by `setup.py`. If `prepare_build.py` was not run (or was run with `--skip-cef`), this file will be missing.

!!! tip "Fix"
    Re-run `prepare_build.py --platform linux` without `--skip-cef`.

### Stale _skbuild cache causes FindCython or other CMake errors

The `_skbuild/` directory caches CMake configuration between builds. If your build environment changes (e.g., different Python virtualenv, different temp paths), the cache becomes stale.

!!! tip "Fix"
    Delete `_skbuild/` and rebuild. The `prepare_build.py` script does this automatically in its cleanup step (Step 1), so re-running it without `--skip-clean` will fix this.

### Build takes very long or hangs

- The first build compiles the CEF wrapper library (~200 source files). Subsequent builds are faster.
- Ensure at least 8 GB of free RAM.
- On WSL with NTFS mounts (`/mnt/...`), I/O is significantly slower than on native ext4.

### Windows: "Syntaxfehler" or macro conflicts

!!! tip "Fix"
    The `CMakeLists.txt` should include `add_compile_definitions(NOMINMAX WIN32_LEAN_AND_MEAN)` for Windows. This is already set in the current codebase.

---

## Clean Build

To perform a completely clean build, re-run `prepare_build.py` without `--skip-clean` (the default). This removes `_skbuild/`, `dist/`, `Pytonium.egg-info/`, and the platform bin folder.

Alternatively, clean manually:

```bash
cd src/pytonium_python_framework
rm -rf _skbuild dist Pytonium.egg-info
```

---

## See Also

- **[Subprocess Build](subprocess.md)** -- Detailed subprocess build guide
- **[Prepare Build Script](prepare-build.md)** -- Full `prepare_build.py` reference
- **[Pytonium Examples](https://github.com/Maximilian-Winter/pytonium_examples)** -- Example applications
