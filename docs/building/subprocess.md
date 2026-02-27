---
title: Subprocess Build
---

# Subprocess Build

The `pytonium_subprocess` is a separate executable required by CEF's multi-process architecture. CEF spawns this process for rendering, GPU work, and other sandboxed tasks. It must be compiled from C++ and placed in the correct `bin_win/` or `bin_linux/` directory before building the Python wheel.

---

## Source Files

```
src/pytonium_subprocess/
    CMakeLists.txt                      # CMake build config
    pytonium_subprocess.cc              # Windows entry point (wWinMain)
    pytonium_subprocess_linux.cc        # Linux entry point (main)
    pytonium_subprocess.exe.manifest    # Windows manifest (UAC, compatibility)
```

The subprocess links against `pytonium_library` and `libcef_dll_wrapper`, so those targets must build first. CMake handles this dependency automatically.

---

## Prerequisites

!!! note "Required tools"
    - **CMake** 3.19+
    - **C++20 compiler** (MSVC on Windows, GCC/Clang on Linux)
    - **CEF binaries** downloaded and extracted:
        - Windows: `cef-binaries-windows/` in the project root
        - Linux: `cef-binaries-linux/` in the project root

---

## Building

=== "Windows"

    ### Using CMake from the command line

    ```bash
    # From the project root (pytonium/)

    # Configure (Release)
    cmake -B cmake-build-release -DCMAKE_BUILD_TYPE=Release

    # Build the subprocess target
    cmake --build cmake-build-release --target pytonium_subprocess --config Release
    ```

    For a Debug build:

    ```bash
    cmake -B cmake-build-debug -DCMAKE_BUILD_TYPE=Debug
    cmake --build cmake-build-debug --target pytonium_subprocess --config Debug
    ```

    ### Using Visual Studio / CLion

    1. Open the root `CMakeLists.txt` as a CMake project
    2. Select the `pytonium_subprocess` target
    3. Build with your desired configuration (Debug/Release)

    ### Output location

    After building, the CMakeLists.txt automatically copies the executable to:

    - `src/pytonium_library_test/debug/bin/pytonium_subprocess.exe` (Debug)
    - `src/pytonium_library_test/release/bin/pytonium_subprocess.exe` (Release)
    - `src/pytonium_python_framework/Pytonium/bin_win/pytonium_subprocess.exe` (both)

    The `prepare_build.py` script looks for the executable at the `pytonium_library_test` paths above by default. You can also point it at your CMake build directory with `--build-dir` to search there first:

    ```bash
    python prepare_build.py --platform windows --build-dir ../cmake-build-release
    ```

=== "Linux"

    ```bash
    # From the project root (pytonium/)

    # Configure (Release)
    cmake -B build_linux -DCMAKE_BUILD_TYPE=Release

    # Build the subprocess target
    cmake --build build_linux --target pytonium_subprocess
    ```

    For a Debug build:

    ```bash
    cmake -B build_linux -DCMAKE_BUILD_TYPE=Debug
    cmake --build build_linux --target pytonium_subprocess
    ```

    ### Output location

    After building, the CMakeLists.txt automatically copies the executable to:

    - `src/pytonium_library_test/debug/pytonium_subprocess` (Debug)
    - `src/pytonium_library_test/release/pytonium_subprocess` (Release)
    - `src/pytonium_python_framework/Pytonium/bin_linux/pytonium_subprocess` (both)

    ### Linux-specific notes

    - The executable has `RPATH` set to `$ORIGIN` so it finds `libcef.so` in the same directory
    - The `chrome-sandbox` binary gets SUID permissions set automatically if present
    - `libminigbm.so` is copied alongside if it exists in the CEF binary distribution

---

## Full Build Workflow

=== "Windows"

    ```bash
    # 1. Build the subprocess (and pytonium_library) from the project root
    cmake -B cmake-build-release -DCMAKE_BUILD_TYPE=Release
    cmake --build cmake-build-release --target pytonium_subprocess --config Release

    # 2. Run the prepare script
    cd building_pythonium_core
    python prepare_build.py --platform windows --build-dir ../cmake-build-release

    # 3. Build the wheel
    cd ../src/pytonium_python_framework
    python -m build --wheel

    # 4. Install
    pip install dist/pytonium-*.whl --force-reinstall
    ```

=== "Linux"

    ```bash
    # 1. Build the subprocess (and pytonium_library) from the project root
    cmake -B build_linux -DCMAKE_BUILD_TYPE=Release
    cmake --build build_linux --target pytonium_subprocess

    # 2. Run the prepare script
    cd building_pythonium_core
    python3 prepare_build.py --platform linux --build-dir ../build_linux

    # 3. Build the wheel
    cd ../src/pytonium_python_framework
    python3 -m build --wheel

    # 4. Install
    pip install dist/pytonium-*.whl --force-reinstall
    ```

---

## Troubleshooting

### "pytonium_subprocess not found at expected locations"

This warning from `prepare_build.py` means:

- The subprocess has not been built yet, **or**
- You are running with `--platform all` (the default) on a single-platform machine, so the other platform's binary is missing

!!! tip "Fix"
    Build the subprocess first, then run `prepare_build.py --platform windows` (or `linux`). If your CMake build directory is non-standard, use `--build-dir` to point at it.

### Build fails with missing CEF headers

!!! tip "Fix"
    Ensure the CEF binary distribution is extracted to `cef-binaries-windows/` or `cef-binaries-linux/` in the project root. The root `CMakeLists.txt` sets `CEF_ROOT` to these paths.

### Build fails with missing pytonium_library

The subprocess depends on the `pytonium_library` target. CMake handles this dependency automatically -- building the subprocess target also builds the library.

!!! tip "Fix"
    If you see linker errors, verify that `src/pytonium_library/` exists and its `CMakeLists.txt` is valid.

---

## See Also

- **[Build Guide](build-guide.md)** -- Complete build-from-source workflow
- **[Prepare Build Script](prepare-build.md)** -- Full `prepare_build.py` reference
