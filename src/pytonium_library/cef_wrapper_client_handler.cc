#include "cef_wrapper_client_handler.h"

#include <filesystem>
#include <sstream>
#include <string>
#include <utility>

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
#include "cef_value_wrapper.h"

namespace
{
    enum client_menu_ids
    {
        CLIENT_ID_SHOW_DEVTOOLS = MENU_ID_USER_FIRST,
        CLIENT_ID_CLOSE_DEVTOOLS,
        CLIENT_ID_INSPECT_ELEMENT,
        CLIENT_ID_PYTONIUM_CUSTOM_FIRST
    };
    CefWrapperClientHandler *g_instance = nullptr;


    std::string GetDataURI(const std::string &data, const std::string &mime_type)
    {
        return "data:" + mime_type + ";base64," +
               CefURIEncode(CefBase64Encode(data.data(), data.size()), false)
                       .ToString();
    }

} // namespace

CefWrapperClientHandler::CefWrapperClientHandler(
        bool use_views, std::vector<JavascriptBinding> javascript_bindings,
        std::vector<JavascriptPythonBinding> javascript_python_bindings,
        std::vector<StateHandlerPythonBinding> stateHandlerPythonBindings, std::vector<ContextMenuBinding> contextMenuBindings) : use_views_(use_views), is_closing_(false)
{
    DCHECK(!g_instance);
    m_JavascriptBindings = std::move(javascript_bindings);
    m_JavascriptPythonBindings = std::move(javascript_python_bindings);
    m_StateHandlerPythonBindings = std::move(stateHandlerPythonBindings);
    m_ContextMenuBindings = std::move(contextMenuBindings);

    for (const auto& contextMenuEntry: m_ContextMenuBindings)
    {
        m_ContextMenuBindingsMap[contextMenuEntry.Namespace].emplace_back(contextMenuEntry);
    }

    m_IsReadyToExecuteJs = false;
    m_ShowDebugContextMenu = false;
    g_instance = this;

}

CefWrapperClientHandler::~CefWrapperClientHandler()
{ g_instance = nullptr; }


CefWrapperClientHandler *CefWrapperClientHandler::GetInstance()
{ return g_instance; }

void CefWrapperClientHandler::OnBeforeContextMenu(CefRefPtr<CefBrowser> browser,
                                                  CefRefPtr<CefFrame> frame,
                                                  CefRefPtr<CefContextMenuParams> params,
                                                  CefRefPtr<CefMenuModel> model)
{
    CEF_REQUIRE_UI_THREAD();
    if(!m_ShowDebugContextMenu)
    {
        model->Clear();
    }
    else
    {
        if (model->GetCount() > 0)
            model->AddSeparator();

        model->AddItem(CLIENT_ID_SHOW_DEVTOOLS, "&Show DevTools");
        model->AddItem(CLIENT_ID_CLOSE_DEVTOOLS, "Close DevTools");
        model->AddSeparator();
        model->AddItem(CLIENT_ID_INSPECT_ELEMENT, "Inspect Element");
        model->AddSeparator();
    }

    for (const auto& contextMenuEntry: m_ContextMenuBindingsMap[m_CurrentContextMenuNamespace])
    {
        model->AddItem(contextMenuEntry.CommandId + CLIENT_ID_PYTONIUM_CUSTOM_FIRST, contextMenuEntry.DisplayName);
    }


}

bool CefWrapperClientHandler::OnContextMenuCommand(CefRefPtr<CefBrowser> browser,
                                                   CefRefPtr<CefFrame> frame,
                                                   CefRefPtr<CefContextMenuParams> params,
                                                   int command_id,
                                                   EventFlags event_flags)
{
    CEF_REQUIRE_UI_THREAD();

    switch (command_id)
    {
        case CLIENT_ID_SHOW_DEVTOOLS:
            ShowDevTools(browser, CefPoint());
            return true;
        case CLIENT_ID_CLOSE_DEVTOOLS:
            CloseDevTools(browser);
            return true;
        case CLIENT_ID_INSPECT_ELEMENT:
            ShowDevTools(browser, CefPoint(params->GetXCoord(), params->GetYCoord()));
            return true;
        default:
            m_ContextMenuBindingsMap[m_CurrentContextMenuNamespace][command_id-CLIENT_ID_PYTONIUM_CUSTOM_FIRST].OnContextMenuEntryClicked();
            return true;
    }
}

void CefWrapperClientHandler::ShowDevTools(CefRefPtr<CefBrowser> browser,
                                           const CefPoint &inspect_element_at)
{
    if (!CefCurrentlyOn(TID_UI))
    {
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

void CefWrapperClientHandler::CloseDevTools(CefRefPtr<CefBrowser> browser)
{
    browser->GetHost()->CloseDevTools();
}

void CefWrapperClientHandler::OnTitleChange(CefRefPtr<CefBrowser> browser,
                                            const CefString &title)
{
    CEF_REQUIRE_UI_THREAD();

    if (use_views_)
    {
        // Set the title of the window using the Views framework.
        CefRefPtr<CefBrowserView> browser_view =
                CefBrowserView::GetForBrowser(browser);
        if (browser_view)
        {
            CefRefPtr<CefWindow> window = browser_view->GetWindow();
            if (window)
                window->SetTitle(title);
        }
    } else if (!IsChromeRuntimeEnabled())
    {
        // Set the title of the window using platform APIs.
        PlatformTitleChange(browser, title);
    }
}

void CefWrapperClientHandler::OnAfterCreated(CefRefPtr<CefBrowser> browser)
{
    CEF_REQUIRE_UI_THREAD();
    if(browser_list_.empty())
    {
        SetupCustomWindowFrame(browser);
    }

    // Add to the list of existing browsers.
    browser_list_.push_back(browser);
}

void CefWrapperClientHandler::SetupCustomWindowFrame(CefRefPtr<CefBrowser> browser) {
    HWND hwnd = browser->GetHost()->GetWindowHandle();
    DWORD style = GetWindowLong(hwnd, GWL_STYLE);
    SetWindowLong(hwnd, GWL_STYLE, style & ~WS_CAPTION & ~WS_THICKFRAME);

    // Load custom HTML for the window frame
    std::filesystem::path entryPoint = std::filesystem::current_path() / "custom_frame.html";
    browser->GetMainFrame()->LoadURL(entryPoint.c_str());
}

bool CefWrapperClientHandler::OnConsoleMessage(CefRefPtr<CefBrowser> browser,
                                               cef_log_severity_t level,
                                               const CefString& message,
                                               const CefString& source,
                                               int line) {
    // Handle custom window controls here
    if (message == "minimize") {
        ShowWindow(browser->GetHost()->GetWindowHandle(), SW_MINIMIZE);
        return true;
    } else if (message == "maximize") {
        ShowWindow(browser->GetHost()->GetWindowHandle(), SW_MAXIMIZE);
        return true;
    } else if (message == "close") {
        browser->GetHost()->CloseBrowser(false);
        return true;
    }

    // Call the base class implementation for other console messages
    return CefDisplayHandler::OnConsoleMessage(browser, level, message, source, line);
}

bool CefWrapperClientHandler::DoClose(CefRefPtr<CefBrowser> browser)
{
    CEF_REQUIRE_UI_THREAD();

    // Closing the main window requires special handling. See the DoClose()
    // documentation in the CEF header for a detailed destription of this
    // process.
    if (browser_list_.size() == 1)
    {
        // Set a flag to indicate that the window close should be allowed.
        is_closing_ = true;
    }

    // Allow the close. For windowed browsers this will result in the OS close
    // event being sent.
    return false;
}

void CefWrapperClientHandler::OnBeforeClose(CefRefPtr<CefBrowser> browser)
{
    CEF_REQUIRE_UI_THREAD();

    // Remove from the list of existing browsers.
    BrowserList::iterator bit = browser_list_.begin();
    for (; bit != browser_list_.end(); ++bit)
    {
        if ((*bit)->IsSame(browser))
        {
            browser_list_.erase(bit);
            break;
        }
    }
    g_IsRunning = false;
    if (browser_list_.empty())
    {
        // All browser windows have closed. Quit the application message loop.
        CefQuitMessageLoop();
    }
}

void CefWrapperClientHandler::OnLoadError(CefRefPtr<CefBrowser> browser,
                                          CefRefPtr<CefFrame> frame, ErrorCode errorCode,
                                          const CefString &errorText,
                                          const CefString &failedUrl)
{
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

void CefWrapperClientHandler::CloseAllBrowsers(bool force_close)
{
    if (!CefCurrentlyOn(TID_UI))
    {
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


bool CefWrapperClientHandler::IsChromeRuntimeEnabled()
{
    static int value = -1;
    if (value == -1)
    {
        CefRefPtr<CefCommandLine> command_line =
                CefCommandLine::GetGlobalCommandLine();
        value = command_line->HasSwitch("enable-chrome-runtime") ? 1 : 0;
    }
    return value == 1;
}

bool CefWrapperClientHandler::RunContextMenu(
        CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
        CefRefPtr<CefContextMenuParams> params, CefRefPtr<CefMenuModel> model,
        CefRefPtr<CefRunContextMenuCallback> callback)
{
    return CefContextMenuHandler::RunContextMenu(browser, frame, params, model,
                                                 callback);
}

void CefWrapperClientHandler::OnContextMenuDismissed(CefRefPtr<CefBrowser> browser,
                                                     CefRefPtr<CefFrame> frame)
{
    CefContextMenuHandler::OnContextMenuDismissed(browser, frame);
}

bool CefWrapperClientHandler::RunQuickMenu(
        CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
        const CefPoint &location, const CefSize &size,
        CefContextMenuHandler::QuickMenuEditStateFlags edit_state_flags,
        CefRefPtr<CefRunQuickMenuCallback> callback)
{
    return CefContextMenuHandler::RunQuickMenu(browser, frame, location, size,
                                               edit_state_flags, callback);
}

bool CefWrapperClientHandler::OnQuickMenuCommand(
        CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame, int command_id,
        CefContextMenuHandler::EventFlags event_flags)
{
    return CefContextMenuHandler::OnQuickMenuCommand(browser, frame, command_id,
                                                     event_flags);
}

void CefWrapperClientHandler::OnQuickMenuDismissed(CefRefPtr<CefBrowser> browser,
                                                   CefRefPtr<CefFrame> frame)
{
    CefContextMenuHandler::OnQuickMenuDismissed(browser, frame);
}

CefRefPtr<CefContextMenuHandler>
CefWrapperClientHandler::GetContextMenuHandler()
{
    return this;
}

void CefWrapperClientHandler::OnLoadEnd(CefRefPtr<CefBrowser> browser,
                                        CefRefPtr<CefFrame> frame, int httpStatusCode)
{
}

bool CefWrapperClientHandler::IsReadyToExecuteJs()
{ return m_IsReadyToExecuteJs; }

void CefWrapperClientHandler::OnLoadStart(
        CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
        CefLoadHandler::TransitionType transition_type)
{
    m_IsReadyToExecuteJs = false;
}

bool CefWrapperClientHandler::OnProcessMessageReceived(
        CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
        CefProcessId source_process, CefRefPtr<CefProcessMessage> message)
{
    const std::string &message_name = message->GetName();
    if (message_name == "javascript-binding")
    {
        CefRefPtr<CefListValue> argList = message->GetArgumentList();
        std::string funcName = argList->GetString(0);
        CefRefPtr<CefListValue> javascript_arg_types = argList->GetList(1);
        CefRefPtr<CefListValue> javascript_args = argList->GetList(2);
        // void* args = nullptr;
        int argsSize = (int) javascript_args->GetSize();

        auto *valueWrapper = new CefValueWrapper[argsSize];
        for (int i = 0; i < (int) javascript_args->GetSize(); ++i)
        {
            std::string type = javascript_arg_types->GetString(i);
            valueWrapper[i] = CefValueWrapperHelper::ConvertCefValueToWrapper(javascript_args->GetValue(i));
        }


        for (int i = 0; i < (int) m_JavascriptBindings.size(); ++i)
        {
            if (m_JavascriptBindings[i].functionName == funcName)
            {
                m_JavascriptBindings[i].function(argsSize, valueWrapper);
            }
        }
        delete[] valueWrapper;


        return true;
    } else if (message_name == "javascript-python-binding")
    {
        CefRefPtr<CefListValue> argList = message->GetArgumentList();
        std::string funcName = argList->GetString(0);
        CefRefPtr<CefListValue> javascript_arg_types = argList->GetList(1);
        CefRefPtr<CefListValue> javascript_args = argList->GetList(2);
        // void* args = nullptr;
        int argsSize = (int) javascript_args->GetSize();

        auto *valueWrapper = new CefValueWrapper[argsSize];
        for (int i = 0; i < (int) javascript_args->GetSize(); ++i)
        {
            std::string type = javascript_arg_types->GetString(i);
            valueWrapper[i] = CefValueWrapperHelper::ConvertCefValueToWrapper(javascript_args->GetValue(i));
        }


        for (int i = 0; i < (int) m_JavascriptPythonBindings.size(); ++i)
        {
            if (m_JavascriptPythonBindings[i].FunctionName == funcName)
            {
                m_JavascriptPythonBindings[i].CallHandler(argsSize, valueWrapper, argList->GetInt(3));
                break;
            }
        }
        delete[] valueWrapper;
        return true;
    } else if (message_name == "push-app-state-update")
    {
        CefRefPtr<CefListValue> argList = message->GetArgumentList();
        if (argList->GetSize() == 3)
        {
            std::string namespaceName =
                    argList->GetValue(0)->GetType() == VTYPE_STRING ? argList->GetValue(0)->GetString() : "";
            std::string key = argList->GetValue(1)->GetType() == VTYPE_STRING ? argList->GetValue(1)->GetString() : "";
            if (namespaceName.empty() || key.empty())
            {
                return false;
            }
            CefValueWrapper wrap = CefValueWrapperHelper::ConvertCefValueToWrapper(argList->GetValue(2));

            for (const auto &stateHandler: m_StateHandlerPythonBindings)
            {
                stateHandler.UpdateState(namespaceName, key, wrap);
            }
            return true;
        } else
        {
            return false;
        }
    } else if (message_name == "set-context-menu-namespace")
    {
        CefRefPtr<CefListValue> argList = message->GetArgumentList();

        m_CurrentContextMenuNamespace = argList->GetString(0);
    }
    return false;
}

void CefWrapperClientHandler::OnLoadingStateChange(
        CefRefPtr<CefBrowser> browser, bool isLoading, bool canGoBack,
        bool canGoForward)
{
    if (!isLoading)
    {
        m_IsReadyToExecuteJs = true;
    } else
    {
        m_IsReadyToExecuteJs = false;
    }
}

void CefWrapperClientHandler::SetCurrentContextMenuName(const std::string& context_menu_namespace)
{
    m_CurrentContextMenuNamespace = context_menu_namespace;
}

void CefWrapperClientHandler::SetShowDebugContextMenu(bool show)
{
    m_ShowDebugContextMenu = show;
}

void CefWrapperClientHandler::SetContextMenuBindings(std::vector<ContextMenuBinding> contextMenuBindings)
{
    m_ContextMenuBindings = std::move(contextMenuBindings);
    m_ContextMenuBindingsMap.clear();
    for (const auto& contextMenuEntry: m_ContextMenuBindings)
    {
        m_ContextMenuBindingsMap[contextMenuEntry.Namespace].emplace_back(contextMenuEntry);
    }
}
