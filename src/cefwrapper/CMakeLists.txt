# Copyright (c) 2014 The Chromium Embedded Framework Authors. All rights
# reserved. Use of this source code is governed by a BSD-style license that
# can be found in the LICENSE file.

#
# Source files.
#

# cefwrapper sources.
set(CEFSIMPLE_SRCS
        cef_wrapper_app.cc
        cef_wrapper_app.h
        cef_wrapper_client_handler.cc
        cef_wrapper_client_handler.h
        javascript_binding.h
        javascript_bindings_handler.h
        cef_wrapper_render_process_handler.cc
        cef_wrapper_render_process_handler.h
        library.cpp
        library.h
        cef_wrapper_browser_process_handler.h cef_wrapper_browser_process_handler.cc javascript_python_binding_handler.h custom_protocol_scheme_handler.h custom_protocol_scheme_handler.cc file_util.h)
set(CEFSIMPLE_SRCS_WINDOWS
        cef_wrapper_client_handler_win.cc
  )
APPEND_PLATFORM_SOURCES(CEFSIMPLE_SRCS)
source_group(cefwrapper FILES ${CEFSIMPLE_SRCS})

#
# Shared configuration.
#

# Target executable names.
set(CEF_TARGET "cefwrapper")
if(OS_MAC)
  set(CEF_HELPER_TARGET "cefsimple_Helper")
  set(CEF_HELPER_OUTPUT_NAME "cefsimple Helper")
else()
  # Logical target used to link the libcef library.
  ADD_LOGICAL_TARGET("libcef_lib" "${CEF_LIB_DEBUG}" "${CEF_LIB_RELEASE}")
endif()

# Determine the target output directory.
SET_CEF_TARGET_OUT_DIR()


add_compile_definitions(_ITERATOR_DEBUG_LEVEL=0)
#
# Windows configuration.
#
if(OS_WINDOWS)
  # Executable target.
  add_library(${CEF_TARGET} STATIC ${CEFSIMPLE_SRCS})
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
  COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "../../../src/Pytonium_Dev/Pytonium/bin/")
  COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "../../../src/Pytonium_Dev/Pytonium/bin/")

  COPY_SINGLE_FILE(${CEF_TARGET} "./Release/cefwrapper.lib" "../../../src/Pytonium_Dev/Pytonium/src/lib/cefwrapper.lib")
  COPY_SINGLE_FILE(${CEF_TARGET} "../../../cef-binaries/Release/libcef.lib" "../../../src/Pytonium_Dev/Pytonium/src/lib/libcef.lib")
  COPY_SINGLE_FILE(${CEF_TARGET} "../../libcef_dll_wrapper/Release/libcef_dll_wrapper.lib" "../../../src/Pytonium_Dev/Pytonium/src/lib/libcef_dll_wrapper.lib")
  add_custom_command(TARGET "${CEF_TARGET}" POST_BUILD
          COMMAND ${CMAKE_COMMAND} -E copy_directory
          ${CMAKE_SOURCE_DIR}/cef-binaries/include/ ${CMAKE_SOURCE_DIR}/src/Pytonium_Dev/Pytonium/src/include/)
  add_custom_command(TARGET "${CEF_TARGET}" POST_BUILD
          COMMAND ${CMAKE_COMMAND} -E copy_directory
          ${CMAKE_SOURCE_DIR}/src/cefwrapper/ ${CMAKE_SOURCE_DIR}/src/Pytonium_Dev/Pytonium/src/cefwrapper/)
endif()
