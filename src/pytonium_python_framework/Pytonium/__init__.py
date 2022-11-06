import os
import zipfile
from ctypes import cdll
from time import sleep

import sys

pytonium_path = os.path.abspath(__file__)
pytonium_path = os.path.dirname(pytonium_path)
pytonium_process_path = ""

if os.name == 'nt':
    pytonium_bin_zip_path = f'{pytonium_path}\\bin.zip'
    pytonium_process_path = f'{pytonium_path}\\bin\\pytonium_subprocess.exe'
    if os.path.exists(pytonium_bin_zip_path):
        print("Pytonium: On the first start up after installation, Pytonium has to extract some dlls and resources!")
        print("Pytonium: This will take a moment, but only happens on first start up!")
        compression = zipfile.ZIP_LZMA
        with zipfile.ZipFile(pytonium_bin_zip_path, compression=compression, mode='r') as zip_ref:
            zip_ref.extractall(f'{pytonium_path}\\bin')
            zip_ref.close()
        sleep(0.1)
        os.remove(pytonium_bin_zip_path)

    os.add_dll_directory(f'{pytonium_path}\\bin')

if os.name == 'posix':
    pytonium_process_path = f'{pytonium_path}/bin/pytonium_subprocess'
    print(f'{pytonium_path}/bin/libcef.so')
    cdll.LoadLibrary(f'{pytonium_path}/bin/libcef.so')


from .pytonium import Pytonium, set_subprocess_path
set_subprocess_path(pytonium_process_path)