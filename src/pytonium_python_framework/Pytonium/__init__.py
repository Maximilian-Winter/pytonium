import os
import zipfile
from time import sleep


pytonium_path = os.path.abspath(__file__)
pytonium_path = os.path.dirname(pytonium_path)
pytonium_subprocess_path = f'{pytonium_path}\\bin\\pytonium_subprocess.exe'
pytonium_bin_zip_path = f'{pytonium_path}\\bin.zip'

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

from .src import Pytonium
