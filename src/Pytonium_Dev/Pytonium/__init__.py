import os
pytonium_path = os.path.abspath(__file__)
pytonium_path = os.path.dirname(pytonium_path)
pytonium_cefsubprocess_path = f'{pytonium_path}\\bin\\cefsubprocess.exe'
os.add_dll_directory(f'{pytonium_path}\\bin')
from .src import Pytonium

