

#include "cef_wrapper_browser_process_handler.h"

#include <cstring>
#include <iostream>
#include <utility>
#include "cef_wrapper_client_handler.h"
#include "cef_wrapper_render_process_handler.h"
#include "custom_protocol_scheme_handler.h"
#include "javascript_binding.h"
#include "cef_value_wrapper.h"

#include "include/internal/cef_types_runtime.h"
#include "include/internal/cef_types.h"


CefWrapperBrowserProcessHandler::CefWrapperBrowserProcessHandler() : init_width(1024), init_height(768), init_frameless(false) {}

/* Null, because instance will be initialized on demand. */
CefRefPtr<CefWrapperBrowserProcessHandler>
        CefWrapperBrowserProcessHandler::instance = nullptr;

CefRefPtr<CefWrapperBrowserProcessHandler>
CefWrapperBrowserProcessHandler::GetInstance()
{
    if (instance == nullptr)
    {
        instance = CefRefPtr<CefWrapperBrowserProcessHandler>(
                new CefWrapperBrowserProcessHandler());
        instance->init_width = 1024;
        instance->init_height = 768;
    }

    return instance;
}

void CefWrapperBrowserProcessHandler::SetJavascriptBindings(
        std::vector<JavascriptBinding> javascript_bindings,
        std::vector<JavascriptPythonBinding> javascript_python_bindings,
        std::vector<StateHandlerPythonBinding> stateHandlerPythonBindings,
        std::vector<ContextMenuBinding> contextMenuBindings,
        std::vector<CefCustomScheme> customSchemes, std::unordered_map<std::string, std::string> mimeTypeMap)
{
    GetInstance()->m_JavascriptBindings = std::move(javascript_bindings);
    GetInstance()->m_JavascriptPythonBindings = std::move(javascript_python_bindings);
    GetInstance()->m_StateHandlerPythonBindings = std::move(stateHandlerPythonBindings);
    GetInstance()->m_ContextMenuBindings = std::move(contextMenuBindings);
    GetInstance()->m_CustomSchemes = std::move(customSchemes);
    GetInstance()->m_MimeTypeMap = std::move(mimeTypeMap);
    // Bindings are now registered per-browser via RegisterBrowserBindings after CreateBrowserSync

}

CefRefPtr<CefClient> CefWrapperBrowserProcessHandler::GetDefaultClient()
{
    return CefWrapperClientHandler::GetInstance();
}

void CefWrapperBrowserProcessHandler::OnContextInitialized()
{
    CEF_REQUIRE_UI_THREAD();

    CefRefPtr<CefCommandLine> command_line =
            CefCommandLine::GetGlobalCommandLine();

    bool use_views = command_line->HasSwitch("use-views");
    std::cout << "Use Views: " << (use_views ? "YES" : "NO") << std::endl;

    // Register custom scheme handler factories
    RegisterSchemeHandlerFactory(m_CustomSchemes, m_MimeTypeMap);

    // Create the shared client handler (browser creation is now deferred to
    // PytoniumLibrary::CreateBrowser)
    if (!CefWrapperClientHandler::GetInstance()) {
        new CefWrapperClientHandler(use_views);
    }
}

void CefWrapperBrowserProcessHandler::SetStartUrl(std::string url)
{
    CefWrapperBrowserProcessHandler::GetInstance()->StartUrl = url;
}

void CefWrapperBrowserProcessHandler::SetInitialResolution(int width,
                                                           int height)
{
    GetInstance()->init_width = width;
    GetInstance()->init_height = height;
}

void CefWrapperBrowserProcessHandler::SetFramelessWindow(bool frameless)
{
    GetInstance()->init_frameless = frameless;
}
