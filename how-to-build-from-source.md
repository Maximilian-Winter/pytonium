# How to Build Pytonium from Source

This guide explains how to build the Pytonium Python framework from source on Windows.

## Prerequisites

### Required Software

1. **Python 3.10+** (64-bit)
   - Download from: https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

2. **Visual Studio 2022** (Community Edition or higher)
   - Download from: https://visualstudio.microsoft.com/
   - Required Workloads:
     - **Desktop development with C++**
   - Required Individual Components:
     - MSVC v143 - VS 2022 C++ x64/x86 build tools
     - Windows 11 SDK (or Windows 10 SDK)
     - CMake tools for Windows

3. **CMake 3.18+**
   - Usually included with Visual Studio
   - Or download from: https://cmake.org/download/

4. **Git** (for cloning the repository)
   - Download from: https://git-scm.com/

## Setup Instructions

### Step 1: Clone the Repository

```bash
git clone https://github.com/Maximilian-Winter/pytonium.git
cd pytonium
```

### Step 2: Create a Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Build Dependencies

```bash
pip install --upgrade pip
pip install build scikit-build cmake ninja Cython
```

### Step 4: Prepare Source Files

The Python framework requires the C++ library source files and CEF binaries to be in the correct location:

```powershell
# From the repository root, copy CEF binaries
copy-item -path "cef-binaries-windows" -destination "src/pytonium_python_framework/Pytonium/src/cef-binaries-windows" -recurse -force

# Copy the C++ library source
copy-item -path "src/pytonium_library" -destination "src/pytonium_python_framework/Pytonium/src/pytonium_library" -recurse -force

# Copy the subprocess source
copy-item -path "src/pytonium_subprocess" -destination "src/pytonium_python_framework/Pytonium/src/pytonium_subprocess" -recurse -force
```

Or using Command Prompt:

```cmd
xcopy /E /I cef-binaries-windows src\pytonium_python_framework\Pytonium\src\cef-binaries-windows
xcopy /E /I src\pytonium_library src\pytonium_python_framework\Pytonium\src\pytonium_library
xcopy /E /I src\pytonium_subprocess src\pytonium_python_framework\Pytonium\src\pytonium_subprocess
```

### Step 5: Build the Wheel

```bash
cd src/pytonium_python_framework
python -m build --wheel
```

This will create a wheel file in `src/pytonium_python_framework/dist/` named something like:
```
pytonium-0.0.13-cp313-cp313-win_amd64.whl
```

The build process typically takes 10-30 minutes depending on your system.

### Step 6: Install the Package

```bash
pip install dist/pytonium-0.0.13-cp313-cp313-win_amd64.whl --force-reinstall
```

Or install directly without building the wheel first:

```bash
pip install . --no-build-isolation
```

## Verification

Test the installation by running a simple example:

```python
from Pytonium import Pytonium

print("Pytonium imported successfully!")

# Create a simple test
pytonium = Pytonium()
print("Pytonium instance created successfully!")
```

## Build Configuration

### Build Options

The build can be customized by modifying `pyproject.toml`:

```toml
[tool.scikit-build]
build-type = "Release"  # or "Debug"
```

### CMake Arguments

Additional CMake arguments can be passed in `setup.py`:

```python
setup(
    cmake_args=['-DUSE_SANDBOX=OFF', '-DCMAKE_BUILD_TYPE=Release'],
)
```

## Troubleshooting

### Issue: "Cannot import 'scikit_build.build'"

**Solution:** Make sure `scikit-build` is installed before building:

```bash
pip install scikit-build>=0.16
```

### Issue: "CMake Error: Could not find package configuration file provided by 'CEF'"

**Solution:** The CEF binaries are not in the expected location. Make sure to copy `cef-binaries-windows` to `src/pytonium_python_framework/Pytonium/src/`.

### Issue: "Syntaxfehler: Ungültiges Token auf der rechten Seite von '::'"

**Solution:** This is a Windows macro conflict. The `CMakeLists.txt` should include:

```cmake
if(WIN32)
    add_compile_definitions(NOMINMAX WIN32_LEAN_AND_MEAN)
endif()
```

### Issue: "CMake Error: Compatibility with CMake < 3.5 has been removed"

**Solution:** Update the minimum CMake version in `src/pytonium_python_framework/CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.5)
```

### Issue: "No module named 'Pytonium.pytonium'" after installation

**Solution:** The compiled extension module (.pyd file) was not built or installed. Make sure:
1. You're using the correct Python version (the wheel is platform-specific)
2. The build completed without errors
3. Install with `--force-reinstall` flag

### Issue: Build takes very long or hangs

**Solution:** 
- The first build compiles CEF which is large. Subsequent builds are faster.
- Make sure you have at least 8GB of free RAM
- Close other applications to free up resources

## Development Build (Editable Install)

For development, you can install in editable mode:

```bash
cd src/pytonium_python_framework
pip install -e . --no-build-isolation
```

Note: This requires all build dependencies to be installed in your environment.

## Clean Build

To perform a clean build, remove the build directories:

```bash
cd src/pytonium_python_framework
Remove-Item -Path "_skbuild" -Recurse -Force
Remove-Item -Path "dist" -Recurse -Force
Remove-Item -Path "Pytonium.egg-info" -Recurse -Force
```

Then rebuild from Step 5.

## Platform-Specific Notes

### Windows
- Use Visual Studio 2022 or 2019
- Make sure to use the "x64 Native Tools Command Prompt" if building manually
- The wheel is platform-specific: `pytonium-0.0.13-cp313-cp313-win_amd64.whl`

### Linux (Ubuntu/Debian)
Install system dependencies:
```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake ninja-build python3-dev
```

Then follow the same build steps.

## See Also

- [README.md](README.md) - Project overview and usage
- [Pytonium Examples](https://github.com/Maximilian-Winter/pytonium_examples) - Example applications
