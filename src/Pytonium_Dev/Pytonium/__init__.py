import os
import zipfile
pytonium_path = os.path.abspath(__file__)
pytonium_path = os.path.dirname(pytonium_path)
pytonium_cefsubprocess_path = f'{pytonium_path}\\bin\\cefsubprocess.exe'
pytonium_libcef_zip_path = f'{pytonium_path}\\bin.zip'
if os.path.exists(pytonium_libcef_zip_path):
    print("On first start up after installation with pip, we have to extract some dlls and resources!")
    print("This will take a moment, but only happens on first start up!")
    compression = zipfile.ZIP_LZMA
    with zipfile.ZipFile(pytonium_libcef_zip_path, compression=compression, mode='r') as zip_ref:
        zip_ref.extractall(f'{pytonium_path}\\bin')
        zip_ref.close()
        os.remove(pytonium_libcef_zip_path)

os.add_dll_directory(f'{pytonium_path}\\bin')
from .src import Pytonium