#ifndef LIBRARY_LIBRARY_H
#define LIBRARY_LIBRARY_H


#include "cef_wrapper_app.h"
#include "cef_wrapper_client_handler.h"
#include "include/cef_command_line.h"

#if defined(OS_WIN)
#include <Windows.h>
#include "include/cef_sandbox_win.h"
#endif


#include "javascript_binding.h"
#include "cef_value_wrapper.h"

class PytoniumLibrary
{
public:
    PytoniumLibrary();

    void InitPytonium(std::string start_url, int init_width, int init_height);

    void ExecuteJavascript(const std::string &code);

    void ShutdownPytonium();

    void ReturnValueToJavascript(int message_id, CefValueWrapper returnValue);

    bool IsRunning();

    bool IsReadyToExecuteJavascript();

    void UpdateMessageLoop();

    void AddJavascriptBinding(std::string name,
                              js_binding_function_ptr jsNativeApiFunctionPtr, std::string javascript_object);

    void AddJavascriptPythonBinding(const std::string &name,
                                    js_python_bindings_handler_function_ptr python_bindings_handler,
                                    js_python_callback_object_ptr python_callback_object,
                                    const std::string &javascript_object, bool returns_value);

    void AddStateHandlerPythonBinding(state_handler_function_ptr stateHandlerFunctionPtr, state_callback_object_ptr stateCallbackObjectPtr, const std::vector<std::string>& namespacesToSubscribeTo);


    void SetState(const std::string& stateNamespace, const std::string& key, CefValueWrapper value);

    void RemoveState(const std::string& stateNamespace, const std::string& key);

    void SetCustomSubprocessPath(std::string cefsub_path);

    void SetCustomCachePath(std::string cef_cache_path);

    void SetCustomResourcePath(std::string cef_resources_path);

    void SetCustomLocalesPath(std::string cef_locales_path);

    void SetCustomIconPath(std::string icon_path);

    void LoadUrl(std::string url);

    void AddContextMenuEntry(context_menu_handler_function_ptr context_menuHandlerFunctionPtr, context_menu_handler_object_ptr context_menuCallbackObjectPtr, const std::string& contextMenuNameSpace, const std::string& contextMenuDisplayName, int contextMenuId);

    void SetCurrentContextMenuNamespace(const std::string& contextMenuNamespace);

    void SetShowDebugContextMenu(bool show);

    void AddCustomScheme(std::string schemeIdentifier, std::string contentRootFolder);

    void AddMimeTypeMapping(const std::string& fileExtension, std::string mimeType);

    void SetFramelessWindow(bool frameless);

private:

    CefRefPtr<CefWrapperApp> m_App;

    bool m_UseCustomCefSubPath = false;
    std::string m_CustomCefSubPath;

    bool m_UseCustomCefCachePath = false;
    std::string m_CustomCefCachePath;

    bool m_UseCustomCefResourcesPath = false;
    std::string m_CustomCefResourcesPath;

    bool m_UseCustomCefLocalesPath = false;
    std::string m_CustomCefLocalesPath;

    bool m_UseCustomIcon = false;
    std::string m_CustomIconPath;

    bool m_FramelessWindow = false;

    std::vector<JavascriptBinding> m_Javascript_Bindings;
    std::vector<JavascriptPythonBinding> m_Javascript_Python_Bindings;
    std::vector<StateHandlerPythonBinding> m_StateHandlerPythonBindings;
    std::vector<ContextMenuBinding> m_ContextMenuBindings;
    std::vector<CefCustomScheme> m_CustomSchemes;
    std::unordered_map<std::string, std::string> m_MimeTypeMap;
};

#endif//LIBRARY_LIBRARY_H
