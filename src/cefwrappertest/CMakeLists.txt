# Determine the target output directory.
SET_CEF_TARGET_OUT_DIR()
add_executable(cefwrappertest main.cpp)
SET_EXECUTABLE_TARGET_PROPERTIES(cefwrappertest)
add_dependencies(cefwrappertest cefwrapper)
target_link_libraries(cefwrappertest PUBLIC cefwrapper)

add_compile_definitions(symbol_level=2)
add_compile_definitions(_ITERATOR_DEBUG_LEVEL=0)
include_directories(${CEF_INCLUDE_PATH})

COPY_FILES(cefwrappertest "${CEF_BINARY_FILES}" "${CEF_BINARY_DIR}" "${CEF_TARGET_OUT_DIR}")
COPY_FILES(cefwrappertest "${CEF_RESOURCE_FILES}" "${CEF_RESOURCE_DIR}" "${CEF_TARGET_OUT_DIR}")
COPY_SINGLE_FILE(cefwrappertest "../../../readme.md" "../../../src/Pytonium_Dev/README.md")
COPY_SINGLE_FILE(cefwrappertest "../../../src/cefwrappertest/index.html" "../../../src/Pytonium_Dev/PytoniumTests/index.html")
COPY_SINGLE_FILE(cefwrappertest "../../../src/cefwrappertest/radioactive.ico" "../../../src/Pytonium_Dev/PytoniumTests/radioactive.ico")
COPY_SINGLE_FILE(cefwrappertest "../../../src/cefwrappertest/index.html"  "${CEF_TARGET_OUT_DIR}/index.html")
COPY_SINGLE_FILE(cefwrappertest "../../../src/cefwrappertest/radioactive.ico"  "${CEF_TARGET_OUT_DIR}/radioactive.ico")