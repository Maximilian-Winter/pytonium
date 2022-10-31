cmake_minimum_required(VERSION 3.19)
set(CMAKE_CONFIGURATION_TYPES Debug Release)
set(CMAKE_CXX_STANDARD 20)
project(pytonium)
set_property(GLOBAL PROPERTY OS_FOLDERS ON)

set(CEF_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/cef-binaries")
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CEF_ROOT}/cmake")

find_package(CEF REQUIRED)

add_subdirectory(${CEF_LIBCEF_DLL_WRAPPER_PATH} libcef_dll_wrapper)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src")
  add_subdirectory(src/cefwrapper)
  add_subdirectory(src/cefsubprocess)
endif()


if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/cefwrappertest")
  add_subdirectory(src/cefwrappertest)
endif()

PRINT_CEF_CONFIG()

