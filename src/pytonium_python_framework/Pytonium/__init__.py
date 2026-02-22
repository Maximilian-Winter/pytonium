import os
from ctypes import cdll
import zipfile
from time import sleep


def returns_value_to_javascript(return_type="any"):
    def decorator(func):
        func.returns_value_to_javascript = True
        func.return_type = return_type
        return func

    return decorator


pytonium_process_path = ""
pytonium_path = os.path.abspath(__file__)
pytonium_path = os.path.dirname(pytonium_path)
if os.name == "nt":
    bin_folder = "bin_win"
    other_bin_folder = "bin_linux"
else:
    bin_folder = "bin_linux"
    other_bin_folder = "bin_win"

pytonium_bin_zip_path = f'{pytonium_path}/{bin_folder}.zip'
other_pytonium_bin_zip_path = f'{pytonium_path}/{other_bin_folder}.zip'

if os.path.exists(pytonium_bin_zip_path):
    print("Pytonium: On the first start up after installation, Pytonium has to extract some dlls and resources!")
    print("Pytonium: This will take a moment, but only happens on first start up!")
    compression = zipfile.ZIP_LZMA
    with zipfile.ZipFile(pytonium_bin_zip_path, compression=compression, mode='r') as zip_ref:
        zip_ref.extractall(f'{pytonium_path}/{bin_folder}')
        zip_ref.close()
    sleep(2.0)
    if os.path.exists(pytonium_bin_zip_path):
        os.remove(pytonium_bin_zip_path)

    if os.path.exists(other_pytonium_bin_zip_path):
        os.remove(other_pytonium_bin_zip_path)

if os.name == 'nt':
    pytonium_process_path = f'{pytonium_path}/{bin_folder}/pytonium_subprocess.exe'
    os.add_dll_directory(f'{pytonium_path}\\{bin_folder}')

if os.name == 'posix':
    pytonium_process_path = f'{pytonium_path}/{bin_folder}/pytonium_subprocess'
    cdll.LoadLibrary(f'{pytonium_path}/{bin_folder}/libcef.so')

from .pytonium import Pytonium as Pytonium

# Initialize the class-level attribute upon import
Pytonium.set_subprocess_path(pytonium_process_path)


async def run_pytonium_async(pytonium, interval=0.016):
    """Run the Pytonium message loop as an async coroutine.

    This allows integrating Pytonium into an asyncio event loop.
    Call this from an async context instead of writing your own
    ``while is_running: update_message_loop; sleep`` loop.

    Args:
        pytonium: A Pytonium instance (must already be initialized).
        interval: Seconds between message loop updates (default ~60fps).

    Example::

        import asyncio
        from Pytonium import Pytonium, run_pytonium_async

        p = Pytonium()
        p.initialize("https://example.com", 800, 600)
        asyncio.run(run_pytonium_async(p))
    """
    import asyncio
    while pytonium.is_running():
        pytonium.update_message_loop()
        await asyncio.sleep(interval)
