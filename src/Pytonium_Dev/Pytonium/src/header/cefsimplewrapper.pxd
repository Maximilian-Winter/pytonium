# distutils: language=c++
# cython: language_level=3

from libcpp.string cimport string
from libcpp cimport bool


cdef extern from "src/cefwrapper/javascript_binding.h":
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


cdef extern from "src/cefwrapper/javascript_binding.h":
    ctypedef void (*js_python_callback_object_ptr);
    ctypedef void (*js_python_bindings_handler_function_ptr)(void* python_callback_object, int size, CefValueWrapper* args );

# Declare the class with cdef
cdef extern from "src/cefwrapper/library.h":
    cdef cppclass CefWrapper:
        CefWrapper() except +
        void InitCefSimple(string start_url, int init_width, int init_height);
        void ExecuteJavascript(string code);
        void ShutdownCefSimple();
        bool IsRunning();
        void DoCefMessageLoopWork();
        void AddJavascriptPythonBinding(string name, js_python_bindings_handler_function_ptr handler_callback, void* python_callable, string javascript_object)
        void SetCustomCefSubprocessPath(string path)
        void SetCustomCefCachePath(string cef_cache_path)
        void LoadUrl(string url);
