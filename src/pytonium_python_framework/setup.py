import os
import shutil
import sys
from typing import List

import os

is_sdist_release = False

if 'RELEASE_SDIST' in os.environ:
    is_sdist_release = True

pytonium_manifest_file_list = []
pytonium_packages = ['Pytonium']

if os.path.exists('./Pytonium/test/cache'):
    shutil.rmtree('./Pytonium/test/cache')


def generate_manifest_file():
    if is_sdist_release:
        pytonium_manifest_file_list.append("CMakeLists.txt")
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
