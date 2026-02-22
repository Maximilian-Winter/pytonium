#ifndef CEF_WRAPPER_RENDER_PROCESS_HANDLER_H_
#define CEF_WRAPPER_RENDER_PROCESS_HANDLER_H_

#include <unordered_map>
#include "include/cef_render_process_handler.h"
#include "javascript_binding.h"
#include "javascript_bindings_handler.h"
#include "javascript_python_binding_handler.h"
#include "application_state_javascript_handler.h"

struct PerBrowserRendererState {
    std::shared_ptr<ApplicationStateManager> applicationStateManager;
    CefRefPtr<AppStateV8Handler> appStateV8Handler;
    std::vector<JavascriptBinding> javascriptBindings;
    std::vector<JavascriptPythonBinding> javascriptPythonBindings;
    CefRefPtr<CefV8Handler> javascriptBindingHandler;
    CefRefPtr<JavascriptPythonBindingsHandler> javascriptPythonBindingHandler;
};

class SimpleRenderProcessHandler : public CefRenderProcessHandler
{
private:
    /* Here will be the instance stored. */
    static CefRefPtr<SimpleRenderProcessHandler> instance;

    /* Private constructor to prevent instancing. */
    SimpleRenderProcessHandler();

    std::unordered_map<int, PerBrowserRendererState> m_BrowserStates;

    PerBrowserRendererState& GetState(int browserId);

public:
    /* Static access method. */
    static CefRefPtr<SimpleRenderProcessHandler> getInstance();

    void OnContextCreated(CefRefPtr<CefBrowser> browser,
                          CefRefPtr<CefFrame> frame,
                          CefRefPtr<CefV8Context> context) override;

    void OnBrowserCreated(CefRefPtr<CefBrowser> browser,
                          CefRefPtr<CefDictionaryValue> extra_info) override;

    void OnBrowserDestroyed(CefRefPtr<CefBrowser> browser) override;

    bool OnProcessMessageReceived(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame, CefProcessId source_process,
                                  CefRefPtr<CefProcessMessage> message) override;

IMPLEMENT_REFCOUNTING(SimpleRenderProcessHandler);
};

#endif //CEF_WRAPPER_RENDER_PROCESS_HANDLER_H_