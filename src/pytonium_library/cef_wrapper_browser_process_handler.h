#ifndef CEF_WRAPPER_BROWSER_PROCESS_HANDLER_H
#define CEF_WRAPPER_BROWSER_PROCESS_HANDLER_H

#include "include/cef_browser_process_handler.h"
#include "javascript_binding.h"
#include "javascript_bindings_handler.h"
#include "cef_value_wrapper.h"
#include "application_state_python.h"
#include "application_context_menu_binding.h"
#include "cef_custom_scheme.h"

class CefWrapperBrowserProcessHandler : public CefBrowserProcessHandler
{
private:
    /* Here will be the instance stored. */
    static CefRefPtr<CefWrapperBrowserProcessHandler> instance;

    /* Private constructor to prevent instancing. */
    CefWrapperBrowserProcessHandler();

    int init_width;
    int init_height;

public:
    /* Static access method. */
    static CefRefPtr<CefWrapperBrowserProcessHandler> GetInstance();

    static void SendReturnValueToJavascript(int message_id, CefValueWrapper returnValue);

    static void SetInitialResolution(int width, int height);

    static void SetJavascriptBindings(std::vector<JavascriptBinding> javascript_bindings,
                                      std::vector<JavascriptPythonBinding> javascript_python_bindings,
                                      std::vector<StateHandlerPythonBinding> stateHandlerPythonBindings,
                                      std::vector<ContextMenuBinding> contextMenuBindings,
                                      std::vector<CefCustomScheme> customSchemes, std::unordered_map<std::string, std::string> mimeTypeMap);

    static void SetStartUrl(std::string url);

    static void LoadUrl(std::string url);
    CefRefPtr<CefBrowser> FrameBrowser;
    CefRefPtr<CefBrowser> ContentBrowser;
    std::vector<JavascriptBinding> m_JavascriptBindings;
    std::vector<JavascriptPythonBinding> m_JavascriptPythonBindings;
    std::vector<StateHandlerPythonBinding> m_StateHandlerPythonBindings;
    std::vector<ContextMenuBinding> m_ContextMenuBindings;
    std::vector<CefCustomScheme> m_CustomSchemes;
    std::unordered_map<std::string, std::string> m_MimeTypeMap;
    CefRefPtr<CefClient> GetDefaultClient() override;

    void OnContextInitialized() override;

    std::string StartUrl;

IMPLEMENT_REFCOUNTING(CefWrapperBrowserProcessHandler);

};

#endif // CEF_WRAPPER_BROWSER_PROCESS_HANDLER_H
