# distutils: language=c++
# cython: language_level=3
import builtins

from Pytonium.src.header.cefsimplewrapper cimport CefWrapper, CefValueWrapper

#from .header.cefsimplewrapper cimport CefWrapper, CefValueWrapper


cdef class PytoniumMethodWrapper:
    cdef python_method
    def __init__(self, method):
        self.python_method = method

    def __call__(self, args):
        self.python_method(args)

cdef class PytoniumValueWrapper:
    cdef CefValueWrapper cef_value_wrapper;

    def __init__(self):
        self.cef_value_wrapper = CefValueWrapper()

    def is_int(self):
        return self.cef_value_wrapper.IsInt()

    def is_bool(self):
        return self.cef_value_wrapper.IsBool()

    def is_double(self):
        return self.cef_value_wrapper.IsDouble()

    def is_string(self):
        return self.cef_value_wrapper.IsString()

    def get_int(self):
        return self.cef_value_wrapper.GetInt()

    def get_bool(self):
        return self.cef_value_wrapper.GetBool()

    def get_double(self):
        return self.cef_value_wrapper.GetDouble()

    def get_string(self):
        return self.cef_value_wrapper.GetString()


cdef inline void java_binding_callback(void *python_function_object, int size, CefValueWrapper* args):
    cdef CefValueWrapper* fargs = args
    arg_list = []
    cdef PytoniumValueWrapper v2
    for i in range(size):
        v2 = PytoniumValueWrapper()
        v2.cef_value_wrapper = fargs[0]
        if v2.is_int():
            arg_list.append(v2.get_int())
        if v2.is_bool():
            arg_list.append(v2.get_bool())
        if v2.is_string():
            arg_list.append(bytes.decode(v2.get_string(), "utf-8"))
        if v2.is_double():
            arg_list.append(v2.get_double())
        fargs += 1

    (<object>python_function_object)(arg_list)

cdef inline void java_binding_object_callback(void *python_function_object, int size, CefValueWrapper* args):
    cdef CefValueWrapper* fargs = args
    arg_list = []
    cdef PytoniumValueWrapper v2
    for i in range(size):
        v2 = PytoniumValueWrapper()
        v2.cef_value_wrapper = fargs[0]
        if v2.is_int():
            arg_list.append(v2.get_int())
        if v2.is_bool():
            arg_list.append(v2.get_bool())
        if v2.is_string():
            arg_list.append(bytes.decode(v2.get_string(), "utf-8"))
        if v2.is_double():
            arg_list.append(v2.get_double())
        fargs += 1

    (<PytoniumMethodWrapper>python_function_object)(arg_list)

cdef class Pytonium:
    cdef CefWrapper cef_wrapper;

    def __init__(self):
        self.cef_wrapper = CefWrapper()

    def init_cef(self, start_url: str, init_width: int, init_height: int):
        self.cef_wrapper.InitCefSimple(start_url.encode("utf-8"), init_width, init_height)

    def execute_javascript(self, code: str):
        self.cef_wrapper.ExecuteJavascript(code.encode("utf-8"))

    def add_javascript_python_binding(self, name: str, func, javascript_object: str = ""):
       self.cef_wrapper.AddJavascriptPythonBinding(name.encode("utf-8"), java_binding_callback, <void *>func, javascript_object.encode("utf-8"))

    def shutdown_cef(self):
        self.cef_wrapper.ShutdownCefSimple()

    def is_running(self):
        return self.cef_wrapper.IsRunning()

    def add_javascript_python_binding_object(self, obj: object, javascript_object: str = ""):
        methods = [a for a in dir(obj) if not a.startswith('__') and callable(getattr(obj, a))]
        for method in methods:
            meth = getattr(obj, method)
            py_meth_wrapper = PytoniumMethodWrapper(meth)
            size_methods = 0
            if hasattr(obj, "python_api_methods"):
                obj.python_api_methods.append(py_meth_wrapper)
                size_methods = len(obj.python_api_methods)
            else:
                obj.python_api_methods = []
                obj.python_api_methods.append(py_meth_wrapper)
                size_methods = 1
            self.cef_wrapper.AddJavascriptPythonBinding(method.encode("utf-8"), java_binding_object_callback, <void *> obj.python_api_methods[size_methods-1], javascript_object.encode("utf-8"))


    def do_cef_message_loop_work(self):
        return self.cef_wrapper.DoCefMessageLoopWork()

    def set_cefsub_path(self, path: str):
        self.cef_wrapper.SetCustomCefSubprocessPath(path.encode("utf-8"))

    def set_cef_cache_path(self, path: str):
        self.cef_wrapper.SetCustomCefCachePath(path.encode("utf-8"))

    def load_url(self, url: str):
        self.cef_wrapper.LoadUrl(url.encode("utf-8"))

