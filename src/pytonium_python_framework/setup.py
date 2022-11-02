from time import sleep

from Cython.Build import cythonize
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as build_ext
import zipfile
import os
from os import listdir
from os.path import isfile, join


is_pytonium_release_build = True


def compress_binaries():
    pytonium_files = []
    pytonium_bin_files = []
    if not isfile("./Pytonium/bin.zip") and is_pytonium_release_build:
        print("Building Pytonium Release")
        print("Creating Pytonium binaries zip file...")
        pytonium_files = ['./bin.zip']
        compression = zipfile.ZIP_LZMA
        zf = zipfile.ZipFile("./Pytonium/bin.zip", mode="w")

        pytonium_binaries_path = "./Pytonium/bin/"
        binaries = [f for f in listdir(pytonium_binaries_path) if isfile(join(pytonium_binaries_path, f))]

        pytonium_locales_path = "./Pytonium/bin/locales/"
        locales_files = [f for f in listdir(pytonium_locales_path) if isfile(join(pytonium_locales_path, f))]
        try:
            for file_to_write in binaries:
                zf.write(pytonium_binaries_path + file_to_write, file_to_write, compress_type=compression)
                os.remove(pytonium_binaries_path + file_to_write)
                open(pytonium_binaries_path + file_to_write, 'x').close()
                pytonium_bin_files.append(file_to_write)

            for file_to_write in locales_files:
                zf.write(pytonium_locales_path + file_to_write, "locales/" + file_to_write, compress_type=compression)
                os.remove(pytonium_locales_path + file_to_write)
                open(pytonium_locales_path + file_to_write, 'x').close()
                pytonium_bin_files.append("locales/" + file_to_write)

        except FileNotFoundError as e:
            print(f' *** Exception occurred during zip process - {e}')
        finally:
            zf.close()
    else:
        if is_pytonium_release_build:
            print("Building Pytonium Release")
            pytonium_files = ['./bin.zip']
        else:
            pytonium_files = []

        pytonium_binaries_path = "./Pytonium/bin/"
        binaries = [f for f in listdir(pytonium_binaries_path) if isfile(join(pytonium_binaries_path, f))]

        for file_to_write in binaries:
            os.remove(pytonium_binaries_path + file_to_write)
            open(pytonium_binaries_path + file_to_write, 'x').close()
            pytonium_bin_files.append(file_to_write)


        pytonium_locales_path = "./Pytonium/bin/locales/"
        locales_files = [f for f in listdir(pytonium_locales_path) if isfile(join(pytonium_locales_path, f))]

        for file_to_write in locales_files:
            os.remove(pytonium_locales_path + file_to_write)
            open(pytonium_locales_path + file_to_write, 'x').close()
            pytonium_bin_files.append("locales/" + file_to_write)
    return [pytonium_files, pytonium_bin_files]


cpp_flags = ['/std:c++20']
extensions = [
    Extension(name="Pytonium.src", sources=["./Pytonium/src/pytonium.pyx"],
              include_dirs=["./Pytonium/"],
              libraries=["user32", "libcef_dll_wrapper", "libcef", "pytonium_library"],
              library_dirs=["./Pytonium/src/lib/"],
              extra_compile_args=cpp_flags)

]


files_list = compress_binaries()

setup(
    name='Pytonium',
    author="Maximilian Winter",
    author_email = "maximilian.winter.91@gmail.com",
    cmdclass={'build_ext': build_ext},
    packages=['Pytonium', 'PytoniumTest', 'Pytonium.bin', "Pytonium.src", "Pytonium.src.pytonium_library",
              "Pytonium.src.include", "Pytonium.src.lib"],
    ext_modules=cythonize(extensions),
    include_package_data=True,
    package_data={
        'Pytonium': files_list[0],
        'PytoniumTest': ['./__init__.py', './main.py', './index.html',  './radioactive.ico'],
        'Pytonium.bin': files_list[1],
        'Pytonium.src': ["./pytonium.pyx"],
        "Pytonium.src.pytonium_library": ["./*.h"],
        "Pytonium.src.include": ["./**/*.h", "./*.h"],
        "Pytonium.src.lib": ["./*.lib"]
    }
)

pytonium_path = os.path.abspath(__file__)
pytonium_path = os.path.dirname(pytonium_path)
pytonium_path += "\\Pytonium"
pytonium_bin_zip_path = f'{pytonium_path}\\bin.zip'

if os.path.exists(pytonium_bin_zip_path):
    compression = zipfile.ZIP_LZMA
    with zipfile.ZipFile(pytonium_bin_zip_path, compression=compression, mode='r') as zip_ref:
        zip_ref.extractall(f'{pytonium_path}\\bin')
        zip_ref.close()
