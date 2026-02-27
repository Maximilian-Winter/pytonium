# Pytonium Build Preparation Script Guide

This guide explains how to use the `prepare_build.py` script to prepare the Pytonium Cython extension for building.

## Overview

The `prepare_build.py` script automates all the preparatory steps needed before building the Pytonium wheel:

1. Cleans old build artifacts
2. Syncs C++ library source files
3. Syncs subprocess source files
4. Copies CEF binaries (headers, cmake modules, wrapper)
5. Copies CEF runtime resources and DLLs
6. Copies the pytonium_subprocess executable

## Prerequisites

Before running the script, ensure you have:

- Python 3.10+ virtual environment activated
- CEF binaries downloaded in `cef-binaries-windows/` or `cef-binaries-linux/`
- C++ library source in `src/pytonium_library/`
- Subprocess source in `src/pytonium_subprocess/`

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

## CLI Options

| Option | Description |
|--------|-------------|
| `--platform {windows,linux,all}` | Which platform to prepare (default: all) |
| `--dry-run` | Show what would be done without making changes |
| `-v, --verbose` | Enable verbose output |
| `--skip-clean` | Skip the cleanup step |
| `--skip-sync` | Skip C++ source sync step |
| `--skip-cef` | Skip CEF binary copy step |
| `--build-dir PATH` | CMake build directory to locate `pytonium_subprocess` |

## Examples

### Dry Run

Preview what the script will do without making any changes:

```bash
python prepare_build.py --dry-run
```

### Verbose Output

See detailed progress during execution:

```bash
python prepare_build.py -v
```

### Combined Options

Windows preparation with verbose output:

```bash
python prepare_build.py --platform windows -v
```

### Skip Specific Steps

If you've already completed certain steps, you can skip them:

```bash
# Skip cleanup if files already removed
python prepare_build.py --skip-clean

# Only copy CEF binaries (skip cleanup and sync)
python prepare_build.py --skip-clean --skip-sync
```

## Complete Build Workflow

### Step 1: Prepare the Build

```bash
cd building_pythonium_core
python prepare_build.py --platform windows -v
```

### Step 2: Build the Wheel

```bash
cd ../src/pytonium_python_framework
python -m build --wheel
```

### Step 3: Install the Wheel

```bash
pip install dist/pytonium-*.whl --force-reinstall
```

## Troubleshooting

### "Source library not found"

Ensure `src/pytonium_library/` exists in the project root.

### "CEF binaries not found"

Ensure `cef-binaries-windows/` or `cef-binaries-linux/` exists in the project root.

### "pytonium_subprocess not found"

The subprocess executable must be built separately from `src/pytonium_subprocess/`. Check that `src/pytonium_library_test/release/bin/pytonium_subprocess.exe` exists, or use `--build-dir` to point at your CMake build directory:

```bash
python prepare_build.py --platform windows --build-dir ../cmake-build-release
```

## Script Location

The script is located at:

```
pytonium/
└── building_pythonium_core/
    └── prepare_build.py
```

Run it from the `building_pythonium_core` directory or adjust paths accordingly.

# Script Usage

Usage:    
```
cd building_pythonium_core                                                                                                                                                                                                                                                                                
python prepare_build.py                    # Full prepare (all platforms)                                                                                                                                                                                                                                 
python prepare_build.py --platform windows  # Windows only                                                                                                                                                                                                                                                
python prepare_build.py --dry-run          # Show what would be done                                                                                                                                                                                                                                      
python prepare_build.py -v                 # Verbose output                                                                                                                                                                                                                                               
python prepare_build.py --skip-clean       # Skip cleanup       
```