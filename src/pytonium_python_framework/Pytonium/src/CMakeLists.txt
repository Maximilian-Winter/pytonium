# /pyaacrl/cython_src/CMakeLists.txt
find_package(PythonExtensions REQUIRED)
find_package(Cython REQUIRED)

add_cython_target(pytonium CXX PY3)  # cythonize as C++ for Python3
set(CEF_TARGET "pytonium")
ADD_LOGICAL_TARGET("libcef_lib" "${CEF_LIB_DEBUG}" "${CEF_LIB_RELEASE}")
add_library(${CEF_TARGET}  MODULE ${pytonium})  # add module as a target
add_dependencies(${CEF_TARGET} libcef_lib libcef_dll_wrapper pytonium_library)
target_link_libraries(${CEF_TARGET} libcef_lib libcef_dll_wrapper pytonium_library ${CEF_STANDARD_LIBS})
python_extension_module(pytonium)  # add Python-specific arguments to target
install(TARGETS pytonium LIBRARY DESTINATION Pytonium)