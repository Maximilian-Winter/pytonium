---
title: Installation
---

# Installation

This guide covers installing Pytonium and verifying that everything works correctly.

---

## Install from PyPI

The recommended way to install Pytonium is from PyPI using pip:

```bash
pip install Pytonium
```

!!! tip "Use a Virtual Environment"
    It is strongly recommended to install Pytonium in a virtual environment to avoid dependency conflicts.

    === "Windows"

        ```bash
        python -m venv .venv
        .venv\Scripts\activate
        pip install Pytonium
        ```

    === "Linux"

        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        pip install Pytonium
        ```

---

## Verify Your Installation

Run the following script to confirm that Pytonium was installed correctly:

```python
from Pytonium import Pytonium

print("Pytonium imported successfully!")

p = Pytonium()
print("Pytonium instance created!")
```

If both messages print without errors, your installation is working.

---

## First-Run Extraction

!!! info "First import takes longer than usual"
    The first time you import Pytonium after installation, the package extracts its bundled CEF binaries (`bin_win.zip` on Windows, `bin_linux.zip` on Linux). This is a one-time operation that takes a few seconds.

    You will see output like:

    ```
    Pytonium: On the first start up after installation, Pytonium has to extract some dlls and resources!
    Pytonium: This will take a moment, but only happens on first start up!
    ```

    Subsequent imports will be fast because the binaries are already extracted.

---

## Platform Requirements

### Windows

| Requirement | Details |
|---|---|
| Python | 3.10+ (64-bit) |
| OS | Windows 10 or Windows 11 |
| Architecture | x86_64 |

No additional system libraries are required on Windows. The CEF binaries are bundled with the package.

### Linux

| Requirement | Details |
|---|---|
| Python | 3.10+ (64-bit) |
| Display Server | X11 (Wayland is not yet supported) |
| Architecture | x86_64 |

On Linux, CEF depends on several system libraries. If you encounter missing library errors, install the following packages:

=== "Debian / Ubuntu"

    ```bash
    sudo apt install libx11-6 libxcomposite1 libxdamage1 libxext6 \
        libxfixes3 libxrandr2 libxrender1 libxtst6 libnss3 \
        libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
        libdrm2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
        libdbus-1-3 libexpat1 libfontconfig1 libgcc-s1 libglib2.0-0 \
        libgtk-3-0 libatspi2.0-0
    ```

=== "Fedora / RHEL"

    ```bash
    sudo dnf install libX11 libXcomposite libXdamage libXext \
        libXfixes libXrandr libXrender libXtst nss nspr \
        atk at-spi2-atk cups-libs libdrm mesa-libgbm pango \
        cairo alsa-lib dbus-libs expat fontconfig gtk3
    ```

!!! warning "Wayland"
    Pytonium currently requires X11. If you are running a Wayland-only session, you may need to set `GDK_BACKEND=x11` or use XWayland.

---

## Building from Source

If you need to build Pytonium from source (for development or to use the latest unreleased changes), see the [Build Guide](../building/build-guide.md).

Building from source requires:

- CMake 3.20+
- A C++17-compatible compiler (MSVC on Windows, GCC/Clang on Linux)
- Python development headers
- Cython
- scikit-build

---

## Next Steps

Once you have Pytonium installed, continue to the [Quick Start](quickstart.md) guide to learn the core concepts.
