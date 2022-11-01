# Copyright (c) 2014 The Chromium Embedded Framework Authors. All rights
# reserved. Use of this source code is governed by a BSD-style license that
# can be found in the LICENSE file.

#
# Source files.
#

# cefsubprocess sources.
set(CEFSUB_SRCS
  )
set(CEFSUB_SRCS_WINDOWS
        cefsubprocess.cc
        )
APPEND_PLATFORM_SOURCES(CEFSUB_SRCS)
source_group(cefsubprocess FILES ${CEFSUB_SRCS})

set(CEFSUB_SRCS
  ${CEFSUB_SRCS}
  )


#
# Shared configuration.
#

# Target executable names.
set(CEF_TARGET "cefsubprocess")
if(OS_MAC)
  set(CEF_HELPER_TARGET "cefsub_Helper")
  set(CEF_HELPER_OUTPUT_NAME "cefsubprocess Helper")
else()
  # Logical target used to link the libcef library.
  ADD_LOGICAL_TARGET("libcef_lib" "${CEF_LIB_DEBUG}" "${CEF_LIB_RELEASE}")
endif()

# Determine the target output directory.
SET_CEF_TARGET_OUT_DIR()

if(OS_WINDOWS)

    # Add custom manifest files to an executable target.
    macro(ADD_WINDOWS_MANIFEST_ONE_PART manifest_path target extension)
        add_custom_command(
                TARGET ${target}
                POST_BUILD
                COMMAND "mt.exe" -nologo
                -manifest \"${manifest_path}/${target}.${extension}.manifest\"
                -outputresource:"${CEF_TARGET_OUT_DIR}/${target}.${extension}"\;\#1
                COMMENT "Adding manifest..."
        )
    endmacro()

endif(OS_WINDOWS)


#
# Windows configuration.
#
add_compile_definitions(_ITERATOR_DEBUG_LEVEL=0)
add_compile_definitions(symbol_level=2)
if(OS_WINDOWS)

  # Executable target.
  add_executable(${CEF_TARGET} WIN32 ${CEFSUB_SRCS})
  add_dependencies(${CEF_TARGET} cefwrapper)
  add_dependencies(${CEF_TARGET} libcef_dll_wrapper)
  SET_EXECUTABLE_TARGET_PROPERTIES(${CEF_TARGET})
  target_link_libraries(${CEF_TARGET} cefwrapper libcef_lib libcef_dll_wrapper ${CEF_STANDARD_LIBS})
  include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../..)
  if(USE_SANDBOX)
    # Logical target used to link the cef_sandbox library.
    ADD_LOGICAL_TARGET("cef_sandbox_lib" "${CEF_SANDBOX_LIB_DEBUG}" "${CEF_SANDBOX_LIB_RELEASE}")
    target_link_libraries(${CEF_TARGET} cef_sandbox_lib ${CEF_SANDBOX_STANDARD_LIBS})
  endif()

  # Add the custom manifest files to the executable.
  ADD_WINDOWS_MANIFEST_ONE_PART("${CMAKE_CURRENT_SOURCE_DIR}" "${CEF_TARGET}" "exe")

  # Copy binary and resource files to the target output directory.
  COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "${CEF_TARGET_OUT_DIR}")
  COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "${CEF_TARGET_OUT_DIR}")

 # COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "../cefwrappertest/debug/cefsubprocess/")
 # COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "../cefwrappertest/debug/cefsubprocess")
  #COPY_FILES("${CEF_TARGET}" "cefsubprocess.exe" "${CEF_TARGET_OUT_DIR}" "../cefwrappertest/debug/bin")
#
 # COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "../cefwrappertest/release/cefsubprocess/")
 # COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "../cefwrappertest/release/cefsubprocess")
  #COPY_FILES("${CEF_TARGET}" "cefsubprocess.exe" "${CEF_TARGET_OUT_DIR}" "../cefwrappertest/release/bin")





  #COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "../../../src/Pytonium_Dev/Pytonium/cefsubprocess/")
  #COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "../../../src/Pytonium_Dev/Pytonium/cefsubprocess/")
  #COPY_FILES("${CEF_TARGET}" "cefsubprocess.exe" "${CEF_TARGET_OUT_DIR}" "../../../src/Pytonium_Dev/Pytonium/bin/")
endif()
