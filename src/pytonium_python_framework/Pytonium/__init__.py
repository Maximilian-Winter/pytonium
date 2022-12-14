import os
from ctypes import cdll
import zipfile
from time import sleep


pytonium_process_path = ""
pytonium_path = os.path.abspath(__file__)
pytonium_path = os.path.dirname(pytonium_path)
if os.name == "nt":
    bin_folder = "bin_win"
else:
    bin_folder = "bin_linux"

pytonium_bin_zip_path = f'{pytonium_path}/{bin_folder}.zip'

if os.path.exists(pytonium_bin_zip_path):
    print("Pytonium: On the first start up after installation, Pytonium has to extract some dlls and resources!")
    print("Pytonium: This will take a moment, but only happens on first start up!")
    compression = zipfile.ZIP_LZMA
    with zipfile.ZipFile(pytonium_bin_zip_path, compression=compression, mode='r') as zip_ref:
        zip_ref.extractall(f'{pytonium_path}/{bin_folder}')
        zip_ref.close()
    sleep(0.1)
    os.remove(pytonium_bin_zip_path)

if os.name == 'nt':
    pytonium_process_path = f'{pytonium_path}/{bin_folder}/pytonium_subprocess.exe'
    os.add_dll_directory(f'{pytonium_path}\\{bin_folder}')

if os.name == 'posix':
    pytonium_process_path = f'{pytonium_path}/{bin_folder}/pytonium_subprocess'
    cdll.LoadLibrary(f'{pytonium_path}/{bin_folder}/libcef.so')

from .pytonium import Pytonium, set_subprocess_path

set_subprocess_path(pytonium_process_path)
