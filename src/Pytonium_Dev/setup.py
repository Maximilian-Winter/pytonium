from Cython.Build import cythonize
from setuptools import setup, Extension, PackageFinder
from setuptools.command.build_ext import build_ext as build_ext

CPPFLAGS = ['/std:c++17']
extensions = [
    Extension(name="Pytonium.src", sources=["./Pytonium/src/pytonium.pyx"],
              include_dirs=["./Pytonium/"],
              libraries=["user32", "libcef_dll_wrapper", "libcef", "cefwrapper"],
              library_dirs=["./Pytonium/src/lib/"],
              extra_compile_args=CPPFLAGS)

]
setup(
    name='Pytonium',
    author="Maximilian Winter",
    author_email = "maximilian.winter.91@gmail.com",
    description="This is a python framework called Pytonium for building python apps with a GUI, based on web technologies. ",
    long_description="This is a python framework called Pytonium for building python apps with a GUI, based on web technologies. It uses the Chromium Embedded Framework for rendering and execution of javascript.\nAt the moment the framework has basic functionality for loading an url and add Javascript bindings, so a python function can be called from Javascript. And also Javascript can be executed, on the website, from python.",
    cmdclass={'build_ext': build_ext},
    packages=['Pytonium', "Pytonium.src"],
    ext_modules=cythonize(extensions),
    package_data={
        'Pytonium': ['./bin/*.exe', './bin/*.dll', './bin/*.dat', './bin/*.pak', './bin/*.bin', './bin/*.json',
                    # './cefsubprocess/*.exe', './cefsubprocess/*.dll', './cefsubprocess/*.dat',
                    # './cefsubprocess/*.pak', './cefsubprocess/*.bin', './cefsubprocess/*.json',
                     './bin/locales/*.pak'],
        'Pytonium.src': ["./pytonium.pyx", "./include/**/*.h", "./include/*.h", "./cefwrapper/*.h", "./lib/*.lib"]
    },

    zip_safe=False,
    version="0.0.1"
)
