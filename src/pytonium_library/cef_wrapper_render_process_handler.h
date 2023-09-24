#ifndef CEF_WRAPPER_RENDER_PROCESS_HANDLER_H_
#define CEF_WRAPPER_RENDER_PROCESS_HANDLER_H_
#include "include/cef_render_process_handler.h"
#include "javascript_binding.h"
#include "javascript_bindings_handler.h"
#include "javascript_python_binding_handler.h"

class SimpleRenderProcessHandler: public CefRenderProcessHandler
{
private:
    /* Here will be the instance stored. */
    static CefRefPtr<SimpleRenderProcessHandler> instance;

    /* Private constructor to prevent instancing. */
    SimpleRenderProcessHandler();

public:
    /* Static access method. */
    static CefRefPtr<SimpleRenderProcessHandler> getInstance();

    static void
    SetJavascriptBindings(std::vector<JavascriptBinding> javascript_bindings, std::vector<JavascriptPythonBinding> javascript_python_bindings);
  //SimpleRenderProcessHandler::SimpleRenderProcessHandler(std::vector<JSNativeApi> nativeApi);

  void OnContextCreated(CefRefPtr<CefBrowser> browser,
                        CefRefPtr<CefFrame> frame,
                        CefRefPtr<CefV8Context> context) override ;


  void OnBrowserCreated(CefRefPtr<CefBrowser> browser,
                        CefRefPtr<CefDictionaryValue> extra_info) override;

    bool OnProcessMessageReceived(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame, CefProcessId source_process,
                                  CefRefPtr<CefProcessMessage> message) override;

    std::vector<JavascriptBinding> m_Javascript_Bindings;
  std::vector<JavascriptPythonBinding> m_Javascript_Python_Bindings;
  std::vector<JavascriptPythonEventBinding> m_Javascript_Python_Event_Bindings;
    CefRefPtr<CefV8Handler> m_JavascriptBindingHandler;
    CefRefPtr<JavascriptPythonBindingsHandler> m_JavascriptPythonBindingHandler;
  IMPLEMENT_REFCOUNTING(SimpleRenderProcessHandler);
};
#endif //CEF_WRAPPER_RENDER_PROCESS_HANDLER_H_