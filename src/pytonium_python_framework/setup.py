import shutil
import os
from skbuild import setup
from os import listdir
from pathlib import Path
from os.path import isfile, join
import zipfile

linux_bin_folder = "bin_linux"
windows_bin_folder = "bin_win"
is_sdist_release = False

if 'RELEASE_SDIST' in os.environ:
    is_sdist_release = True

pytonium_manifest_file_list = []
pytonium_packages = ['Pytonium']

if os.path.exists('./Pytonium/test/cache'):
    shutil.rmtree('./Pytonium/test/cache')


def compress_binaries(os_bin_folder):
    if not isfile(f"./Pytonium/{os_bin_folder}.zip") and is_sdist_release:
        print("Building Pytonium Release")
        print("Creating Pytonium binaries zip file...")
        compression_out = zipfile.ZIP_LZMA
        linux_bin_zip_file = zipfile.ZipFile(f"./Pytonium/{os_bin_folder}.zip", mode="w")

        pytonium_binaries_path = f"./Pytonium/{os_bin_folder}/"
        binaries = [f for f in listdir(pytonium_binaries_path) if isfile(join(pytonium_binaries_path, f))]

        pytonium_locales_path = f"./Pytonium/{os_bin_folder}/locales/"
        locales_files = [f for f in listdir(pytonium_locales_path) if isfile(join(pytonium_locales_path, f))]
        try:
            for file_to_write in binaries:
                linux_bin_zip_file.write(pytonium_binaries_path + file_to_write, file_to_write, compress_type=compression_out)
                os.remove(pytonium_binaries_path + file_to_write)
                open(pytonium_binaries_path + file_to_write, 'x').close()

            for file_to_write in locales_files:
                linux_bin_zip_file.write(pytonium_locales_path + file_to_write, "locales/" + file_to_write,
                         compress_type=compression_out)
                os.remove(pytonium_locales_path + file_to_write)
                open(pytonium_locales_path + file_to_write, 'x').close()

        except FileNotFoundError as e:
            print(f' *** Exception occurred during zip process - {e}')
        finally:
            linux_bin_zip_file.close()
    else:
        print("Scanning the Pytonium binaries...")
        pytonium_binaries_path = f"./Pytonium/{os_bin_folder}/"
        binaries = [f for f in listdir(pytonium_binaries_path) if isfile(join(pytonium_binaries_path, f))]

        for file_to_write in binaries:
            if is_sdist_release:
                os.remove(pytonium_binaries_path + file_to_write)
                open(pytonium_binaries_path + file_to_write, 'x').close()

        pytonium_locales_path = f"./Pytonium/{os_bin_folder}/locales/"
        locales_files = [f for f in listdir(pytonium_locales_path) if isfile(join(pytonium_locales_path, f))]

        for file_to_write in locales_files:
            if is_sdist_release:
                os.remove(pytonium_locales_path + file_to_write)
                open(pytonium_locales_path + file_to_write, 'x').close()


def generate_package_list_and_manifest_file_list(os_bin_folder):
    if is_sdist_release:
        pytonium_manifest_file_list.append(f'./Pytonium/{os_bin_folder}.zip')
        pytonium_manifest_file_list.append("CMakeLists.txt")
        for path in Path('./Pytonium').rglob('*'):
            if isfile(path):
                pytonium_manifest_file_list.append(str(path))
            else:
                pytonium_packages.append(str(path).replace("/", "."))
    else:
        pytonium_manifest_file_list.append(f'./Pytonium/{os_bin_folder}.zip')
        pytonium_packages.append(f"Pytonium.{os_bin_folder}")
        pytonium_packages.append("Pytonium.test")
        pytonium_packages.append(f"Pytonium.{os_bin_folder}.locales")
        for path in Path(f'./Pytonium/{os_bin_folder}').rglob('*'):
            if os.name == 'nt':
                if isfile(path) and not str(path).endswith('.so'):
                    pytonium_manifest_file_list.append(str(path))
            else:
                if isfile(path) and not str(path).endswith('.dll'):
                    pytonium_manifest_file_list.append(str(path))

        for path in Path('./Pytonium/test').rglob('*'):
            if isfile(path):
                pytonium_manifest_file_list.append(str(path))


def generate_manifest_file():
    with open('./MANIFEST.in', 'w') as fp:

        for item in pytonium_manifest_file_list:
            fp.write("include %s\n" % item)


def extract_bin_zip(bin_folder):
    pytonium_path = os.path.abspath(__file__)
    pytonium_path = os.path.dirname(pytonium_path)
    pytonium_path += "/Pytonium"
    pytonium_bin_zip_path = f'{pytonium_path}/{bin_folder}.zip'

    if os.path.exists(pytonium_bin_zip_path):
        print("Extracting the Pytonium binaries...")
        compression = zipfile.ZIP_LZMA
        with zipfile.ZipFile(pytonium_bin_zip_path, compression=compression, mode='r') as zip_ref:
            zip_ref.extractall(f'{pytonium_path}/{bin_folder}')
            zip_ref.close()


if is_sdist_release:
    extract_bin_zip("bin_linux")
    extract_bin_zip("bin_win")
else:
    if os.name == "nt":
        extract_bin_zip("bin_win")
    else:
        extract_bin_zip("bin_linux")


if os.path.exists('./Pytonium/src/cef-binaries-linux/Release/libcef.so'):
    os.remove('./Pytonium/src/cef-binaries-linux/Release/libcef.so')

if is_sdist_release:
    generate_package_list_and_manifest_file_list("bin_win")
    generate_package_list_and_manifest_file_list("bin_linux")
else:
    if os.name == "nt":
        generate_package_list_and_manifest_file_list("bin_win")
    else:
        generate_package_list_and_manifest_file_list("bin_linux")

generate_manifest_file()

if is_sdist_release:
    compress_binaries("bin_win")
    compress_binaries("bin_linux")
else:
    if os.name == "nt":
        compress_binaries("bin_win")
    else:
        compress_binaries("bin_linux")


shutil.copyfile('./Pytonium/bin_linux/libcef.so', 'Pytonium/src/cef-binaries-linux/Release/libcef.so')

setup(
    name='Pytonium',
    packages=pytonium_packages,
    cmake_args=['-DUSE_SANDBOX=OFF'],
    include_package_data=True
)

if is_sdist_release:
    extract_bin_zip("bin_linux")
    extract_bin_zip("bin_win")
else:
    if os.name == "nt":
        extract_bin_zip("bin_win")
    else:
        extract_bin_zip("bin_linux")




#import shutil
#import os
#from skbuild import setup
#from os import listdir
#from pathlib import Path
#from os.path import isfile, join
#import zipfile
#
#is_sdist_release = False
#
#if 'RELEASE_SDIST' in os.environ:
#    is_sdist_release = True
#
#pytonium_manifest_file_list = []
#pytonium_packages = ['Pytonium']
#
#if os.path.exists('./Pytonium/test/cache'):
#    shutil.rmtree('./Pytonium/test/cache')
#
#
#def compress_binaries(bin_folder):
#    if not isfile(f"./Pytonium/{bin_folder}.zip") and is_sdist_release:
#        print("Building Pytonium Release")
#        print("Creating Pytonium binaries zip file...")
#        compression_out = zipfile.ZIP_LZMA
#        zf = zipfile.ZipFile(f"./Pytonium/{bin_folder}.zip", mode="w")
#
#        pytonium_binaries_path = f"./Pytonium/{bin_folder}/"
#        binaries = [f for f in os.listdir(pytonium_binaries_path) if isfile(join(pytonium_binaries_path, f))]
#
#        pytonium_locales_path = f"./Pytonium/{bin_folder}/locales/"
#        locales_files = [f for f in os.listdir(pytonium_locales_path) if isfile(join(pytonium_locales_path, f))]
#        try:
#            for file_to_write in binaries:
#                zf.write(pytonium_binaries_path + file_to_write, file_to_write, compress_type=compression_out)
#                os.remove(pytonium_binaries_path + file_to_write)
#                open(pytonium_binaries_path + file_to_write, 'x').close()
#
#            for file_to_write in locales_files:
#                zf.write(pytonium_locales_path + file_to_write, "locales/" + file_to_write,
#                         compress_type=compression_out)
#                os.remove(pytonium_locales_path + file_to_write)
#                open(pytonium_locales_path + file_to_write, 'x').close()
#
#        except FileNotFoundError as e:
#            print(f' *** Exception occurred during zip process - {e}')
#        finally:
#            zf.close()
#    else:
#        if is_sdist_release:
#            print("Scanning the Pytonium binaries...")
#            pytonium_binaries_path = f"./Pytonium/{bin_folder}/"
#            binaries = [f for f in os.listdir(pytonium_binaries_path) if isfile(join(pytonium_binaries_path, f))]
#
#            for file_to_write in binaries:
#                if is_sdist_release:
#                    os.remove(pytonium_binaries_path + file_to_write)
#                    open(pytonium_binaries_path + file_to_write, 'x').close()
#
#            pytonium_locales_path = f"./Pytonium/{bin_folder}/locales/"
#            locales_files = [f for f in os.listdir(pytonium_locales_path) if isfile(join(pytonium_locales_path, f))]
#
#            for file_to_write in locales_files:
#                if is_sdist_release:
#                    os.remove(pytonium_locales_path + file_to_write)
#                    open(pytonium_locales_path + file_to_write, 'x').close()
#
#
#def generate_manifest_file():
#    if is_sdist_release:
#        pytonium_manifest_file_list.append('Pytonium/bin_win.zip')
#        pytonium_manifest_file_list.append('Pytonium/bin_linux.zip')
#        pytonium_manifest_file_list.append("CMakeLists.txt")
#        for path in Path('./Pytonium').rglob('*'):
#            if isfile(path):
#                pytonium_manifest_file_list.append(str(path))
#            else:
#                pytonium_packages.append(str(path).replace("/", "."))
#    else:
#
#        if os.name == "nt":
#            os_bin_folder = "bin_win"
#            pytonium_manifest_file_list.append('Pytonium/bin_win.zip')
#
#        else:
#            os_bin_folder = "bin_linux"
#            pytonium_manifest_file_list.append('Pytonium/bin_linux.zip')
#
#        pytonium_packages.append(f"Pytonium.{os_bin_folder}")
#        pytonium_packages.append("Pytonium.test")
#        pytonium_packages.append(f"Pytonium.{os_bin_folder}.locales")
#        for path in Path(f'./Pytonium/{os_bin_folder}').rglob('*'):
#            if os.name == 'nt':
#                if isfile(path) and not str(path).endswith('.so'):
#                    pytonium_manifest_file_list.append(str(path))
#            else:
#                if isfile(path) and not str(path).endswith('.dll'):
#                    pytonium_manifest_file_list.append(str(path))
#
#        for path in Path('./Pytonium/test').rglob('*'):
#            if isfile(path):
#                pytonium_manifest_file_list.append(str(path))
#
#    with open('./MANIFEST.in', 'w') as fp:
#
#        for item in pytonium_manifest_file_list:
#            fp.write("include %s\n" % item)
#
#
#if os.path.exists('./Pytonium/src/cef-binaries-linux/Release/libcef.so'):
#    os.remove('./Pytonium/src/cef-binaries-linux/Release/libcef.so')
#
#generate_manifest_file()
#shutil.copyfile('./Pytonium/bin_linux/libcef.so', './Pytonium/src/cef-binaries-linux/Release/libcef.so')
#
#if is_sdist_release:
#    compress_binaries("bin_win")
#    compress_binaries("bin_linux")
#else:
#    if os.name == "nt":
#        compress_binaries("bin_win")
#    else:
#        compress_binaries("bin_linux")
#
#setup(
#    name='Pytonium',
#    packages=pytonium_packages,
#    cmake_args=['-DUSE_SANDBOX=OFF'],
#    include_package_data=True
#)
#
#pytonium_path = os.path.abspath(__file__)
#pytonium_path = os.path.dirname(pytonium_path)
#
#if is_sdist_release:
#    pytonium_bin_zip_path = f'{pytonium_path}/bin_win.zip'
#    if os.path.exists(pytonium_bin_zip_path):
#        compression = zipfile.ZIP_LZMA
#        with zipfile.ZipFile(pytonium_bin_zip_path, compression=compression, mode='r') as zip_ref:
#            zip_ref.extractall(f'{pytonium_path}/bin_win')
#            zip_ref.close()
#
#    pytonium_bin_zip_path = f'{pytonium_path}/bin_linux.zip'
#    if os.path.exists(pytonium_bin_zip_path):#
#        compression = zipfile.ZIP_LZMA
#        with zipfile.ZipFile(pytonium_bin_zip_path, compression=compression, mode='r') as zip_ref:
#            zip_ref.extractall(f'{pytonium_path}/bin_linux')
#            zip_ref.close()
#
#else:
#
#    if os.name == "nt":
#        os_bin_folder = "bin_win"
#    else:
#        os_bin_folder = "bin_linux"
#
#    pytonium_bin_zip_path = f'{pytonium_path}/{os_bin_folder}.zip'
#    if os.path.exists(pytonium_bin_zip_path):
#        compression = zipfile.ZIP_LZMA
#        with zipfile.ZipFile(pytonium_bin_zip_path, compression=compression, mode='r') as zip_ref:
#            zip_ref.extractall(f'{pytonium_path}/{os_bin_folder}')
#            zip_ref.close()
#