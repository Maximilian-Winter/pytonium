#include "cef_wrapper_client_handler.h"

#include <sstream>
#include <string>

#include "global_vars.h"
#include "include/base/cef_callback.h"
#include "include/cef_app.h"
#include "include/cef_parser.h"
#include "include/views/cef_browser_view.h"
#include "include/views/cef_window.h"
#include "include/wrapper/cef_closure_task.h"
#include "include/wrapper/cef_helpers.h"
#include "javascript_binding.h"
#include "javascript_bindings_handler.h"

namespace {
enum client_menu_ids {
  CLIENT_ID_SHOW_DEVTOOLS = MENU_ID_USER_FIRST,
  CLIENT_ID_CLOSE_DEVTOOLS,
  CLIENT_ID_INSPECT_ELEMENT,
  CLIENT_ID_SHOW_SSL_INFO,
  CLIENT_ID_CURSOR_CHANGE_DISABLED,
  CLIENT_ID_MEDIA_HANDLING_DISABLED,
  CLIENT_ID_OFFLINE,
  CLIENT_ID_TESTMENU_SUBMENU,
  CLIENT_ID_TESTMENU_CHECKITEM,
  CLIENT_ID_TESTMENU_RADIOITEM1,
  CLIENT_ID_TESTMENU_RADIOITEM2,
  CLIENT_ID_TESTMENU_RADIOITEM3,
};
CefWrapperClientHandler *g_instance = nullptr;


std::string GetDataURI(const std::string &data, const std::string &mime_type) {
  return "data:" + mime_type + ";base64," +
         CefURIEncode(CefBase64Encode(data.data(), data.size()), false)
             .ToString();
}

} // namespace

CefWrapperClientHandler::CefWrapperClientHandler(
    bool use_views, std::vector<JavascriptBinding> javascript_bindings, std::vector<JavascriptPythonBinding> javascript_python_bindings) : use_views_(use_views), is_closing_(false) {
  DCHECK(!g_instance);
  m_JavascriptBindings = javascript_bindings;
  m_JavascriptPythonBindings = javascript_python_bindings;
  g_instance = this;
  
}
CefWrapperClientHandler::~CefWrapperClientHandler() { g_instance = nullptr; }


CefWrapperClientHandler *CefWrapperClientHandler::GetInstance() { return g_instance; }

void CefWrapperClientHandler::OnBeforeContextMenu(CefRefPtr<CefBrowser> browser,
                                        CefRefPtr<CefFrame> frame,
                                        CefRefPtr<CefContextMenuParams> params,
                                        CefRefPtr<CefMenuModel> model) {
  CEF_REQUIRE_UI_THREAD();

  //model->Clear();

  if (model->GetCount() > 0)
    model->AddSeparator();

  model->AddItem(CLIENT_ID_SHOW_DEVTOOLS, "&Show DevTools");
  model->AddItem(CLIENT_ID_CLOSE_DEVTOOLS, "Close DevTools");
  model->AddSeparator();
  model->AddItem(CLIENT_ID_INSPECT_ELEMENT, "Inspect Element");


}

bool CefWrapperClientHandler::OnContextMenuCommand(CefRefPtr<CefBrowser> browser,
                                         CefRefPtr<CefFrame> frame,
                                         CefRefPtr<CefContextMenuParams> params,
                                         int command_id,
                                         EventFlags event_flags) {
  CEF_REQUIRE_UI_THREAD();

  switch (command_id) {
  case CLIENT_ID_SHOW_DEVTOOLS:
    ShowDevTools(browser, CefPoint());
    return true;
  case CLIENT_ID_CLOSE_DEVTOOLS:
    CloseDevTools(browser);
    return true;
  case CLIENT_ID_INSPECT_ELEMENT:
    ShowDevTools(browser, CefPoint(params->GetXCoord(), params->GetYCoord()));
    return true;
  default: // Allow default handling, if any.
    return true;
  }
}
void CefWrapperClientHandler::ShowDevTools(CefRefPtr<CefBrowser> browser,
                                 const CefPoint &inspect_element_at) {
  if (!CefCurrentlyOn(TID_UI)) {
    // Execute this method on the UI thread.
    CefPostTask(TID_UI, base::BindOnce(&CefWrapperClientHandler::ShowDevTools, this,
                                       browser, inspect_element_at));
    return;
  }

  CefWindowInfo windowInfo;
  CefRefPtr<CefClient> client;
  CefBrowserSettings settings;

  CefRefPtr<CefBrowserHost> host = browser->GetHost();

  host->ShowDevTools(windowInfo, client, settings, inspect_element_at);
}

void CefWrapperClientHandler::CloseDevTools(CefRefPtr<CefBrowser> browser) {
  browser->GetHost()->CloseDevTools();
}

void CefWrapperClientHandler::OnTitleChange(CefRefPtr<CefBrowser> browser,
                                  const CefString &title) {
  CEF_REQUIRE_UI_THREAD();

  if (use_views_) {
    // Set the title of the window using the Views framework.
    CefRefPtr<CefBrowserView> browser_view =
        CefBrowserView::GetForBrowser(browser);
    if (browser_view) {
      CefRefPtr<CefWindow> window = browser_view->GetWindow();
      if (window)
        window->SetTitle(title);
    }
  } else if (!IsChromeRuntimeEnabled()) {
    // Set the title of the window using platform APIs.
    PlatformTitleChange(browser, title);
  }
}

void CefWrapperClientHandler::OnAfterCreated(CefRefPtr<CefBrowser> browser) {
  CEF_REQUIRE_UI_THREAD();

  // Add to the list of existing browsers.
  browser_list_.push_back(browser);
}

bool CefWrapperClientHandler::DoClose(CefRefPtr<CefBrowser> browser) {
  CEF_REQUIRE_UI_THREAD();

  // Closing the main window requires special handling. See the DoClose()
  // documentation in the CEF header for a detailed destription of this
  // process.
  if (browser_list_.size() == 1) {
    // Set a flag to indicate that the window close should be allowed.
    is_closing_ = true;
  }

  // Allow the close. For windowed browsers this will result in the OS close
  // event being sent.
  return false;
}

void CefWrapperClientHandler::OnBeforeClose(CefRefPtr<CefBrowser> browser) {
  CEF_REQUIRE_UI_THREAD();

  // Remove from the list of existing browsers.
  BrowserList::iterator bit = browser_list_.begin();
  for (; bit != browser_list_.end(); ++bit) {
    if ((*bit)->IsSame(browser)) {
      browser_list_.erase(bit);
      break;
    }
  }
  g_IsRunning = false;
  if (browser_list_.empty()) {
    // All browser windows have closed. Quit the application message loop.
    CefQuitMessageLoop();
  }
}

void CefWrapperClientHandler::OnLoadError(CefRefPtr<CefBrowser> browser,
                                CefRefPtr<CefFrame> frame, ErrorCode errorCode,
                                const CefString &errorText,
                                const CefString &failedUrl) {
  CEF_REQUIRE_UI_THREAD();

  // Allow Chrome to show the error page.
  if (IsChromeRuntimeEnabled())
    return;

  // Don't display an error for downloaded files.
  if (errorCode == ERR_ABORTED)
    return;

  // Display a load error message using a data: URI.
  std::stringstream ss;
  ss << "<html><body bgcolor=\"white\">"
        "<h2>Failed to load URL "
     << std::string(failedUrl) << " with error " << std::string(errorText)
     << " (" << errorCode << ").</h2></body></html>";

  frame->LoadURL(GetDataURI(ss.str(), "text/html"));
}

void CefWrapperClientHandler::CloseAllBrowsers(bool force_close) {
  if (!CefCurrentlyOn(TID_UI)) {
    // Execute on the UI thread.
    CefPostTask(TID_UI, base::BindOnce(&CefWrapperClientHandler::CloseAllBrowsers, this,
                                       force_close));
    return;
  }

  if (browser_list_.empty())
    return;

  BrowserList::const_iterator it = browser_list_.begin();
  for (; it != browser_list_.end(); ++it)
    (*it)->GetHost()->CloseBrowser(force_close);
}


bool CefWrapperClientHandler::IsChromeRuntimeEnabled() {
  static int value = -1;
  if (value == -1) {
    CefRefPtr<CefCommandLine> command_line =
        CefCommandLine::GetGlobalCommandLine();
    value = command_line->HasSwitch("enable-chrome-runtime") ? 1 : 0;
  }
  return value == 1;
}
bool CefWrapperClientHandler::RunContextMenu(
    CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
    CefRefPtr<CefContextMenuParams> params, CefRefPtr<CefMenuModel> model,
    CefRefPtr<CefRunContextMenuCallback> callback) {
  return CefContextMenuHandler::RunContextMenu(browser, frame, params, model,
                                               callback);
}
void CefWrapperClientHandler::OnContextMenuDismissed(CefRefPtr<CefBrowser> browser,
                                           CefRefPtr<CefFrame> frame) {
  CefContextMenuHandler::OnContextMenuDismissed(browser, frame);
}
bool CefWrapperClientHandler::RunQuickMenu(
    CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
    const CefPoint &location, const CefSize &size,
    CefContextMenuHandler::QuickMenuEditStateFlags edit_state_flags,
    CefRefPtr<CefRunQuickMenuCallback> callback) {
  return CefContextMenuHandler::RunQuickMenu(browser, frame, location, size,
                                             edit_state_flags, callback);
}
bool CefWrapperClientHandler::OnQuickMenuCommand(
    CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame, int command_id,
    CefContextMenuHandler::EventFlags event_flags) {
  return CefContextMenuHandler::OnQuickMenuCommand(browser, frame, command_id,
                                                   event_flags);
}
void CefWrapperClientHandler::OnQuickMenuDismissed(CefRefPtr<CefBrowser> browser,
                                         CefRefPtr<CefFrame> frame) {
  CefContextMenuHandler::OnQuickMenuDismissed(browser, frame);
}
CefRefPtr<CefContextMenuHandler>
CefWrapperClientHandler::GetContextMenuHandler() {
  return this;
}
void CefWrapperClientHandler::OnLoadEnd(CefRefPtr<CefBrowser> browser,
                              CefRefPtr<CefFrame> frame, int httpStatusCode)
{
}
bool CefWrapperClientHandler::IsReadyToExecuteJs() { return m_IsReadyToExecuteJs; }
void CefWrapperClientHandler::OnLoadStart(
    CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
    CefLoadHandler::TransitionType transition_type) {
  m_IsReadyToExecuteJs = false;
}
bool CefWrapperClientHandler::OnProcessMessageReceived(
    CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
    CefProcessId source_process, CefRefPtr<CefProcessMessage> message) {
  const std::string& message_name = message->GetName();
  if (message_name == "javascript-binding")
  {
    CefRefPtr<CefListValue> argList = message->GetArgumentList();
    std::string funcName = argList->GetString(0);
    CefRefPtr<CefListValue> javascript_arg_types = argList->GetList(1);
    CefRefPtr<CefListValue> javascript_args = argList->GetList(2);
    // void* args = nullptr;
    int argsSize = (int)javascript_args->GetSize();

    auto* valueWrapper = new CefValueWrapper[argsSize];
    for (int i = 0; i < (int)javascript_args->GetSize(); ++i) {
      std::string type = javascript_arg_types->GetString(i);

      if(type == "int")
      {
        valueWrapper->Type = 0;
        valueWrapper->IntValue = javascript_args->GetInt(i);
      }
      else if(type == "bool")
      {
        valueWrapper->Type = 1;
        valueWrapper->BoolValue = javascript_args->GetBool(i);
      }
      else if(type == "double")
      {
        valueWrapper->Type = 2;
        valueWrapper->DoubleValue = javascript_args->GetDouble(i);
      }
      else if(type == "string")
      {
        valueWrapper->Type = 3;
        valueWrapper->StringValue = javascript_args->GetString(i);
      }
      ++valueWrapper;
    }

    valueWrapper -= argsSize;

    for (int i = 0; i < (int)m_JavascriptBindings.size(); ++i)
    {
      if(m_JavascriptBindings[i].functionName == funcName)
      {
        m_JavascriptBindings[i].function(argsSize, valueWrapper);
      }
    }
    delete[] valueWrapper;


    return true;
  }
  else if (message_name == "javascript-python-binding")
  {
    CefRefPtr<CefListValue> argList = message->GetArgumentList();
    std::string funcName = argList->GetString(0);
    CefRefPtr<CefListValue> javascript_arg_types = argList->GetList(1);
    CefRefPtr<CefListValue> javascript_args = argList->GetList(2);
   // void* args = nullptr;
    int argsSize = (int)javascript_args->GetSize();

    auto* valueWrapper = new CefValueWrapper[argsSize];
    for (int i = 0; i < (int)javascript_args->GetSize(); ++i) {
      std::string type = javascript_arg_types->GetString(i);

      if(type == "int")
      {
        valueWrapper->Type = 0;
        valueWrapper->IntValue = javascript_args->GetInt(i);
      }
      else if(type == "bool")
      {
        valueWrapper->Type = 1;
        valueWrapper->BoolValue = javascript_args->GetBool(i);
      }
      else if(type == "double")
      {
        valueWrapper->Type = 2;
        valueWrapper->DoubleValue = javascript_args->GetDouble(i);
      }
      else if(type == "string")
      {
        valueWrapper->Type = 3;
        valueWrapper->StringValue = javascript_args->GetString(i);
      }
      ++valueWrapper;
    }

    valueWrapper -= argsSize;

    for (int i = 0; i < (int)m_JavascriptPythonBindings.size(); ++i)
    {
      if(m_JavascriptPythonBindings[i].MessageTopic == funcName)
      {
        m_JavascriptPythonBindings[i].CallHandler(argsSize, valueWrapper);
      }
    }
    delete[] valueWrapper;
    return true;
  }
  return false;
}
void CefWrapperClientHandler::OnLoadingStateChange(
    CefRefPtr<CefBrowser> browser, bool isLoading, bool canGoBack,
    bool canGoForward) {
  if(!isLoading)
  {
    m_IsReadyToExecuteJs = true;
  }
  else
  {
    m_IsReadyToExecuteJs = false;
  }
}
