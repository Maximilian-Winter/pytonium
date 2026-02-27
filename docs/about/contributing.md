---
title: Contributing
---

# Contributing

Thank you for your interest in contributing to Pytonium. This page covers how to report bugs, set up a development environment, and submit changes.

---

## Reporting Bugs

If you encounter a bug, please open an issue on the [GitHub Issues](https://github.com/Maximilian-Winter/pytonium/issues) page with the following information:

!!! info "What to include in a bug report"
    - **Operating system and version** (e.g., Windows 11 23H2, Ubuntu 24.04)
    - **Python version** (e.g., Python 3.10.12)
    - **Pytonium version** (e.g., 0.0.13)
    - **Steps to reproduce** the issue
    - **Expected behavior** vs. **actual behavior**
    - **Error messages or stack traces** (if applicable)
    - **Minimal code example** that reproduces the problem

A minimal reproduction makes it much easier to diagnose and fix the issue.

---

## Feature Requests

Feature requests are welcome. Open a [GitHub Issue](https://github.com/Maximilian-Winter/pytonium/issues) with the `enhancement` label and describe:

- What you want to achieve
- Why existing features do not meet your needs
- Any ideas for how the feature could work

---

## Development Setup

### 1. Fork and Clone

Fork the repository on GitHub, then clone your fork:

```bash
git clone https://github.com/YOUR-USERNAME/pytonium.git
cd pytonium
```

### 2. Create a Virtual Environment

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

### 3. Build from Source

Follow the [Build Guide](../building/build-guide.md) to build and install Pytonium from source. This involves:

1. Building the C++ subprocess
2. Running the prepare build script
3. Building the Python wheel
4. Installing the wheel

### 4. Run Tests

```bash
python -m pytest tests/
```

---

## Pull Request Guidelines

### Before Submitting

1. **Create a branch** from `master` for your changes:

    ```bash
    git checkout -b my-feature-branch
    ```

2. **Make your changes** in focused, logical commits.

3. **Test your changes** by running the existing test suite and adding new tests if applicable.

4. **Verify the build** completes successfully on your platform.

### Submitting

1. Push your branch to your fork:

    ```bash
    git push origin my-feature-branch
    ```

2. Open a Pull Request against the `master` branch of the main repository.

3. In the PR description, explain:
    - **What** the change does
    - **Why** the change is needed
    - **How** you tested it
    - Any **breaking changes** or **migration steps** required

!!! warning "Large Changes"
    For significant changes (new features, architectural changes, API modifications), consider opening an issue first to discuss the approach before writing code.

---

## Code Style

### C++ (src/pytonium_library/, src/pytonium_subprocess/)

- **Standard**: C++20
- **Naming**: PascalCase for classes and methods, camelCase for local variables
- **Formatting**: 4-space indentation
- **Definitions**: Use `add_compile_definitions(NOMINMAX WIN32_LEAN_AND_MEAN)` on Windows
- **Window API**: Use the `W` variants (e.g., `GetWindowLongPtrW`, `GetModuleFileNameW`) for Unicode support
- **Pointer size**: Use `GetWindowLongPtrW`/`SetWindowLongPtrW` (not `GetWindowLongW`) for 64-bit safety

### Cython (src/pytonium_python_framework/Pytonium/src/pytonium.pyx)

- All callbacks must use `with gil` and wrap the body in `try/except`
- Keep the `.pxd` declarations in sync with the C++ header
- Update the `.pyi` stub file when adding or changing public methods

### Python

- **Standard**: PEP 8
- **Type hints**: Required on all public functions and methods
- **Docstrings**: Required on all public functions and methods
- **Default arguments**: Do not use mutable default arguments (lists, dicts)

### Type Stubs (.pyi)

The type stubs at `src/pytonium_python_framework/Pytonium/pytonium.pyi` are **hand-maintained** (not auto-generated). If you add or modify a public method in the Cython bridge, update the stubs accordingly.

---

## Project Structure

```
pytonium/
    src/
        pytonium_library/       # C++ core library
        pytonium_subprocess/    # C++ subprocess for CEF multi-process
        pytonium_python_framework/
            Pytonium/
                src/
                    pytonium.pyx    # Cython bridge
                    pytonium_library.pxd  # C++ declarations
                __init__.py         # Package init
                pytonium.pyi        # Type stubs
            setup.py                # scikit-build setup
    tests/                          # Test suite
    building_pythonium_core/        # Build preparation scripts
    docs/                           # MkDocs documentation
    cef-binaries-windows/           # CEF binaries (not in git)
    cef-binaries-linux/             # CEF binaries (not in git)
```

---

## Areas Where Help is Appreciated

- **macOS support** -- Pytonium does not yet support macOS
- **Wayland support** -- Currently X11 only on Linux
- **Documentation improvements** -- Corrections, clarifications, additional examples
- **Test coverage** -- Additional unit and integration tests
- **Bug fixes** -- See the [open issues](https://github.com/Maximilian-Winter/pytonium/issues)

---

## License

By contributing to Pytonium, you agree that your contributions will be licensed under the [MIT License](license.md), the same license that covers the project.
