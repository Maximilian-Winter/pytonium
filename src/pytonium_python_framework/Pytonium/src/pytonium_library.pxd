# distutils: language=c++
# cython: language_level=3

from libcpp.string cimport string
from libcpp cimport bool
from libcpp.map cimport map  # Import map from the C++ standard library
from libcpp.vector cimport vector  # Import vector from the C++ standard library

cdef extern from "src/pytonium_library/javascript_binding.h":
    cdef enum ValueType:  # Enum to represent value types
        TYPE_INT
        TYPE_BOOL
        TYPE_DOUBLE
        TYPE_STRING
        TYPE_OBJECT
        TYPE_BINARY
        TYPE_LIST
        TYPE_NULL
        TYPE_INVALID
        TYPE_UNDEFINED

    cdef cppclass CefValueWrapper:
        CefValueWrapper() except +  # Constructor
        ValueType Type  # The type of the value

        # Checkers for basic types
        bool IsInt()
        bool IsBool()
        bool IsDouble()
        bool IsString()
        bool IsObject()
        bool IsBinary()
        bool IsList()
        bool IsNull()
        bool IsInvalid()

        # Getters for basic types
        int GetInt()
        bool GetBool()
        double GetDouble()
        string GetString()

        # Setters for basic types
        void SetInt(int value)
        void SetBool(bool value)
        void SetDouble(double value)
        void SetString(string value)

        # Special types
        map[string, CefValueWrapper] GetObject_()
        vector[char] GetBinary()
        vector[CefValueWrapper] GetList()

        # Setters for special types
        void SetObject(map[string, CefValueWrapper] value)
        void SetBinary(vector[char] value)
        void SetList(vector[CefValueWrapper] value)

        # Setters for null and invalid types
        void SetNull()
        void SetInvalid()


cdef extern from "src/pytonium_library/javascript_binding.h":
    ctypedef void (*js_python_callback_object_ptr)
    ctypedef void (*js_python_bindings_handler_function_ptr)(void* python_callback_object, int size, CefValueWrapper* args, int message_id )

cdef extern from "src/pytonium_library/application_state_python.h":
    ctypedef void (*state_callback_object_ptr)
    ctypedef void (*state_handler_function_ptr)(state_callback_object_ptr python_callback_object, string stateNamespace, string stateKey, CefValueWrapper callback_args)

cdef extern from "src/pytonium_library/application_context_menu_binding.h":
    ctypedef void (*context_menu_handler_object_ptr)
    ctypedef void (*context_menu_handler_function_ptr)(context_menu_handler_object_ptr python_callback_object, string contextMenuNamespace, int contextMenuIndex)

# Declare the class with cdef
cdef extern from "src/pytonium_library/pytonium_library.h":
    cdef cppclass PytoniumLibrary:
        PytoniumLibrary() except +
        void InitPytonium(string start_url, int init_width, int init_height);
        void ExecuteJavascript(string code)
        void ReturnValueToJavascript(int message_id, CefValueWrapper returnValue)
        void ShutdownPytonium()
        bool IsRunning()
        void UpdateMessageLoop();
        void AddJavascriptPythonBinding(string name, js_python_bindings_handler_function_ptr handler_callback, void* python_callable, string javascript_object, bool returns_value)
        void AddStateHandlerPythonBinding(state_handler_function_ptr stateHandlerFunctionPtr, state_callback_object_ptr stateCallbackObjectPtr,  vector[string] namespacesToSubscribeTo)
        void SetState(string stateNamespace, string key, CefValueWrapper value)
        void RemoveState(string stateNamespace, string key)
        void AddContextMenuEntry(context_menu_handler_function_ptr context_menuHandlerFunctionPtr, context_menu_handler_object_ptr context_menuCallbackObjectPtr, string contextMenuNameSpace, string contextMenuDisplayName, int contextMenuId)
        void SetCustomSubprocessPath(string path)
        void SetCustomCachePath(string cef_cache_path)
        void SetCustomIconPath(string custom_icon_path)
        void LoadUrl(string url);
        void SetCurrentContextMenuNamespace(string contextMenuNamespace);
        void SetShowDebugContextMenu(bool show);
        void AddCustomScheme(string schemeIdentifier, string contentRootFolder);
        void AddMimeTypeMapping(string fileExtension, string mimeType);
