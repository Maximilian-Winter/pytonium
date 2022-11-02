# Copyright (c) 2014 The Chromium Embedded Framework Authors. All rights
# reserved. Use of this source code is governed by a BSD-style license that
# can be found in the LICENSE file.

#
# Source files.
#

# pytonium_library sources.
set(PYTONIUM_LIBRARY_SRCS
        cef_wrapper_app.cc
        cef_wrapper_app.h
        cef_wrapper_client_handler.cc
        cef_wrapper_client_handler.h
        javascript_binding.h
        javascript_bindings_handler.h
        cef_wrapper_render_process_handler.cc
        cef_wrapper_render_process_handler.h
        pytonium_library.cpp
        pytonium_library.h
        cef_wrapper_browser_process_handler.h cef_wrapper_browser_process_handler.cc javascript_python_binding_handler.h custom_protocol_scheme_handler.h custom_protocol_scheme_handler.cc file_util.h)
set(PYTONIUM_LIBRARY_SRCS_WINDOWS
        cef_wrapper_client_handler_win.cc
  )
APPEND_PLATFORM_SOURCES(PYTONIUM_LIBRARY_SRCS)
source_group(pytonium_library FILES ${PYTONIUM_LIBRARY_SRCS})


# Target executable names.
set(CEF_TARGET "pytonium_library")

# Determine the target output directory.
SET_CEF_TARGET_OUT_DIR()

ADD_LOGICAL_TARGET("libcef_lib" "${CEF_LIB_DEBUG}" "${CEF_LIB_RELEASE}")

add_compile_definitions(_ITERATOR_DEBUG_LEVEL=0)
#
# Windows configuration.
#
if(OS_WINDOWS)
  # Executable target.
  add_library(${CEF_TARGET} STATIC ${PYTONIUM_LIBRARY_SRCS})
  SET_LIBRARY_TARGET_PROPERTIES(${CEF_TARGET})
  add_dependencies(${CEF_TARGET} libcef_dll_wrapper)
  target_include_directories(${CEF_TARGET} PUBLIC ${CEF_INCLUDE_PATH})
  target_link_libraries(${CEF_TARGET} libcef_lib libcef_dll_wrapper ${CEF_STANDARD_LIBS})
  add_compile_definitions(symbol_level=2)
  if(USE_SANDBOX)
    # Logical target used to link the cef_sandbox library.
    ADD_LOGICAL_TARGET("cef_sandbox_lib" "${CEF_SANDBOX_LIB_DEBUG}" "${CEF_SANDBOX_LIB_RELEASE}")
    target_link_libraries(${CEF_TARGET} cef_sandbox_lib ${CEF_SANDBOX_STANDARD_LIBS})
  endif()

  # Add the custom manifest files to the executable.
  #ADD_WINDOWS_MANIFEST("${CMAKE_CURRENT_SOURCE_DIR}" "${CEF_TARGET}" "exe")

  # Copy binary and resource files to the target output directory.
  #COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "${CEF_TARGET_OUT_DIR}")
  COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "../../../src/pytonium_python_framework/Pytonium/bin/")
  COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "../../../src/pytonium_python_framework/Pytonium/bin/")

  COPY_SINGLE_FILE(${CEF_TARGET} "./Release/pytonium_library.lib" "../../../src/pytonium_python_framework/Pytonium/src/lib/pytonium_library.lib")
  COPY_SINGLE_FILE(${CEF_TARGET} "../../../cef-binaries/Release/libcef.lib" "../../../src/pytonium_python_framework/Pytonium/src/lib/libcef.lib")
  COPY_SINGLE_FILE(${CEF_TARGET} "../../libcef_dll_wrapper/Release/libcef_dll_wrapper.lib" "../../../src/pytonium_python_framework/Pytonium/src/lib/libcef_dll_wrapper.lib")
  add_custom_command(TARGET "${CEF_TARGET}" POST_BUILD
          COMMAND ${CMAKE_COMMAND} -E copy_directory
          ${CMAKE_SOURCE_DIR}/cef-binaries/include/ ${CMAKE_SOURCE_DIR}/src/pytonium_python_framework/Pytonium/src/include/)
  add_custom_command(TARGET "${CEF_TARGET}" POST_BUILD
          COMMAND ${CMAKE_COMMAND} -E copy_directory
          ${CMAKE_SOURCE_DIR}/src/pytonium_library/ ${CMAKE_SOURCE_DIR}/src/pytonium_python_framework/Pytonium/src/pytonium_library/)
endif()


if(OS_LINUX)
  add_library(${CEF_TARGET} STATIC ${PYTONIUM_LIBRARY_SRCS})
  SET_LIBRARY_TARGET_PROPERTIES(${CEF_TARGET})
  add_dependencies(${CEF_TARGET} libcef_dll_wrapper)
  target_include_directories(${CEF_TARGET} PUBLIC ${CEF_INCLUDE_PATH})
  target_link_libraries(${CEF_TARGET} libcef_lib libcef_dll_wrapper ${CEF_STANDARD_LIBS})
  add_compile_definitions(symbol_level=2)
  if(USE_SANDBOX)
    # Logical target used to link the cef_sandbox library.
    ADD_LOGICAL_TARGET("cef_sandbox_lib" "${CEF_SANDBOX_LIB_DEBUG}" "${CEF_SANDBOX_LIB_RELEASE}")
    target_link_libraries(${CEF_TARGET} cef_sandbox_lib ${CEF_SANDBOX_STANDARD_LIBS})
  endif()

  # Add the custom manifest files to the executable.
  #ADD_WINDOWS_MANIFEST("${CMAKE_CURRENT_SOURCE_DIR}" "${CEF_TARGET}" "exe")

  # Copy binary and resource files to the target output directory.
  #COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "${CEF_TARGET_OUT_DIR}")
  COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "../../../src/pytonium_python_framework/Pytonium/bin/")
  COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "../../../src/pytonium_python_framework/Pytonium/bin/")

  COPY_SINGLE_FILE(${CEF_TARGET} "./Release/pytonium_library.lib" "../../../src/pytonium_python_framework/Pytonium/src/lib/pytonium_library.lib")
  COPY_SINGLE_FILE(${CEF_TARGET} "../../../cef-binaries/Release/libcef.lib" "../../../src/pytonium_python_framework/Pytonium/src/lib/libcef.lib")
  COPY_SINGLE_FILE(${CEF_TARGET} "../../libcef_dll_wrapper/Release/libcef_dll_wrapper.lib" "../../../src/pytonium_python_framework/Pytonium/src/lib/libcef_dll_wrapper.lib")
  add_custom_command(TARGET "${CEF_TARGET}" POST_BUILD
          COMMAND ${CMAKE_COMMAND} -E copy_directory
          ${CMAKE_SOURCE_DIR}/cef-binaries/include/ ${CMAKE_SOURCE_DIR}/src/pytonium_python_framework/Pytonium/src/include/)
  add_custom_command(TARGET "${CEF_TARGET}" POST_BUILD
          COMMAND ${CMAKE_COMMAND} -E copy_directory
          ${CMAKE_SOURCE_DIR}/src/pytonium_library/ ${CMAKE_SOURCE_DIR}/src/pytonium_python_framework/Pytonium/src/pytonium_library/)
endif()