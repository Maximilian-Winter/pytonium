import os

from Cython.Build import cythonize
from setuptools import setup, Extension, PackageFinder
from setuptools.command.build_ext import build_ext as build_ext
import zipfile
from os import listdir
from os.path import isfile, join


def compress_binaries():
    if not os.path.isfile("./Pytonium/bin.zip"):
        compression = zipfile.ZIP_LZMA
        zf = zipfile.ZipFile("./Pytonium/bin.zip", mode="w")

        pytonium_binaries_path = "./Pytonium/bin/"
        binaries = [f for f in listdir(pytonium_binaries_path) if isfile(join(pytonium_binaries_path, f))]

        pytonium_locales_path = "./Pytonium/bin/locales/"
        locales_files = [f for f in listdir(pytonium_locales_path) if isfile(join(pytonium_locales_path, f))]
        try:
            for file_to_write in binaries:
                zf.write(pytonium_binaries_path + file_to_write, file_to_write, compress_type=compression)

            for file_to_write in locales_files:
                zf.write(pytonium_locales_path + file_to_write, "locales/" + file_to_write, compress_type=compression)

        except FileNotFoundError as e:
            print(f' *** Exception occurred during zip process - {e}')
        finally:
            zf.close()


class BuildExt(build_ext):
    def build_extension(self, ext):
        compress_binaries()
        super().build_extension(ext)


cpp_flags = ['/std:c++20']
extensions = [
    Extension(name="Pytonium.src", sources=["./Pytonium/src/pytonium.pyx"],
              include_dirs=["./Pytonium/"],
              libraries=["user32", "libcef_dll_wrapper", "libcef", "cefwrapper"],
              library_dirs=["./Pytonium/src/lib/"],
              extra_compile_args=cpp_flags)

]

compress_binaries()
setup(
    name='Pytonium',
    author="Maximilian Winter",
    author_email = "maximilian.winter.91@gmail.com",
    description="This is a python framework called Pytonium for building python apps with a GUI, based on web technologies. ",
    long_description="This is a python framework called Pytonium for building python apps with a GUI, based on web technologies. It uses the Chromium Embedded Framework for rendering and execution of javascript.\nAt the moment the framework has basic functionality for loading an url and add Javascript bindings, so a python function can be called from Javascript. And also Javascript can be executed, on the website, from python.",
    cmdclass={'build_ext': build_ext},
    packages=['Pytonium', 'PytoniumTests', 'Pytonium.bin', "Pytonium.src", "Pytonium.src.cefwrapper",
              "Pytonium.src.include", "Pytonium.src.lib"],
    ext_modules=cythonize(extensions),
    include_package_data=True,
    package_data={
        'Pytonium': ['./bin.zip'],
        'PytoniumTests': ['./__init__.py', './main.py', './index.html'],
        'Pytonium.src': ["./pytonium.pyx"],
        "Pytonium.src.cefwrapper": ["./*.h"],
        "Pytonium.src.include": ["./**/*.h", "./*.h"],
        "Pytonium.src.lib": ["./*.lib"]
    }
)
