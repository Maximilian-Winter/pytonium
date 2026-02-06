cmake_minimum_required(VERSION 3.19)
set(CMAKE_CONFIGURATION_TYPES Debug Release)
set(CMAKE_CXX_STANDARD 20)
project(pytonium)
set_property(GLOBAL PROPERTY OS_FOLDERS ON)

if(UNIX)
  set(CEF_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/cef-binaries-linux")
endif(UNIX)

if(WIN32)
  set(CEF_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/cef-binaries-windows")
endif(WIN32)
set(USE_SANDBOX OFF)
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CEF_ROOT}/cmake")

find_package(CEF REQUIRED)

add_subdirectory(${CEF_LIBCEF_DLL_WRAPPER_PATH} libcef_dll_wrapper)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src")
  add_subdirectory(src/pytonium_library)
  add_subdirectory(src/pytonium_subprocess)
endif()


if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/src/pytonium_library_test")
  add_subdirectory(src/pytonium_library_test)
endif()
set(CMAKE_CXX_STANDARD 20)
PRINT_CEF_CONFIG()

