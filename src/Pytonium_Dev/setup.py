import os

from Cython.Build import cythonize
from setuptools import setup, Extension, PackageFinder
from setuptools.command.build_ext import build_ext as build_ext
import zipfile
from os import listdir
from os.path import isfile, join


def compress_binaries():
    if not os.path.isfile("Pytonium/bin.zip"):
        compression = zipfile.ZIP_LZMA
        zf = zipfile.ZipFile("Pytonium/bin.zip", mode="w")
        mypath = "./Pytonium/bin/"
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        mypath2 = "./Pytonium/bin/locales/"
        onlyfiles2 = [f for f in listdir(mypath2) if isfile(join(mypath2, f))]
        try:
            for file_to_write in onlyfiles:
                zf.write(mypath + file_to_write, file_to_write, compress_type=compression)

            for file_to_write in onlyfiles2:
                zf.write(mypath2 + file_to_write, "locales/" + file_to_write, compress_type=compression)

        except FileNotFoundError as e:
            print(f' *** Exception occurred during zip process - {e}')
        finally:
            zf.close()


class BuildExt(build_ext):
    def build_extension(self, ext):
        compress_binaries()
        super().build_extension(ext)


CPPFLAGS = ['/std:c++17']
extensions = [
    Extension(name="Pytonium.src", sources=["./Pytonium/src/pytonium.pyx"],
              include_dirs=["./Pytonium/"],
              libraries=["user32", "libcef_dll_wrapper", "libcef", "cefwrapper"],
              library_dirs=["./Pytonium/src/lib/"],
              extra_compile_args=CPPFLAGS)

]

compress_binaries()
setup(
    name='Pytonium',
    author="Maximilian Winter",
    author_email = "maximilian.winter.91@gmail.com",
    description="This is a python framework called Pytonium for building python apps with a GUI, based on web technologies. ",
    long_description="This is a python framework called Pytonium for building python apps with a GUI, based on web technologies. It uses the Chromium Embedded Framework for rendering and execution of javascript.\nAt the moment the framework has basic functionality for loading an url and add Javascript bindings, so a python function can be called from Javascript. And also Javascript can be executed, on the website, from python.",
    cmdclass={'build_ext': build_ext},
    packages=['Pytonium', 'PytoniumTests', 'Pytonium.bin', "Pytonium.src", "Pytonium.src.cefwrapper", "Pytonium.src.include", "Pytonium.src.lib"],
    ext_modules=cythonize(extensions),
    include_package_data=True,
    package_data={
        'Pytonium': ['./bin.zip'],
        'PytoniumTests': ['./__init__.py', './main.py', './index.html'],
        'Pytonium.src': ["./pytonium.pyx"],
        "Pytonium.src.cefwrapper": ["./*.h"],
        "Pytonium.src.include": ["./**/*.h", "./*.h"],
        "Pytonium.src.lib": ["./*.lib"]
    },
    version="0.0.4"
)
