# /pyaacrl/cython_src/CMakeLists.txt
find_package(PythonExtensions REQUIRED)
find_package(Cython REQUIRED)

add_cython_target(pytonium CXX PY3)  # cythonize as C++ for Python3
add_library(pytonium MODULE ${pytonium})  # add module as a target
target_link_libraries(pytonium pytonium_library)  # link to original library

python_extension_module(pytonium)  # add Python-specific arguments to target
install(TARGETS pytonium LIBRARY DESTINATION Pytonium)