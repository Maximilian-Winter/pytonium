# Determine the target output directory.
SET_CEF_TARGET_OUT_DIR()
add_executable(pytonium_library_test main.cpp)
SET_EXECUTABLE_TARGET_PROPERTIES(pytonium_library_test)
add_dependencies(pytonium_library_test pytonium_library)
target_link_libraries(pytonium_library_test PUBLIC pytonium_library)

add_compile_definitions(symbol_level=2)
add_compile_definitions(_ITERATOR_DEBUG_LEVEL=0)
include_directories(${CEF_INCLUDE_PATH})

COPY_FILES(pytonium_library_test "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "${CEF_TARGET_OUT_DIR}")
COPY_FILES(pytonium_library_test "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "${CEF_TARGET_OUT_DIR}")
COPY_SINGLE_FILE(pytonium_library_test "../../../readme.md" "../../../src/pytonium_python_framework/README.md")
COPY_SINGLE_FILE(pytonium_library_test "../../../src/pytonium_library_test/index.html" "../../../src/pytonium_python_framework/PytoniumTests/index.html")
COPY_SINGLE_FILE(pytonium_library_test "../../../src/pytonium_library_test/radioactive.ico" "../../../src/pytonium_python_framework/PytoniumTests/radioactive.ico")
COPY_SINGLE_FILE(pytonium_library_test "../../../src/pytonium_library_test/index.html"  "${CEF_TARGET_OUT_DIR}/index.html")
COPY_SINGLE_FILE(pytonium_library_test "../../../src/pytonium_library_test/radioactive.ico"  "${CEF_TARGET_OUT_DIR}/radioactive.ico")