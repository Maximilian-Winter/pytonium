# Determine the target output directory.
set(CEF_TARGET "pytonium_library_test")
SET_CEF_TARGET_OUT_DIR()
if(OS_WINDOWS)

add_executable(${CEF_TARGET} main.cpp)
SET_EXECUTABLE_TARGET_PROPERTIES(${CEF_TARGET})
add_dependencies(${CEF_TARGET} pytonium_library)
target_link_libraries(${CEF_TARGET} PUBLIC pytonium_library)

add_compile_definitions(symbol_level=2)
add_compile_definitions(_ITERATOR_DEBUG_LEVEL=0)
include_directories(${CEF_INCLUDE_PATH})

COPY_FILES(${CEF_TARGET} "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "${CEF_TARGET_OUT_DIR}")
COPY_FILES(${CEF_TARGET} "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "${CEF_TARGET_OUT_DIR}")
COPY_SINGLE_FILE(${CEF_TARGET} "../../../readme.md" "../../../src/pytonium_python_framework/README.md")
COPY_SINGLE_FILE(${CEF_TARGET} "../../../src/pytonium_library_test/index.html" "../../../src/pytonium_python_framework/PytoniumTest/index.html")
COPY_SINGLE_FILE(${CEF_TARGET} "../../../src/pytonium_library_test/radioactive.ico" "../../../src/pytonium_python_framework/PytoniumTest/radioactive.ico")
COPY_SINGLE_FILE(${CEF_TARGET} "../../../src/pytonium_library_test/index.html"  "${CEF_TARGET_OUT_DIR}/index.html")
COPY_SINGLE_FILE(${CEF_TARGET} "../../../src/pytonium_library_test/radioactive.ico"  "${CEF_TARGET_OUT_DIR}/radioactive.ico")
endif()

if(OS_LINUX)
    # Executable target.
    add_executable(${CEF_TARGET} main.cpp)
    SET_EXECUTABLE_TARGET_PROPERTIES(${CEF_TARGET})
    add_dependencies(${CEF_TARGET} libcef_dll_wrapper)
    target_link_libraries(${CEF_TARGET} libcef_lib libcef_dll_wrapper ${CEF_STANDARD_LIBS})

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

    # Set SUID permissions on the chrome-sandbox target.
    SET_LINUX_SUID_PERMISSIONS("${CEF_TARGET}" "${CEF_TARGET_OUT_DIR}/chrome-sandbox")

    COPY_SINGLE_FILE(pytonium_library_test "../../../readme.md" "../../../src/pytonium_python_framework/README.md")
    COPY_SINGLE_FILE(pytonium_library_test "../../../src/pytonium_library_test/index.html" "../../../src/pytonium_python_framework/PytoniumTest/index.html")
    COPY_SINGLE_FILE(pytonium_library_test "../../../src/pytonium_library_test/radioactive.ico" "../../../src/pytonium_python_framework/PytoniumTest/radioactive.ico")
    COPY_SINGLE_FILE(pytonium_library_test "../../../src/pytonium_library_test/index.html"  "${CEF_TARGET_OUT_DIR}/index.html")
    COPY_SINGLE_FILE(pytonium_library_test "../../../src/pytonium_library_test/radioactive.ico"  "${CEF_TARGET_OUT_DIR}/radioactive.ico")
endif()