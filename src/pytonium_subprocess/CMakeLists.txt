# Copyright (c) 2014 The Chromium Embedded Framework Authors. All rights
# reserved. Use of this source code is governed by a BSD-style license that
# can be found in the LICENSE file.

#
# Source files.
#

# pytonium_subprocess sources.
set(PYTONIUM_SUB_SRCS
  )
set(PYTONIUM_SUB_SRCS_WINDOWS
        pytonium_subprocess.cc
        )
set(PYTONIUM_SUB_SRCS_LINUX
        pytonium_subprocess_linux.cc
        )
APPEND_PLATFORM_SOURCES(PYTONIUM_SUB_SRCS)
source_group(pytonium_subprocess FILES ${PYTONIUM_SUB_SRCS})

set(PYTONIUM_SUB_SRCS
  ${PYTONIUM_SUB_SRCS}
  )


#
# Shared configuration.
#

# Target executable names.
set(CEF_TARGET "pytonium_subprocess")


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

ADD_LOGICAL_TARGET("libcef_lib" "${CEF_LIB_DEBUG}" "${CEF_LIB_RELEASE}")
#
# Windows configuration.
#
add_compile_definitions(_ITERATOR_DEBUG_LEVEL=0)
add_compile_definitions(symbol_level=2)
if(OS_WINDOWS)

  # Executable target.
  add_executable(${CEF_TARGET} WIN32 ${PYTONIUM_SUB_SRCS})
  SET_EXECUTABLE_TARGET_PROPERTIES(${CEF_TARGET})
  add_dependencies(${CEF_TARGET} libcef_dll_wrapper)
  add_dependencies(${CEF_TARGET} pytonium_library)
  target_include_directories(${CEF_TARGET} PUBLIC ${CEF_INCLUDE_PATH})
  target_link_libraries(${CEF_TARGET} pytonium_library libcef_lib libcef_dll_wrapper ${CEF_STANDARD_LIBS})
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

 # COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "../pytonium_cpp_librarytest/debug/pytonium_subprocess/")
 # COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "../pytonium_cpp_librarytest/debug/pytonium_subprocess")
 COPY_FILES("${CEF_TARGET}" "pytonium_subprocess.exe" "${CEF_TARGET_OUT_DIR}" "../pytonium_library_test/debug/bin")
#
 # COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "../pytonium_cpp_librarytest/release/pytonium_subprocess/")
 # COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "../pytonium_cpp_librarytest/release/pytonium_subprocess")
 COPY_FILES("${CEF_TARGET}" "pytonium_subprocess.exe" "${CEF_TARGET_OUT_DIR}" "../pytonium_library_test/release/bin")



  COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "../../../src/pytonium_python_framework/Pytonium/bin_win/")
  COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "../../../src/pytonium_python_framework/Pytonium/bin_win/")

  #COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "../../../src/pytonium_python_framework/PytoniumLibrary/pytonium_subprocess/")
  #COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "../../../src/pytonium_python_framework/PytoniumLibrary/pytonium_subprocess/")
  COPY_FILES("${CEF_TARGET}" "pytonium_subprocess.exe" "${CEF_TARGET_OUT_DIR}" "../../../src/pytonium_python_framework/Pytonium/bin_win/")
endif()

if(OS_LINUX)

    # Executable target.
    add_executable(${CEF_TARGET} ${PYTONIUM_SUB_SRCS})
    SET_EXECUTABLE_TARGET_PROPERTIES(${CEF_TARGET})
    add_dependencies(${CEF_TARGET} libcef_dll_wrapper)
    add_dependencies(${CEF_TARGET} pytonium_library)
    target_include_directories(${CEF_TARGET} PUBLIC ${CEF_INCLUDE_PATH})
    target_link_libraries(${CEF_TARGET} pytonium_library libcef_lib libcef_dll_wrapper ${CEF_STANDARD_LIBS})
    include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../..)
    # Set rpath so that libraries can be placed next to the executable.
    set_target_properties(${CEF_TARGET} PROPERTIES INSTALL_RPATH "$ORIGIN")
    set_target_properties(${CEF_TARGET} PROPERTIES BUILD_WITH_INSTALL_RPATH TRUE)
    set_target_properties(${CEF_TARGET} PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CEF_TARGET_OUT_DIR})

    # Copy binary and resource files to the target output directory.
    COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "${CEF_TARGET_OUT_DIR}")
    COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "${CEF_TARGET_OUT_DIR}")
    if (EXISTS "${CEF_BINARY_DIR}/libminigbm.so")
        COPY_FILES("${CEF_TARGET}" "libminigbm.so" "${CEF_BINARY_DIR}" "${CEF_TARGET_OUT_DIR}")
    endif()
    if(USE_SANDBOX)
        # Logical target used to link the cef_sandbox library.
        ADD_LOGICAL_TARGET("cef_sandbox_lib" "${CEF_SANDBOX_LIB_DEBUG}" "${CEF_SANDBOX_LIB_RELEASE}")
        target_link_libraries(${CEF_TARGET} cef_sandbox_lib ${CEF_SANDBOX_STANDARD_LIBS})
    endif()
    # Set SUID permissions on the chrome-sandbox target.
    SET_LINUX_SUID_PERMISSIONS("${CEF_TARGET}" "${CEF_TARGET_OUT_DIR}/chrome-sandbox")
#
    ## COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "../pytonium_cpp_librarytest/debug/pytonium_subprocess/")
    ## COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "../pytonium_cpp_librarytest/debug/pytonium_subprocess")
    COPY_FILES("${CEF_TARGET}" "pytonium_subprocess" "${CEF_TARGET_OUT_DIR}" "../pytonium_library_test/debug")
    ##
    ## COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "../pytonium_cpp_librarytest/release/pytonium_subprocess/")
    ## COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "../pytonium_cpp_librarytest/release/pytonium_subprocess")
    COPY_FILES("${CEF_TARGET}" "pytonium_subprocess" "${CEF_TARGET_OUT_DIR}" "../pytonium_library_test/release")
#
#
#
    COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "../../../src/pytonium_python_framework/Pytonium/bin_linux/")
    COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "../../../src/pytonium_python_framework/Pytonium/bin_linux/")
#
    ##COPY_FILES("${CEF_TARGET}" "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "../../../src/pytonium_python_framework/PytoniumLibrary/pytonium_subprocess/")
    ##COPY_FILES("${CEF_TARGET}" "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "../../../src/pytonium_python_framework/PytoniumLibrary/pytonium_subprocess/")
    COPY_FILES("${CEF_TARGET}" "pytonium_subprocess" "${CEF_TARGET_OUT_DIR}" "../../../src/pytonium_python_framework/Pytonium/bin_linux/")
endif()