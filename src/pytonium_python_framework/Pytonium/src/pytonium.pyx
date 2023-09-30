# distutils: language=c++
# cython: language_level=3



import inspect

from .pytonium_library cimport PytoniumLibrary, CefValueWrapper, state_callback_object_ptr
from libcpp.string cimport string

from libcpp cimport bool as boolie
from libcpp.map cimport map  # Import map from the C++ standard library
from libcpp.vector cimport vector  # Import vector from the C++ standard library
from libcpp.pair cimport pair
from libcpp.unordered_map cimport unordered_map
#from .header.pytonium_library cimport PytoniumLibrary, CefValueWrapper


cdef class PytoniumFunctionBindingWrapper:
    cdef object python_method
    cdef boolie returns_value
    cdef string return_value_type
    cdef object pytonium_instance
    cdef int arg_count
    cdef list arg_names
    cdef string javascript_object_name
    cdef string function_name_in_javascript

    def __init__(self, method, pytonium_instance, javascript_object_name, function_name_in_javascript, returns_value=False, return_value_type="void"):
        self.python_method = method
        self.returns_value = returns_value
        self.pytonium_instance = pytonium_instance
        self.return_value_type = return_value_type.encode("utf-8")
        sig = inspect.signature(method)
        params = sig.parameters
        self.javascript_object_name = javascript_object_name.encode("utf-8")
        self.arg_count = len(params)
        self.arg_names = list(params.keys())
        self.function_name_in_javascript = function_name_in_javascript.encode("utf-8")

    def __call__(self, *args):
        if self.returns_value:
            return self.python_method(*args)
        else:
            self.python_method(*args)

    @property
    def get_python_method(self):
        return self.python_method



    @property
    def get_returns_value(self):
        return self.returns_value

    @property
    def get_pytonium_instance(self):
        return self.pytonium_instance

    @property
    def get_arg_count(self):
        return self.arg_count

    @property
    def get_arg_names(self):
        return self.arg_names

    @property
    def get_javascript_object_name(self):
        return self.javascript_object_name.decode("utf-8")

    @property
    def get_return_value_type(self):
        return self.return_value_type.decode("utf-8")

    @property
    def get_function_name_in_javascript(self):
        return self.function_name_in_javascript.decode("utf-8")

cdef class PytoniumStateHandlerWrapper:
    cdef object python_method

    def __init__(self, method):
        self.python_method = method

    def __call__(self, namespace, key, arg):
        self.python_method(namespace, key, arg)

    @property
    def get_python_method(self):
        return self.python_method

cdef class PytoniumContextMenuBindingWrapper:
    cdef object python_method

    def __init__(self, method):
        self.python_method = method

    def __call__(self):
        self.python_method()

cdef class PytoniumContextMenuWrapper:
    cdef dict context_menu

    def __init__(self):
        self.context_menu = {}

    def add_menu_entry(self, entryNamespace: str, entry: PytoniumContextMenuBindingWrapper):
        if entryNamespace not in self.context_menu:
            self.context_menu[entryNamespace] = []
        self.context_menu[entryNamespace].append(entry)

    def get_menu_size(self, entryNamespace: str):
        return len(self.context_menu.get(entryNamespace, []))

    def __call__(self, entryNamespace: string, command_id: int):
        key = entryNamespace.decode("utf-8")
        if key in self.context_menu and command_id < len(self.context_menu[key]):
            self.context_menu[key][command_id]()

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

cpdef vector[string] convert_list_of_strings_to_vector(list py_list):
    cdef vector[string] cpp_vector
    for item in py_list:
        cpp_vector.push_back(item.encode("utf-8"))
    return cpp_vector

cdef inline void javascript_binding_object_callback(void *python_function_object, int size, CefValueWrapper* args, int message_id) noexcept:
    arg_list = get_javascript_binding_arg_list(args, size, message_id)

    if (<PytoniumFunctionBindingWrapper> python_function_object).returns_value:
        convert = PytoniumValueWrapper()
        return_value = (<PytoniumFunctionBindingWrapper> python_function_object)(*arg_list)
        (<Pytonium> (<PytoniumFunctionBindingWrapper> python_function_object).pytonium_instance).pytonium_library.ReturnValueToJavascript(message_id, convert.PythonType_to_CefValueWrapper(return_value))
    else:
        (<PytoniumFunctionBindingWrapper> python_function_object)(*arg_list)

cdef inline void context_menu_binding_object_callback(void *python_function_object, string entryNamespace, int command_id) noexcept:
    (<PytoniumContextMenuWrapper> python_function_object)(entryNamespace, command_id)

cdef inline void state_handler_callback(state_callback_object_ptr python_callback_object, string stateNamespace, string stateKey, CefValueWrapper callback_args) noexcept:
    converter = PytoniumValueWrapper()
    arg = converter.CefValueWrapper_to_PythonType(callback_args)
    (<PytoniumStateHandlerWrapper> python_callback_object)(bytes.decode(stateNamespace, "utf-8"), bytes.decode(stateKey, "utf-8"), arg)

cdef str _global_pytonium_subprocess_path = ""

def python_type_to_ts_type(python_type):
    mapping = {
        int: 'number',
        float: 'number',
        str: 'string',
        bool: 'boolean',
        object: 'object',
        None: 'void'
    }
    return mapping.get(python_type, 'any')

cdef class Pytonium:
    cdef PytoniumLibrary pytonium_library;
    cdef list _pytonium_api
    cdef list _pytonium_state_handler
    cdef PytoniumContextMenuWrapper _pytonium_context_menu

    def __init__(self):
        global _global_pytonium_subprocess_path
        self._pytonium_api = []
        self._pytonium_state_handler = []
        self._pytonium_context_menu = PytoniumContextMenuWrapper()
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

    def bind_function_to_javascript(self, function_to_bind: callable, name="", javascript_object="") :
        cdef should_return = hasattr(function_to_bind, 'returns_value_to_javascript') and function_to_bind.returns_value_to_javascript
        return_value_type = "void"
        if should_return:
            return_value_type = getattr(function_to_bind, 'return_type')

        if name == "":
            name = function_to_bind.__name__
        py_meth_wrapper = PytoniumFunctionBindingWrapper(function_to_bind, self, javascript_object, name, should_return, return_value_type)
        self._pytonium_api.append(py_meth_wrapper)
        self.pytonium_library.AddJavascriptPythonBinding(name.encode("utf-8"), javascript_binding_object_callback, <void *>self._pytonium_api[len(self._pytonium_api)-1], javascript_object.encode("utf-8"), should_return)

    def bind_functions_to_javascript(self, functions_to_bind: list[callable], names=[], javascript_object=""):
        name_index = 0
        for meth in functions_to_bind:
            should_return = hasattr(meth, 'returns_value_to_javascript') and meth.returns_value_to_javascript
            return_value_type = "void"
            if should_return:
                return_value_type = getattr(meth, 'return_type')
            if len(names) > name_index:
                py_meth_wrapper = PytoniumFunctionBindingWrapper(meth, self, javascript_object, names[name_index], should_return, return_value_type)
                self._pytonium_api.append(py_meth_wrapper)
                size_methods = len(self._pytonium_api)
                self.pytonium_library.AddJavascriptPythonBinding(names[name_index].encode("utf-8"), javascript_binding_object_callback, <void *> self._pytonium_api[size_methods - 1], javascript_object.encode("utf-8"), should_return)
            else:
                py_meth_wrapper = PytoniumFunctionBindingWrapper(meth, self, javascript_object, meth.__name__, should_return, return_value_type)
                self._pytonium_api.append(py_meth_wrapper)
                size_methods = len(self._pytonium_api)
                self.pytonium_library.AddJavascriptPythonBinding(meth.__name__.encode("utf-8"), javascript_binding_object_callback, <void *> self._pytonium_api[size_methods - 1], javascript_object.encode("utf-8"), should_return)
            name_index += 1


    def bind_object_methods_to_javascript(self, obj: object, names=[], javascript_object=""):
        methods = [a for a in dir(obj) if not a.startswith('__') and callable(getattr(obj, a))]
        name_index = 0
        for method in methods:
            meth = getattr(obj, method)
            should_return = hasattr(meth, 'returns_value_to_javascript') and meth.returns_value_to_javascript
            return_value_type = "void"
            if should_return:
                return_value_type = getattr(meth, 'return_type')
            if len(names) > name_index:
                py_meth_wrapper = PytoniumFunctionBindingWrapper(meth, self, javascript_object, names[name_index], should_return, return_value_type)
                self._pytonium_api.append(py_meth_wrapper)
                size_methods = len(self._pytonium_api)
                self.pytonium_library.AddJavascriptPythonBinding(names[name_index].encode("utf-8"), javascript_binding_object_callback, <void *> self._pytonium_api[size_methods - 1], javascript_object.encode("utf-8"), should_return)
            else:
                py_meth_wrapper = PytoniumFunctionBindingWrapper(meth, self, javascript_object, method, should_return, return_value_type)
                self._pytonium_api.append(py_meth_wrapper)
                size_methods = len(self._pytonium_api)
                self.pytonium_library.AddJavascriptPythonBinding(method.encode("utf-8"), javascript_binding_object_callback, <void *> self._pytonium_api[size_methods - 1], javascript_object.encode("utf-8"), should_return)
            name_index += 1

    def add_context_menu_entry(self, context_menu_entry_function, display_name="", context_menu_namespace=""):
        if display_name == "":
            display_name = context_menu_entry_function.__name__
        if context_menu_namespace == "":
            context_menu_namespace = "app"
        context_menu_entry = PytoniumContextMenuBindingWrapper(context_menu_entry_function)
        entry_index = self._pytonium_context_menu.get_menu_size(context_menu_namespace)
        self._pytonium_context_menu.add_menu_entry(context_menu_namespace, context_menu_entry)
        self.pytonium_library.AddContextMenuEntry(context_menu_binding_object_callback, <void *>self._pytonium_context_menu, context_menu_namespace.encode("utf-8"), display_name.encode("utf-8"), entry_index)

    def add_context_menu_entries(self, context_menu_entry_functions: list[callable], display_names=[], context_menu_namespace=""):
        if context_menu_namespace == "":
            context_menu_namespace = "app"
        name_index = 0
        for meth in context_menu_entry_functions:
            if len(display_names) > name_index:
                context_menu_entry = PytoniumContextMenuBindingWrapper(meth)
                entry_index = self._pytonium_context_menu.get_menu_size(context_menu_namespace)
                self._pytonium_context_menu.add_menu_entry(context_menu_namespace, context_menu_entry)
                self.pytonium_library.AddContextMenuEntry(context_menu_binding_object_callback, <void *>self._pytonium_context_menu, context_menu_namespace.encode("utf-8"), display_names[name_index].encode("utf-8"), entry_index)
            else:
                name = meth.__name__
                context_menu_entry = PytoniumContextMenuBindingWrapper(meth)
                entry_index = self._pytonium_context_menu.get_menu_size(context_menu_namespace)
                self._pytonium_context_menu.add_menu_entry(context_menu_namespace, context_menu_entry)
                self.pytonium_library.AddContextMenuEntry(context_menu_binding_object_callback, <void *>self._pytonium_context_menu, context_menu_namespace.encode("utf-8"), name.encode("utf-8"), entry_index)
            name_index += 1


    def add_context_menu_entries_from_object(self, context_menu_entries_object: object, display_names=[], context_menu_namespace=""):
        if context_menu_namespace == "":
            context_menu_namespace = "app"
        methods = [a for a in dir(context_menu_entries_object) if not a.startswith('__') and callable(getattr(context_menu_entries_object, a))]
        name_index = 0
        for method in methods:
            meth = getattr(context_menu_entries_object, method)
            if len(display_names) > name_index:
                context_menu_entry = PytoniumContextMenuBindingWrapper(meth)
                entry_index = self._pytonium_context_menu.get_menu_size(context_menu_namespace)
                self._pytonium_context_menu.add_menu_entry(context_menu_namespace, context_menu_entry)
                self.pytonium_library.AddContextMenuEntry(context_menu_binding_object_callback, <void *>self._pytonium_context_menu, context_menu_namespace.encode("utf-8"), display_names[name_index].encode("utf-8"), entry_index)
            else:
                name = meth.__name__
                context_menu_entry = PytoniumContextMenuBindingWrapper(meth)
                entry_index = self._pytonium_context_menu.get_menu_size(context_menu_namespace)
                self._pytonium_context_menu.add_menu_entry(context_menu_namespace, context_menu_entry)
                self.pytonium_library.AddContextMenuEntry(context_menu_binding_object_callback, <void *>self._pytonium_context_menu, context_menu_namespace.encode("utf-8"), name.encode("utf-8"), entry_index)
            name_index += 1

    def add_state_handler(self, state_handler: object, namespaces: list[str]) :
        cdef has_update = hasattr(state_handler, 'update_state')
        if has_update:
            state_handler_meth = getattr(state_handler, 'update_state')
            py_meth_wrapper = PytoniumStateHandlerWrapper(state_handler_meth)
            namespaces_converted = convert_list_of_strings_to_vector(namespaces)
            self._pytonium_state_handler.append(py_meth_wrapper)
            self.pytonium_library.AddStateHandlerPythonBinding(state_handler_callback, <void *>self._pytonium_state_handler[len(self._pytonium_state_handler)-1], namespaces_converted)

    def set_context_menu_namespace(self, context_menu_namespace: str):
        self.pytonium_library.SetCurrentContextMenuNamespace(context_menu_namespace.encode("utf-8"))

    def set_show_debug_context_menu(self, show: bool):
        self.pytonium_library.SetShowDebugContextMenu(show)

    def shutdown(self):
        self.pytonium_library.ShutdownPytonium()

    def is_running(self):
        return self.pytonium_library.IsRunning()

    def update_message_loop(self):
        return self.pytonium_library.UpdateMessageLoop()


    def set_cache_path(self, path: str):
        self.pytonium_library.SetCustomCachePath(path.encode("utf-8"))

    def set_custom_icon_path(self, path: str):
        self.pytonium_library.SetCustomIconPath(path.encode("utf-8"))

    def load_url(self, url: str):
        self.pytonium_library.LoadUrl(url.encode("utf-8"))

    def set_state(self, namespace: str, key: str, value: object):
        converter = PytoniumValueWrapper()
        self.pytonium_library.SetState(namespace.encode("utf-8"), key.encode("utf-8"), converter.PythonType_to_CefValueWrapper(value))

    def generate_typescript_definitions(self, filename: str):
       ts_definitions = []
       ts_definitions.append("declare namespace Pytonium {")

       object_map = {}  # To group functions under the same javascript_object_name

       for py_meth_wrapper in self._pytonium_api:
           func_name = py_meth_wrapper.get_function_name_in_javascript
           sig = inspect.signature(py_meth_wrapper.get_python_method)
           arg_names = ', '.join([f"{name}: {python_type_to_ts_type(param.annotation)}"
                                   for name, param in sig.parameters.items()])
           javascript_object_name = py_meth_wrapper.get_javascript_object_name

           if py_meth_wrapper.get_returns_value:
               return_type = py_meth_wrapper.get_return_value_type
           else:
               return_type = 'void'

           # Organize by javascript_object_name
           if javascript_object_name not in object_map:
               object_map[javascript_object_name] = []

           object_map[javascript_object_name].append(
               f"function {func_name}({arg_names}): {return_type};"
           )

       object_map["appState"] = []

       object_map["appState"].append(
                             f"function registerForStateUpdates(eventName: string, namespaces: string[]): void;"
                         )
       object_map["appState"].append(
                      f"function setState(namespace: string, key: string, value: any): void;"
                  )
       object_map["appState"].append(
                     f"function getState(namespace: string, key: string): any;"
                 )
       object_map["appState"].append(
                    f"function removeState(namespace: string, key: string): void;"
                )


       # Generate the TypeScript definitions
       for obj_name, functions in object_map.items():
           if obj_name:  # Skip if empty, means these functions are directly under Pytonium
               ts_definitions.append(f"  export namespace {obj_name} {{")

           for func in functions:
               ts_definitions.append(f"    {func}")

           if obj_name:
               ts_definitions.append("  }")
       ts_definitions.append("}")

       ts_definitions.append("interface Window {")
       ts_definitions.append("  PytoniumReady: boolean;")
       ts_definitions.append("}")

       ts_definitions.append("interface WindowEventMap {")
       ts_definitions.append("  PytoniumReady: Event;")
       ts_definitions.append("}")

       # Writing to a .d.ts file for IDE to pick up
       with open(filename, "w") as f:
           f.write('\n'.join(ts_definitions))

       print("TypeScript definitions generated.")
