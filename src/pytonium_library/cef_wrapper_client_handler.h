#ifndef CEF_WRAPPER_CLIENT_HANDLER_H_
#define CEF_WRAPPER_CLIENT_HANDLER_H_

#include "include/cef_client.h"

#include <list>
#include <unordered_map>

#include "include/wrapper/cef_helpers.h"
#include "javascript_binding.h"
#include "javascript_bindings_handler.h"
#include "application_state_python.h"
#include "application_context_menu_binding.h"

#if defined(OS_WIN)
#include "osr_render_handler_dispatcher.h"
#endif

// Callback typedefs for window events
using window_event_string_callback_ptr = void (*)(void* user_data, const char* value);
using window_event_bool_callback_ptr = void (*)(void* user_data, bool value);

// Per-browser state stored in the shared client handler, keyed by browser ID.
struct PerBrowserState {
    bool isOsr = false;
    bool isReadyToExecuteJs = false;
    std::string currentContextMenuNamespace = "app";
    bool showDebugContextMenu = false;

    // Bindings registered for this specific browser
    std::vector<JavascriptBinding> javascriptBindings;
    std::vector<JavascriptPythonBinding> javascriptPythonBindings;
    std::vector<StateHandlerPythonBinding> stateHandlerPythonBindings;
    std::vector<ContextMenuBinding> contextMenuBindings;
    std::unordered_map<std::string, std::vector<ContextMenuBinding>> contextMenuBindingsMap;

    // Window event callbacks
    window_event_string_callback_ptr onTitleChangeCallback = nullptr;
    void* onTitleChangeUserData = nullptr;
    window_event_string_callback_ptr onAddressChangeCallback = nullptr;
    void* onAddressChangeUserData = nullptr;
    window_event_bool_callback_ptr onFullscreenChangeCallback = nullptr;
    void* onFullscreenChangeUserData = nullptr;
};

class CefWrapperClientHandler : public CefClient,
                                public CefDisplayHandler,
                                public CefLifeSpanHandler,
                                public CefLoadHandler,
                                public CefContextMenuHandler
{
public:

    explicit CefWrapperClientHandler(bool use_views);

    void OnLoadStart(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
                     TransitionType transition_type) override;

    ~CefWrapperClientHandler() override;

    // Provide access to the single global instance of this object.
    static CefWrapperClientHandler *GetInstance();

    // Register per-browser bindings after CreateBrowserSync
    void RegisterBrowserBindings(int browserId,
        std::vector<JavascriptBinding> jsBindings,
        std::vector<JavascriptPythonBinding> jsPythonBindings,
        std::vector<StateHandlerPythonBinding> stateBindings,
        std::vector<ContextMenuBinding> contextMenuBindings);

    void OnBeforeContextMenu(CefRefPtr<CefBrowser> browser,
                             CefRefPtr<CefFrame> frame,
                             CefRefPtr<CefContextMenuParams> params,
                             CefRefPtr<CefMenuModel> model) override;

    bool OnContextMenuCommand(CefRefPtr<CefBrowser> browser,
                              CefRefPtr<CefFrame> frame,
                              CefRefPtr<CefContextMenuParams> params,
                              int command_id, EventFlags event_flags) override;

    // Show a new DevTools popup window.
    void ShowDevTools(CefRefPtr<CefBrowser> browser,
                      const CefPoint &inspect_element_at);

    // Close the existing DevTools popup window, if any.
    void CloseDevTools(CefRefPtr<CefBrowser> browser);

    // CefClient methods:
    CefRefPtr<CefDisplayHandler> GetDisplayHandler() override
    { return this; }

    CefRefPtr<CefLifeSpanHandler> GetLifeSpanHandler() override
    { return this; }

    CefRefPtr<CefLoadHandler> GetLoadHandler() override
    { return this; }

#if defined(OS_WIN)
    CefRefPtr<CefRenderHandler> GetRenderHandler() override
    { return m_OsrDispatcher; }

    OsrRenderHandlerDispatcher* GetOsrDispatcher()
    { return m_OsrDispatcher.get(); }
#endif

    // CefDisplayHandler methods:
    void OnTitleChange(CefRefPtr<CefBrowser> browser,
                       const CefString &title) override;
    void OnAddressChange(CefRefPtr<CefBrowser> browser,
                         CefRefPtr<CefFrame> frame,
                         const CefString &url) override;
    void OnFullscreenModeChange(CefRefPtr<CefBrowser> browser,
                                bool fullscreen) override;

    // CefLifeSpanHandler methods:
    void OnAfterCreated(CefRefPtr<CefBrowser> browser) override;

    bool DoClose(CefRefPtr<CefBrowser> browser) override;

    void OnBeforeClose(CefRefPtr<CefBrowser> browser) override;

    // CefLoadHandler methods:
    void OnLoadError(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
                     ErrorCode errorCode, const CefString &errorText,
                     const CefString &failedUrl) override;

    // Request that all existing browser windows close.
    void CloseAllBrowsers(bool force_close);

    bool IsClosing() const
    { return is_closing_; }

    // Returns true if the Chrome runtime is enabled.
    static bool IsChromeRuntimeEnabled();

    bool RunContextMenu(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
                        CefRefPtr<CefContextMenuParams> params,
                        CefRefPtr<CefMenuModel> model,
                        CefRefPtr<CefRunContextMenuCallback> callback) override;

    void OnContextMenuDismissed(CefRefPtr<CefBrowser> browser,
                                CefRefPtr<CefFrame> frame) override;

    bool RunQuickMenu(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
                      const CefPoint &location, const CefSize &size,
                      QuickMenuEditStateFlags edit_state_flags,
                      CefRefPtr<CefRunQuickMenuCallback> callback) override;

    bool OnQuickMenuCommand(CefRefPtr<CefBrowser> browser,
                            CefRefPtr<CefFrame> frame, int command_id,
                            EventFlags event_flags) override;

    void OnQuickMenuDismissed(CefRefPtr<CefBrowser> browser,
                              CefRefPtr<CefFrame> frame) override;

    CefRefPtr<CefContextMenuHandler> GetContextMenuHandler() override;

    void OnLoadEnd(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
                   int httpStatusCode) override;

    bool IsReadyToExecuteJs(int browserId);

    bool OnProcessMessageReceived(CefRefPtr<CefBrowser> browser,
                                  CefRefPtr<CefFrame> frame,
                                  CefProcessId source_process,
                                  CefRefPtr<CefProcessMessage> message) override;

    void OnLoadingStateChange(CefRefPtr<CefBrowser> browser, bool isLoading,
                              bool canGoBack, bool canGoForward) override;

    void SetCurrentContextMenuName(int browserId, const std::string& context_menu_namespace);

    void SetShowDebugContextMenu(int browserId, bool show);

    void SetContextMenuBindings(int browserId, std::vector<ContextMenuBinding> contextMenuBindings);

    // Window event callback setters (per-browser)
    void SetOnTitleChangeCallback(int browserId, window_event_string_callback_ptr callback, void* user_data);
    void SetOnAddressChangeCallback(int browserId, window_event_string_callback_ptr callback, void* user_data);
    void SetOnFullscreenChangeCallback(int browserId, window_event_bool_callback_ptr callback, void* user_data);

    // Access per-browser state
    PerBrowserState& GetBrowserState(int browserId);

private:
    // Platform-specific implementation.
    void PlatformTitleChange(CefRefPtr<CefBrowser> browser,
                             const CefString &title);

    // Platform-specific window subclassing for resize borders
    void PlatformSubclassWindow(CefRefPtr<CefBrowser> browser);
    void PlatformRemoveSubclass(CefRefPtr<CefBrowser> browser);

    // True if the application is using the Views framework.
    const bool use_views_;

    // List of existing browser windows. Only accessed on the CEF UI thread.
    using BrowserList = std::list<CefRefPtr<CefBrowser>>;
    BrowserList browser_list_;

    bool is_closing_;

    // Per-browser state map, keyed by browser->GetIdentifier()
    std::unordered_map<int, PerBrowserState> m_BrowserStates;

#if defined(OS_WIN)
    // OSR render handler dispatcher (routes OnPaint by browser ID)
    CefRefPtr<OsrRenderHandlerDispatcher> m_OsrDispatcher;
#endif

    // Include the default reference counting implementation.
IMPLEMENT_REFCOUNTING(CefWrapperClientHandler);
};

#endif // CEF_WRAPPER_CLIENT_HANDLER_H_
