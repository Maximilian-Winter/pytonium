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

    // Backward-compatible: init CEF + create first browser in one call
    void InitPytonium(std::string start_url, int init_width, int init_height);

    // Multi-instance API: separate CEF init from browser creation
    int CreateBrowser(const std::string& url, int width, int height, bool frameless,
                      const std::string& iconPath);
    void CloseBrowser();
    bool IsBrowserRunning() const;
    int GetBrowserId() const { return m_BrowserId; }

    static bool IsCefInitialized() { return s_CefInitialized; }
    static void ShutdownCef();

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

    // Window control methods for frameless windows
    void MinimizeWindow();
    void MaximizeWindow();
    void RestoreWindow();
    void CloseWindow();
    bool IsMaximized();

    // Drag window by delta (for draggable custom title bar)
    void DragWindow(int deltaX, int deltaY);

    // Get window position
    void GetWindowPosition(int& x, int& y);

    // Move window to absolute position (smoother than delta)
    void SetWindowPosition(int x, int y);

    // Get window size
    void GetWindowSize(int& width, int& height);

    // Resize window
    void SetWindowSize(int width, int height);

    // Resize window from a specific edge/corner (anchor: 0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right)
    void ResizeWindow(int newWidth, int newHeight, int anchor);

    // Get the native window handle (HWND on Windows, X11 window on Linux)
    void* GetNativeWindowHandle();

    // Window event callback setters
    void SetOnTitleChangeCallback(void (*callback)(void*, const char*), void* user_data);
    void SetOnAddressChangeCallback(void (*callback)(void*, const char*), void* user_data);
    void SetOnFullscreenChangeCallback(void (*callback)(void*, bool), void* user_data);

private:

    // Shared across all PytoniumLibrary instances (one CEF process)
    static bool s_CefInitialized;
    static int s_InstanceCount;
    static CefRefPtr<CefWrapperApp> s_App;

    // Per-instance browser reference
    int m_BrowserId = -1;
    CefRefPtr<CefBrowser> m_Browser;

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
