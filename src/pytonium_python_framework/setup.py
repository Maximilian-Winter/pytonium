import os
import shutil
from typing import List

import os

is_sdist_release = False

if 'RELEASE_SDIST' in os.environ and os.environ.get("RELEASE_SDIST") == 1:
    is_sdist_release = True

pytonium_manifest_file_list = []
pytonium_packages = ['Pytonium']

if os.path.exists('./Pytonium/test/cache'):
    shutil.rmtree('./Pytonium/test/cache')

#def compress_binaries():
#    pytonium_files = []
#    pytonium_bin_files = []
#    if not isfile("./Pytonium/bin.zip") and is_pytonium_release_build:
#        print("Building Pytonium Release")
#        print("Creating Pytonium binaries zip file...")
#        pytonium_files = ['./bin.zip']
#        compression = zipfile.ZIP_LZMA
#        zf = zipfile.ZipFile("./Pytonium/bin.zip", mode="w")

#        pytonium_binaries_path = "./Pytonium/bin/"
#        binaries = [f for f in listdir(pytonium_binaries_path) if isfile(join(pytonium_binaries_path, f))]

#        pytonium_locales_path = "./Pytonium/bin/locales/"
#        locales_files = [f for f in listdir(pytonium_locales_path) if isfile(join(pytonium_locales_path, f))]
#        try:
#            for file_to_write in binaries:
#                zf.write(pytonium_binaries_path + file_to_write, file_to_write, compress_type=compression)
#                os.remove(pytonium_binaries_path + file_to_write)
#                open(pytonium_binaries_path + file_to_write, 'x').close()
#                pytonium_bin_files.append(file_to_write)

#            for file_to_write in locales_files:
#                zf.write(pytonium_locales_path + file_to_write, "locales/" + file_to_write,
#                         compress_type=compression)
#                os.remove(pytonium_locales_path + file_to_write)
#                open(pytonium_locales_path + file_to_write, 'x').close()
#                pytonium_bin_files.append("locales/" + file_to_write)

#        except FileNotFoundError as e:
#            print(f' *** Exception occurred during zip process - {e}')
#        finally:
#            zf.close()
#    else:
#        if is_pytonium_release_build:
#            print("Building Pytonium Release")
#            pytonium_files = ['./bin.zip']
#        else:

#            pytonium_files = []
#        print("Scanning the Pytonium binaries...")
#        pytonium_binaries_path = "./Pytonium/bin/"
#        binaries = [f for f in listdir(pytonium_binaries_path) if isfile(join(pytonium_binaries_path, f))]

#        for file_to_write in binaries:
#            if is_pytonium_release_build:
#                os.remove(pytonium_binaries_path + file_to_write)
#                open(pytonium_binaries_path + file_to_write, 'x').close()
#            pytonium_bin_files.append(file_to_write)

#        pytonium_locales_path = "./Pytonium/bin/locales/"
#        locales_files = [f for f in listdir(pytonium_locales_path) if isfile(join(pytonium_locales_path, f))]

#        for file_to_write in locales_files:
#            if is_pytonium_release_build:
#                os.remove(pytonium_locales_path + file_to_write)
#                open(pytonium_locales_path + file_to_write, 'x').close()
#            pytonium_bin_files.append("locales/" + file_to_write)
#    return [pytonium_files, pytonium_bin_files]


#cpp_flags = ['/std:c++20']
#extensions = [
#    Extension(name="Pytonium.src", sources=["./Pytonium/src/pytonium.pyx"],
#              include_dirs=["./Pytonium/"],
#              libraries=["user32", "libcef_dll_wrapper", "libcef", "pytonium_library"],
#              library_dirs=["./Pytonium/src/lib/"],
#              extra_compile_args=cpp_flags)

#]

#files_list = compress_binaries()

#setup(
#    name='Pytonium',
#    author="Maximilian Winter",
#    author_email="maximilian.winter.91@gmail.com",
#    cmdclass={'build_ext': build_ext},
#    packages=['Pytonium', 'PytoniumTest', 'Pytonium.bin', "Pytonium.src", "Pytonium.src.pytonium_library",
#              "Pytonium.src.include", "Pytonium.src.lib"],
#    ext_modules=cythonize(extensions),
#    include_package_data=True,
#    package_data={
#        'Pytonium': files_list[0],
#        'PytoniumTest': ['./__init__.py', './main.py', './index.html', './radioactive.ico'],
#        'Pytonium.bin': files_list[1],
#        'Pytonium.src': ["./pytonium.pyx"],
#        "Pytonium.src.pytonium_library": ["./*.h"],
#        "Pytonium.src.include": ["./**/*.h", "./*.h"],
#        "Pytonium.src.lib": ["./*"]
#    }
#)

#pytonium_path = os.path.abspath(__file__)
#pytonium_path = os.path.dirname(pytonium_path)
#pytonium_path += "/Pytonium"
#pytonium_bin_zip_path = f'{pytonium_path}/bin.zip'

#if os.path.exists(pytonium_bin_zip_path):
#    print("Extracting the Pytonium binaries...")
#    compression = zipfile.ZIP_LZMA
#    with zipfile.ZipFile(pytonium_bin_zip_path, compression=compression, mode='r') as zip_ref:
#        zip_ref.extractall(f'{pytonium_path}/bin')
#        zip_ref.close()

def generate_manifest_file():
    if is_sdist_release:
        for path in Path('./Pytonium').rglob('*'):
            if isfile(path):
                pytonium_manifest_file_list.append(str(path))
            else:
                pytonium_packages.append(str(path).replace("/", "."))
    else:
        pytonium_packages.append("Pytonium.bin")
        pytonium_packages.append("Pytonium.test")
        pytonium_packages.append("Pytonium.bin.locales")
        for path in Path('./Pytonium/bin').rglob('*'):
            if isfile(path):
                pytonium_manifest_file_list.append(str(path))

        for path in Path('./Pytonium/test').rglob('*'):
            if isfile(path):
                pytonium_manifest_file_list.append(str(path))

    with open('./MANIFEST.in', 'w') as fp:

        for item in pytonium_manifest_file_list:
            fp.write("include %s\n" % item)


if os.name == 'nt':
    from skbuild import setup
    from pathlib import Path
    from os.path import isfile

    if os.path.exists('./Pytonium/src/cef-binaries/Release/libcef.dll'):
        os.remove('./Pytonium/src/cef-binaries/Release/libcef.dll')

    if os.path.exists('./Pytonium/src/cef-binaries/Release/libcef.lib'):
        os.remove('./Pytonium/src/cef-binaries/Release/libcef.lib')

    generate_manifest_file()

    shutil.copyfile('./Pytonium/bin/libcef.dll', 'Pytonium/src/cef-binaries/Release/libcef.dll')
    shutil.copyfile('./Pytonium/bin/libcef.lib', 'Pytonium/src/cef-binaries/Release/libcef.lib')

    setup(
        name='Pytonium',
        packages=pytonium_packages,
        cmake_args=['-DUSE_SANDBOX:BOOL=OFF'],
        include_package_data=True
    )


if os.name == 'posix':
    from skbuild import setup
    from pathlib import Path
    from os.path import isfile
    from setuptools import Extension

    if os.path.exists('./Pytonium/src/cef-binaries/Release/libcef.so'):
        os.remove('./Pytonium/src/cef-binaries/Release/libcef.so')

    generate_manifest_file()

    shutil.copyfile('./Pytonium/bin/libcef.so', 'Pytonium/src/cef-binaries/Release/libcef.so')

    setup(
        name='Pytonium',
        packages=pytonium_packages,
        cmake_args=['-DUSE_SANDBOX:BOOL=OFF'],
        include_package_data=True
    )
