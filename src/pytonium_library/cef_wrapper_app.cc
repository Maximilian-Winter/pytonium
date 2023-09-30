



#include "cef_wrapper_app.h"

#include <utility>

#include "include/cef_browser.h"
#include "include/cef_command_line.h"

#include "include/cef_origin_whitelist.h"
#include "javascript_binding.h"
#include "javascript_bindings_handler.h"

CefRefPtr<CefBrowser> CefWrapperApp::GetBrowser()
{
    return CefWrapperBrowserProcessHandler::GetInstance()->Browser;
}

void CefWrapperApp::OnBeforeCommandLineProcessing(
    const CefString &process_type, CefRefPtr<CefCommandLine> command_line) {
  //command_line->AppendSwitch("allow-file-access-from-files");
}

CefWrapperApp::CefWrapperApp(std::string start_url, std::vector<JavascriptBinding> javascript_bindings, std::vector<JavascriptPythonBinding> javascript_python_bindings, std::vector<StateHandlerPythonBinding> stateHandlerPythonBindings,  std::vector<ContextMenuBinding> contextMenuBindings) {
  m_Javascript_Bindings = std::move(javascript_bindings);
  m_Javascript_Python_Bindings = std::move(javascript_python_bindings);
  m_StateHandlerPythonBindings = std::move(stateHandlerPythonBindings);
  CefWrapperBrowserProcessHandler::SetJavascriptBindings(
      m_Javascript_Bindings, m_Javascript_Python_Bindings, m_StateHandlerPythonBindings, std::move(contextMenuBindings));
  CefWrapperBrowserProcessHandler::SetStartUrl(std::move(start_url));
}

void CefWrapperApp::LoadUrl(std::string url) {
  CefWrapperBrowserProcessHandler::LoadUrl(std::move(url));
}
void CefWrapperApp::OnRegisterCustomSchemes(
    CefRawPtr<CefSchemeRegistrar> registrar) {
  //registrar->AddCustomScheme("zen", CEF_SCHEME_OPTION_STANDARD | CEF_SCHEME_OPTION_CORS_ENABLED);
}
