import os
from ctypes import cdll

pytonium_path = os.path.abspath(__file__)
pytonium_path = os.path.dirname(pytonium_path)
pytonium_process_path = ""

if os.name == 'nt':
    pytonium_process_path = f'{pytonium_path}/bin/pytonium_subprocess.exe'
    os.add_dll_directory(f'{pytonium_path}\\bin')

if os.name == 'posix':
    pytonium_process_path = f'{pytonium_path}/bin/pytonium_subprocess'
    cdll.LoadLibrary(f'{pytonium_path}/bin/libcef.so')

from .pytonium import Pytonium, set_subprocess_path

set_subprocess_path(pytonium_process_path)
