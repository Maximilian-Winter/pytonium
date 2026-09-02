# /pyaacrl/cython_src/CMakeLists.txt
find_package(PythonExtensions REQUIRED)
find_package(Cython REQUIRED)

add_cython_target(pytonium CXX PY3)  # cythonize as C++ for Python3
set(CEF_TARGET "pytonium")
ADD_LOGICAL_TARGET("libcef_lib" "${CEF_LIB_DEBUG}" "${CEF_LIB_RELEASE}")
add_library(${CEF_TARGET}  MODULE ${pytonium})  # add module as a target
if(UNIX AND NOT APPLE)
    target_sources(${CEF_TARGET} PRIVATE pytonium_library/osr_window_x11.cc)
    target_compile_definitions(${CEF_TARGET} PRIVATE OS_LINUX)
endif()
target_include_directories(${CEF_TARGET} PUBLIC ${CEF_INCLUDE_PATH})
add_dependencies(${CEF_TARGET} libcef_lib libcef_dll_wrapper pytonium_library)
if(UNIX AND NOT APPLE)
    target_link_libraries(${CEF_TARGET} libcef_lib libcef_dll_wrapper pytonium_library ${CEF_STANDARD_LIBS} X11 Xext)
else()
    target_link_libraries(${CEF_TARGET} libcef_lib libcef_dll_wrapper pytonium_library ${CEF_STANDARD_LIBS})
endif()
python_extension_module(pytonium)  # add Python-specific arguments to target
install(TARGETS pytonium LIBRARY DESTINATION Pytonium)
