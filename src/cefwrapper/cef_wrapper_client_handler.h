#ifndef CEF_WRAPPER_CLIENT_HANDLER_H_
#define CEF_WRAPPER_CLIENT_HANDLER_H_

#include "include/cef_client.h"

#include <list>

#include "include/wrapper/cef_helpers.h"
#include "javascript_binding.h"
#include "javascript_bindings_handler.h"


class CefWrapperClientHandler : public CefClient,
                      public CefDisplayHandler,
                      public CefLifeSpanHandler,
                      public CefLoadHandler,
                      public CefContextMenuHandler {
public:

  explicit CefWrapperClientHandler(bool use_views,
                std::vector<JavascriptBinding> javascript_bindings, std::vector<JavascriptPythonBinding> javascript_python_bindings);

  void OnLoadStart(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
                   TransitionType transition_type) override;
  ~CefWrapperClientHandler() override;

  // Provide access to the single global instance of this object.
  static CefWrapperClientHandler *GetInstance();

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
  CefRefPtr<CefDisplayHandler> GetDisplayHandler() override { return this; }

  CefRefPtr<CefLifeSpanHandler> GetLifeSpanHandler() override { return this; }

  CefRefPtr<CefLoadHandler> GetLoadHandler() override { return this; }

  // CefDisplayHandler methods:
  void OnTitleChange(CefRefPtr<CefBrowser> browser,
                     const CefString &title) override;

  // CefLifeSpanHandler methods:
  void OnAfterCreated(CefRefPtr<CefBrowser> browser) override;
  bool DoClose(CefRefPtr<CefBrowser> browser) override;
  void OnBeforeClose(CefRefPtr<CefBrowser> browser) override;

  // CefLoadHandler methods:
  void OnLoadError(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
                   ErrorCode errorCode, const CefString &errorText,
                   const CefString &failedUrl) override;

  // Request that all existing m_Browser windows close.
  void CloseAllBrowsers(bool force_close);

  bool IsClosing() const { return is_closing_; }

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

  bool IsReadyToExecuteJs();
  bool OnProcessMessageReceived(CefRefPtr<CefBrowser> browser,
                                CefRefPtr<CefFrame> frame,
                                CefProcessId source_process,
                                CefRefPtr<CefProcessMessage> message) override;
  void OnLoadingStateChange(CefRefPtr<CefBrowser> browser, bool isLoading,
                            bool canGoBack, bool canGoForward) override;


private:
  // Platform-specific implementation.
  void PlatformTitleChange(CefRefPtr<CefBrowser> browser,
                           const CefString &title);

  // True if the application is using the Views framework.
  const bool use_views_;

  // List of existing m_Browser windows. Only accessed on the CEF UI thread.
  using BrowserList = std::list<CefRefPtr<CefBrowser>>;
  BrowserList browser_list_;

  bool m_IsReadyToExecuteJs;
  std::vector<JavascriptBinding> m_JavascriptBindings;
  std::vector<JavascriptPythonBinding> m_JavascriptPythonBindings;
  bool is_closing_;

  // Include the default reference counting implementation.
  IMPLEMENT_REFCOUNTING(CefWrapperClientHandler);
};

#endif // CEF_WRAPPER_CLIENT_HANDLER_H_
