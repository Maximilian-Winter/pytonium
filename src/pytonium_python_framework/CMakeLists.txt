cmake_minimum_required(VERSION 3.3.0)
project(Pytonium)
set(CMAKE_CXX_STANDARD 20)
set_property(GLOBAL PROPERTY OS_FOLDERS ON)

if(UNIX)
    set(CEF_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/Pytonium/src/cef-binaries-linux")
endif(UNIX)

if(WIN32)
    set(CEF_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/Pytonium/src/cef-binaries-windows")
endif(WIN32)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CEF_ROOT}/cmake")

find_package(CEF REQUIRED)

add_subdirectory(${CEF_LIBCEF_DLL_WRAPPER_PATH} libcef_dll_wrapper)


add_subdirectory(Pytonium/src/pytonium_library)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/Pytonium ${CMAKE_CURRENT_SOURCE_DIR}/Pytonium/src)

add_subdirectory(Pytonium/src)