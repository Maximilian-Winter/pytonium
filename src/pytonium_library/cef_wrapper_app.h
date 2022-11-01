#ifndef CEF_WRAPPER_APP_H_
#define CEF_WRAPPER_APP_H_

#include "cef_wrapper_browser_process_handler.h"
#include "cef_wrapper_render_process_handler.h"
#include "include/cef_app.h"
#include "javascript_binding.h"
#include "javascript_bindings_handler.h"

class CefWrapperApp : public CefApp {
public:
  CefWrapperApp(
      std::string start_url, std::vector<JavascriptBinding> javascript_bindings,
      std::vector<JavascriptPythonBinding> javascript_python_bindings);

  CefRefPtr<CefBrowser> GetBrowser();

  CefRefPtr<CefBrowserProcessHandler> GetBrowserProcessHandler() override {
    return CefWrapperBrowserProcessHandler::GetInstance();
  }

  CefRefPtr<CefRenderProcessHandler> GetRenderProcessHandler() override {
    return SimpleRenderProcessHandler::getInstance();
  }

  void OnBeforeCommandLineProcessing(
      const CefString &process_type,
      CefRefPtr<CefCommandLine> command_line) override;

  void LoadUrl(std::string url);
  void
  OnRegisterCustomSchemes(CefRawPtr<CefSchemeRegistrar> registrar) override;

private:
  std::vector<JavascriptBinding> m_Javascript_Bindings;
  std::vector<JavascriptPythonBinding> m_Javascript_Python_Bindings;

  IMPLEMENT_REFCOUNTING(CefWrapperApp);
};

#endif // CEF_WRAPPER_APP_H_
