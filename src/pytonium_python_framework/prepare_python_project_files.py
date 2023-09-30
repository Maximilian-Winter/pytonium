import os
import shutil
from os import listdir
from pathlib import Path
from os.path import isfile, join
import zipfile


if __name__ == "__main__":
    if os.path.exists("./Pytonium/src/cef-binaries-windows/"):
        shutil.rmtree("./Pytonium/src/cef-binaries-windows/")

    if os.path.exists("./Pytonium/src/cef-binaries-linux/"):
        shutil.rmtree("./Pytonium/src/cef-binaries-linux/")

    if os.path.exists("./Pytonium/src/pytonium_library/"):
        shutil.rmtree("./Pytonium/src/pytonium_library/")

    if os.path.exists("./dist"):
        shutil.rmtree("./dist")

    if os.path.exists("./_skbuild"):
        shutil.rmtree("./_skbuild")

    if os.path.exists("./Pytonium.egg-info"):
        shutil.rmtree("./Pytonium.egg-info")

    # Define source and destination directories
    src_dir = Path('../pytonium_library/')
    dest_dir = Path('./Pytonium/src/pytonium_library/')

    # Iterate through all files in source directory and its subdirectories
    for path in src_dir.rglob('*'):
        if path.is_file():  # Check if it's a file
            # Get the relative path of the file within the source directory
            relative_path = path.relative_to(src_dir)

            # Construct the destination path, preserving the folder structure
            dest_fpath = dest_dir / relative_path

            # Create the destination directory if it doesn't exist
            os.makedirs(dest_fpath.parent, exist_ok=True)

            # Copy the file
            shutil.copyfile(path, dest_fpath)

    # Copy windows binaries.
    for path in Path('../../cef-binaries-windows/cmake').rglob('*'):
        if isfile(path):
            dest_fpath = f"./Pytonium/src/cef-binaries-windows/cmake/{os.path.relpath(path, '../../cef-binaries-windows/cmake/')}"
            os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
            shutil.copyfile(path, dest_fpath)

    for path in Path('../../cef-binaries-windows/include').rglob('*'):
        if isfile(path):
            dest_fpath = f"./Pytonium/src/cef-binaries-windows/include/{os.path.relpath(path, '../../cef-binaries-windows/include/')}"
            os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
            shutil.copyfile(path, dest_fpath)

    for path in Path('../../cef-binaries-windows/libcef_dll').rglob('*'):
        if isfile(path):
            dest_fpath = f"./Pytonium/src/cef-binaries-windows/libcef_dll/{os.path.relpath(path, '../../cef-binaries-windows/libcef_dll/')}"
            os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
            shutil.copyfile(path, dest_fpath)

    if not os.path.exists("./Pytonium/src/cef-binaries-windows/Release"):
        os.mkdir("./Pytonium/src/cef-binaries-windows/Release")

    if not os.path.exists("./Pytonium/src/cef-binaries-windows/Release/placeholder"):
        open("./Pytonium/src/cef-binaries-windows/Release/placeholder", 'x').close()

    shutil.copyfile("../../cef-binaries-windows/Release/libcef.lib", "./Pytonium/src/cef-binaries-windows/Release/libcef.lib")

    # Copy linux binaries.

    for path in Path('../../cef-binaries-linux/cmake').rglob('*'):
        if isfile(path):
            dest_fpath = f"./Pytonium/src/cef-binaries-linux/cmake/{os.path.relpath(path, '../../cef-binaries-linux/cmake/')}"
            os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
            shutil.copyfile(path, dest_fpath)

    for path in Path('../../cef-binaries-linux/include').rglob('*'):
        if isfile(path):
            dest_fpath = f"./Pytonium/src/cef-binaries-linux/include/{os.path.relpath(path, '../../cef-binaries-linux/include/')}"
            os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
            shutil.copyfile(path, dest_fpath)

    for path in Path('../../cef-binaries-linux/libcef_dll').rglob('*'):
        if isfile(path):
            dest_fpath = f"./Pytonium/src/cef-binaries-linux/libcef_dll/{os.path.relpath(path, '../../cef-binaries-linux/libcef_dll/')}"
            os.makedirs(os.path.dirname(dest_fpath), exist_ok=True)
            shutil.copyfile(path, dest_fpath)

    if not os.path.exists("./Pytonium/src/cef-binaries-linux/Release"):
        os.mkdir("./Pytonium/src/cef-binaries-linux/Release")

    if not os.path.exists("./Pytonium/src/cef-binaries-linux/Release/placeholder"):
        open("./Pytonium/src/cef-binaries-linux/Release/placeholder", 'x').close()

    shutil.copyfile("../../cef-binaries-linux/Release/libcef.so", "./Pytonium/src/cef-binaries-linux/Release/libcef.so")