# distutils: language=c++
# cython: language_level=3

from libcpp.string cimport string
from libcpp cimport bool


cdef extern from "src/pytonium_library/javascript_binding.h":
    cdef cppclass CefValueWrapper:
        CefValueWrapper() except +
        bool IsInt()
        bool IsBool()
        bool IsDouble()
        bool IsString()
        int GetInt()
        bool GetBool()
        double GetDouble()
        string GetString()


cdef extern from "src/pytonium_library/javascript_binding.h":
    ctypedef void (*js_python_callback_object_ptr);
    ctypedef void (*js_python_bindings_handler_function_ptr)(void* python_callback_object, int size, CefValueWrapper* args );

# Declare the class with cdef
cdef extern from "src/pytonium_library/pytonium_library.h":
    cdef cppclass PytoniumLibrary:
        PytoniumLibrary() except +
        void InitPytonium(string start_url, int init_width, int init_height);
        void ExecuteJavascript(string code);
        void ShutdownPytonium();
        bool IsRunning();
        void UpdateMessageLoop();
        void AddJavascriptPythonBinding(string name, js_python_bindings_handler_function_ptr handler_callback, void* python_callable, string javascript_object)
        void SetCustomSubprocessPath(string path)
        void SetCustomCachePath(string cef_cache_path)
        void SetCustomIconPath(string custom_icon_path)
        void LoadUrl(string url);
