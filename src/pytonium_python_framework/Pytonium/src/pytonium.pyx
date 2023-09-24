# distutils: language=c++
# cython: language_level=3


import string
import inspect

from .pytonium_library cimport PytoniumLibrary, CefValueWrapper
from libcpp.string cimport string

from libcpp.map cimport map  # Import map from the C++ standard library
from libcpp.vector cimport vector  # Import vector from the C++ standard library
from libcpp.pair cimport pair
#from .header.pytonium_library cimport PytoniumLibrary, CefValueWrapper


cdef class PytoniumMethodWrapper:
    cdef python_method
    cdef returns_value
    cdef pytonium_instance
    cdef arg_count
    cdef arg_names

    def __init__(self, method, pytonium_instance, returns_value=False):
        self.python_method = method
        self.returns_value = returns_value
        self.pytonium_instance = pytonium_instance
        sig = inspect.signature(method)
        params = sig.parameters

        self.arg_count = len(params)
        self.arg_names = list(params.keys())

    def __call__(self, *args):
        if self.returns_value:
            return self.python_method(*args)
        else:
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

    def is_object(self):
        return self.cef_value_wrapper.IsObject()

    def is_list(self):
        return self.cef_value_wrapper.IsList()

    def get_int(self):
        return self.cef_value_wrapper.GetInt()

    def get_bool(self):
        return self.cef_value_wrapper.GetBool()

    def get_double(self):
        return self.cef_value_wrapper.GetDouble()

    def get_string(self):
        return self.cef_value_wrapper.GetString()

    # Getter for list type
    def get_list(self):
        cdef vector[CefValueWrapper] cef_vector = self.cef_value_wrapper.GetList()
        return [self.CefValueWrapper_to_PythonType(item) for item in cef_vector]

    def get_object(self):
        cdef map[string, CefValueWrapper] cef_map = self.cef_value_wrapper.GetObject_()
        cdef pair[string, CefValueWrapper] kv  # Declare as a pair
        cdef string key
        cdef CefValueWrapper value
        py_dict = {}
        for kv in cef_map:
            key = kv.first  # Extract key
            value = kv.second  # Extract value
            py_dict[key.decode("utf-8")] = self.CefValueWrapper_to_PythonType(value)
        return py_dict

    def set_int(self, value):
        return self.cef_value_wrapper.SetInt(value)

    def set_bool(self, value):
        return self.cef_value_wrapper.SetBool(value)

    def set_double(self, value):
        return self.cef_value_wrapper.SetDouble(value)

    def set_string(self, value):
        return self.cef_value_wrapper.SetString(value.encode("utf-8"))

    # Setter for list type
    def set_list(self, py_list):
        cdef vector[CefValueWrapper] cef_vector = vector[CefValueWrapper]()
        for item in py_list:
            cef_item = self.PythonType_to_CefValueWrapper(item)
            cef_vector.push_back(cef_item)
        self.cef_value_wrapper.SetList(cef_vector)

    # Setter for object (dictionary) type
    def set_object(self, py_dict):
        cdef map[string, CefValueWrapper] cef_map = map[string, CefValueWrapper]()
        for key, value in py_dict.items():
            cef_key = key.encode("utf-8")
            cef_value = self.PythonType_to_CefValueWrapper(value)
            cef_map[cef_key] = cef_value
        self.cef_value_wrapper.SetObject(cef_map)

    # Conversion from CefValueWrapper to Python type
    cdef object CefValueWrapper_to_PythonType(self, CefValueWrapper cef_value):
        cdef vector[CefValueWrapper] cef_list
        cdef map[string, CefValueWrapper] cef_map
        cdef string key
        cdef CefValueWrapper value
        cdef pair[string, CefValueWrapper] kv  # Declare as a pair
        if cef_value.IsInt():
            return cef_value.GetInt()
        elif cef_value.IsBool():
            return cef_value.GetBool() == True
        elif cef_value.IsDouble():
            return cef_value.GetDouble()
        elif cef_value.IsString():
            return cef_value.GetString().decode("utf-8")
        elif cef_value.IsList():
            cef_list = cef_value.GetList()
            return [self.CefValueWrapper_to_PythonType(item) for item in cef_list]
        elif cef_value.IsObject():
            cef_map = cef_value.GetObject_()
            py_dict = {}
            for kv in cef_map:
                key = kv.first  # Extract key
                value = kv.second  # Extract value
                py_dict[key.decode("utf-8")] = self.CefValueWrapper_to_PythonType(value)
            return py_dict
        else:
            return None

    # Conversion from Python type to CefValueWrapper
    cdef CefValueWrapper PythonType_to_CefValueWrapper(self, object py_value):
        cdef CefValueWrapper cef_value = CefValueWrapper()
        cdef vector[CefValueWrapper] cef_vector = vector[CefValueWrapper]()
        cdef map[string, CefValueWrapper] cef_map = map[string, CefValueWrapper]()
        if isinstance(py_value, int):
            cef_value.SetInt(py_value)
        elif isinstance(py_value, bool):
            cef_value.SetBool(py_value)
        elif isinstance(py_value, float):
            cef_value.SetDouble(py_value)
        elif isinstance(py_value, str):
            cef_value.SetString(py_value.encode("utf-8"))
        elif isinstance(py_value, list):
            for item in py_value:
                cef_item = self.PythonType_to_CefValueWrapper(item)
                cef_vector.push_back(cef_item)
            cef_value.SetList(cef_vector)
        elif isinstance(py_value, dict):
            for key, value in py_value.items():
                cef_map[key.encode("utf-8")] = self.PythonType_to_CefValueWrapper(value)
            cef_value.SetObject(cef_map)
        return cef_value

cdef inline list get_javascript_binding_arg_list(CefValueWrapper* args, int size, int message_id):
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
        if v2.is_object():
            arg_list.append(v2.get_object())
        if v2.is_list():
            arg_list.append(v2.get_list())
        fargs += 1

    return arg_list


cdef inline void javascript_binding_object_callback(void *python_function_object, int size, CefValueWrapper* args, int message_id) noexcept:
    arg_list = get_javascript_binding_arg_list(args, size, message_id)

    if (<PytoniumMethodWrapper> python_function_object).returns_value:
        convert = PytoniumValueWrapper()
        return_value = (<PytoniumMethodWrapper> python_function_object)(*arg_list)
        (<Pytonium> (<PytoniumMethodWrapper> python_function_object).pytonium_instance).pytonium_library.ReturnValueToJavascript(message_id, convert.PythonType_to_CefValueWrapper(return_value))
    else:
        (<PytoniumMethodWrapper> python_function_object)(*arg_list)

cdef str _global_pytonium_subprocess_path = ""

cdef class Pytonium:
    cdef PytoniumLibrary pytonium_library;
    cdef list _pytonium_api
    def __init__(self):
        global _global_pytonium_subprocess_path
        self._pytonium_api = []
        self.pytonium_library = PytoniumLibrary()
        self.pytonium_library.SetCustomSubprocessPath(_global_pytonium_subprocess_path.encode('utf-8'))

    @classmethod
    def pytonium_subprocess_path(cls):
        global _global_pytonium_subprocess_path
        return _global_pytonium_subprocess_path

    @classmethod
    def set_subprocess_path(cls, value):
        global _global_pytonium_subprocess_path
        _global_pytonium_subprocess_path = value


    def initialize(self, start_url: str, init_width: int, init_height: int):
        self.pytonium_library.InitPytonium(start_url.encode("utf-8"), init_width, init_height)

    def return_value_to_javascript(self, message_id: int, value):
        cdef PytoniumValueWrapper pyth_value = PytoniumValueWrapper()
        self.pytonium_library.ReturnValueToJavascript(message_id, pyth_value.PythonType_to_CefValueWrapper(value))

    def execute_javascript(self, code: str):
        self.pytonium_library.ExecuteJavascript(code.encode("utf-8"))

    def bind_function_to_javascript(self, name: str, func, javascript_object: str = "") :
        cdef should_return = hasattr(func, 'returns_value_to_javascript') and func.returns_value_to_javascript
        py_meth_wrapper = PytoniumMethodWrapper(func, self, should_return)
        self._pytonium_api.append(py_meth_wrapper)
        self.pytonium_library.AddJavascriptPythonBinding(name.encode("utf-8"), javascript_binding_object_callback, <void *>self._pytonium_api[len(self._pytonium_api)-1], javascript_object.encode("utf-8"), should_return)

    def shutdown(self):
        self.pytonium_library.ShutdownPytonium()

    def is_running(self):
        return self.pytonium_library.IsRunning()

    def bind_object_methods_to_javascript(self, obj: object, javascript_object: str = ""):
        methods = [a for a in dir(obj) if not a.startswith('__') and callable(getattr(obj, a))]
        for method in methods:
            meth = getattr(obj, method)
            should_return = hasattr(meth, 'returns_value_to_javascript') and meth.returns_value_to_javascript
            py_meth_wrapper = PytoniumMethodWrapper(meth, self, should_return)
            self._pytonium_api.append(py_meth_wrapper)
            size_methods = len(self._pytonium_api)
            self.pytonium_library.AddJavascriptPythonBinding(method.encode("utf-8"), javascript_binding_object_callback, <void *> self._pytonium_api[size_methods - 1], javascript_object.encode("utf-8"), should_return)


    def update_message_loop(self):
        return self.pytonium_library.UpdateMessageLoop()


    def set_cache_path(self, path: str):
        self.pytonium_library.SetCustomCachePath(path.encode("utf-8"))

    def set_custom_icon_path(self, path: str):
        self.pytonium_library.SetCustomIconPath(path.encode("utf-8"))

    def load_url(self, url: str):
        self.pytonium_library.LoadUrl(url.encode("utf-8"))

