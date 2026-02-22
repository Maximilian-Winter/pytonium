#!/usr/bin/env python3
"""Sync C++ source files to the pyframework build directory.

Deletes all files in the target location and replaces them with the
current versions from src/pytonium_library/.  Run this before building
the Cython extension (python -m build --wheel).

Usage:
    python sync_cpp_to_pyframework.py
"""

import shutil
import sys
from pathlib import Path

# Resolve paths relative to this script's location
SCRIPT_DIR = Path(__file__).resolve().parent
SRC = SCRIPT_DIR / "src" / "pytonium_library"
DST = (
    SCRIPT_DIR
    / "src"
    / "pytonium_python_framework"
    / "Pytonium"
    / "src"
    / "pytonium_library"
)


def sync():
    if not SRC.is_dir():
        print(f"ERROR: Source directory not found: {SRC}")
        sys.exit(1)

    if not DST.is_dir():
        print(f"ERROR: Target directory not found: {DST}")
        sys.exit(1)

    # Delete everything in target (files + subdirs like nlohmann/)
    deleted = 0
    for item in sorted(DST.iterdir()):
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
        deleted += 1

    # Copy everything from source
    copied = 0
    for item in sorted(SRC.iterdir()):
        dst_item = DST / item.name
        if item.is_dir():
            shutil.copytree(item, dst_item)
        else:
            shutil.copy2(item, dst_item)
        copied += 1

    print(f"Synced {copied} items: {SRC.name}/ -> .../{DST.parent.name}/{DST.name}/")
    print(f"  Deleted: {deleted}  Copied: {copied}")


if __name__ == "__main__":
    sync()
