# distutils: language=c++
# cython: language_level=3

from .pytonium_library cimport PytoniumLibrary, CefValueWrapper

#from .header.pytonium_library cimport PytoniumLibrary, CefValueWrapper


cdef class PytoniumMethodWrapper:
    cdef python_method
    def __init__(self, method):
        self.python_method = method

    def __call__(self, *args):
        self.python_method(*args)

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


cdef inline list get_java_binding_arg_list(CefValueWrapper* args, int size):
    cdef CefValueWrapper * fargs = args
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

    return arg_list


cdef inline void java_binding_callback(void *python_function_object, int size, CefValueWrapper* args):
    arg_list = get_java_binding_arg_list(args, size)
    (<object> python_function_object)(*arg_list)



cdef inline void java_binding_object_callback(void *python_function_object, int size, CefValueWrapper* args):
    arg_list = get_java_binding_arg_list(args, size)
    (<PytoniumMethodWrapper> python_function_object)(*arg_list)




def set_subprocess_path(subprocess_path: str):
    Pytonium.pytonium_subprocess_path = subprocess_path.encode("utf-8")


cdef class Pytonium:
    cdef PytoniumLibrary pytonium_library;
    pytonium_subprocess_path : string

    def __init__(self):
        self.pytonium_library = PytoniumLibrary()
        self.pytonium_library.SetCustomSubprocessPath(Pytonium.pytonium_subprocess_path)

    def initialize(self, start_url: str, init_width: int, init_height: int):
        self.pytonium_library.InitPytonium(start_url.encode("utf-8"), init_width, init_height)

    def execute_javascript(self, code: str):
        self.pytonium_library.ExecuteJavascript(code.encode("utf-8"))

    def bind_function_to_javascript(self, name: str, func, javascript_object: str = ""):
       self.pytonium_library.AddJavascriptPythonBinding(name.encode("utf-8"), java_binding_callback, <void *>func, javascript_object.encode("utf-8"))

    def shutdown(self):
        self.pytonium_library.ShutdownPytonium()

    def is_running(self):
        return self.pytonium_library.IsRunning()

    def bind_object_methods_to_javascript(self, obj: object, javascript_object: str = ""):
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
            self.pytonium_library.AddJavascriptPythonBinding(method.encode("utf-8"), java_binding_object_callback, <void *> obj.python_api_methods[size_methods - 1], javascript_object.encode("utf-8"))


    def update_message_loop(self):
        return self.pytonium_library.UpdateMessageLoop()

    def set_subprocess_path(self, path: str):
        self.pytonium_library.SetCustomSubprocessPath(path.encode("utf-8"))

    def set_cache_path(self, path: str):
        self.pytonium_library.SetCustomCachePath(path.encode("utf-8"))

    def set_custom_icon_path(self, path: str):
        self.pytonium_library.SetCustomIconPath(path.encode("utf-8"))

    def load_url(self, url: str):
        self.pytonium_library.LoadUrl(url.encode("utf-8"))

