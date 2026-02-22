#include "cef_wrapper_client_handler.h"

#include <atomic>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

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
    std::atomic<CefWrapperClientHandler*> g_instance{nullptr};


    std::string GetDataURI(const std::string &data, const std::string &mime_type)
    {
        return "data:" + mime_type + ";base64," +
               CefURIEncode(CefBase64Encode(data.data(), data.size()), false)
                       .ToString();
    }

} // namespace

CefWrapperClientHandler::CefWrapperClientHandler(bool use_views)
    : use_views_(use_views), is_closing_(false)
{
    g_instance.store(this, std::memory_order_release);
}

CefWrapperClientHandler::~CefWrapperClientHandler()
{ g_instance.store(nullptr, std::memory_order_release); }


CefWrapperClientHandler *CefWrapperClientHandler::GetInstance()
{
    CefWrapperClientHandler* instance = g_instance.load(std::memory_order_acquire);
    if (!instance) {
        return nullptr;
    }
    return instance;
}

PerBrowserState& CefWrapperClientHandler::GetBrowserState(int browserId)
{
    return m_BrowserStates[browserId];
}

void CefWrapperClientHandler::RegisterBrowserBindings(int browserId,
    std::vector<JavascriptBinding> jsBindings,
    std::vector<JavascriptPythonBinding> jsPythonBindings,
    std::vector<StateHandlerPythonBinding> stateBindings,
    std::vector<ContextMenuBinding> contextMenuBindings)
{
    auto& state = GetBrowserState(browserId);
    state.javascriptBindings = std::move(jsBindings);
    state.javascriptPythonBindings = std::move(jsPythonBindings);
    state.stateHandlerPythonBindings = std::move(stateBindings);
    state.contextMenuBindings = std::move(contextMenuBindings);

    state.contextMenuBindingsMap.clear();
    for (const auto& entry : state.contextMenuBindings)
    {
        state.contextMenuBindingsMap[entry.Namespace].emplace_back(entry);
    }
}

void CefWrapperClientHandler::OnBeforeContextMenu(CefRefPtr<CefBrowser> browser,
                                                  CefRefPtr<CefFrame> frame,
                                                  CefRefPtr<CefContextMenuParams> params,
                                                  CefRefPtr<CefMenuModel> model)
{
    CEF_REQUIRE_UI_THREAD();
    auto& state = GetBrowserState(browser->GetIdentifier());

    if(!state.showDebugContextMenu)
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

    for (const auto& contextMenuEntry: state.contextMenuBindingsMap[state.currentContextMenuNamespace])
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
    auto& state = GetBrowserState(browser->GetIdentifier());

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
            state.contextMenuBindingsMap[state.currentContextMenuNamespace][command_id-CLIENT_ID_PYTONIUM_CUSTOM_FIRST].OnContextMenuEntryClicked();
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

    // Fire user callback if set
    auto& state = GetBrowserState(browser->GetIdentifier());
    if (state.onTitleChangeCallback) {
        std::string titleStr = title.ToString();
        state.onTitleChangeCallback(state.onTitleChangeUserData, titleStr.c_str());
    }
}

void CefWrapperClientHandler::OnAddressChange(CefRefPtr<CefBrowser> browser,
                                               CefRefPtr<CefFrame> frame,
                                               const CefString &url)
{
    CEF_REQUIRE_UI_THREAD();
    auto& state = GetBrowserState(browser->GetIdentifier());

    if (state.onAddressChangeCallback && frame->IsMain()) {
        std::string urlStr = url.ToString();
        state.onAddressChangeCallback(state.onAddressChangeUserData, urlStr.c_str());
    }
}

void CefWrapperClientHandler::OnFullscreenModeChange(CefRefPtr<CefBrowser> browser,
                                                      bool fullscreen)
{
    CEF_REQUIRE_UI_THREAD();
    auto& state = GetBrowserState(browser->GetIdentifier());

    if (state.onFullscreenChangeCallback) {
        state.onFullscreenChangeCallback(state.onFullscreenChangeUserData, fullscreen);
    }
}

void CefWrapperClientHandler::OnAfterCreated(CefRefPtr<CefBrowser> browser)
{
    CEF_REQUIRE_UI_THREAD();

    // Add to the list of existing browsers.
    browser_list_.push_back(browser);
    g_BrowserCount.fetch_add(1, std::memory_order_release);

    // Initialize per-browser state
    m_BrowserStates[browser->GetIdentifier()] = PerBrowserState{};

    // Subclass the window for resize border handling
    PlatformSubclassWindow(browser);
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

    // Remove window subclassing
    PlatformRemoveSubclass(browser);

    // Remove per-browser state
    m_BrowserStates.erase(browser->GetIdentifier());

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
    g_BrowserCount.fetch_sub(1, std::memory_order_release);
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

bool CefWrapperClientHandler::IsReadyToExecuteJs(int browserId)
{
    auto it = m_BrowserStates.find(browserId);
    if (it != m_BrowserStates.end()) {
        return it->second.isReadyToExecuteJs;
    }
    return false;
}

void CefWrapperClientHandler::OnLoadStart(
        CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
        CefLoadHandler::TransitionType transition_type)
{
    GetBrowserState(browser->GetIdentifier()).isReadyToExecuteJs = false;
}

bool CefWrapperClientHandler::OnProcessMessageReceived(
        CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
        CefProcessId source_process, CefRefPtr<CefProcessMessage> message)
{
    auto& state = GetBrowserState(browser->GetIdentifier());
    const std::string &message_name = message->GetName();

    if (message_name == "javascript-binding")
    {
        CefRefPtr<CefListValue> argList = message->GetArgumentList();
        std::string funcName = argList->GetString(0);
        CefRefPtr<CefListValue> javascript_arg_types = argList->GetList(1);
        CefRefPtr<CefListValue> javascript_args = argList->GetList(2);
        int argsSize = (int) javascript_args->GetSize();

        std::vector<CefValueWrapper> valueWrapper(argsSize);
        for (int i = 0; i < argsSize; ++i)
        {
            std::string type = javascript_arg_types->GetString(i);
            valueWrapper[i] = CefValueWrapperHelper::ConvertCefValueToWrapper(javascript_args->GetValue(i));
        }

        for (int i = 0; i < (int) state.javascriptBindings.size(); ++i)
        {
            if (state.javascriptBindings[i].functionName == funcName)
            {
                state.javascriptBindings[i].function(argsSize, valueWrapper.data());
            }
        }

        return true;
    } else if (message_name == "javascript-python-binding")
    {
        CefRefPtr<CefListValue> argList = message->GetArgumentList();
        std::string funcName = argList->GetString(0);
        CefRefPtr<CefListValue> javascript_arg_types = argList->GetList(1);
        CefRefPtr<CefListValue> javascript_args = argList->GetList(2);
        int argsSize = (int) javascript_args->GetSize();

        std::vector<CefValueWrapper> valueWrapper(argsSize);
        for (int i = 0; i < argsSize; ++i)
        {
            std::string type = javascript_arg_types->GetString(i);
            valueWrapper[i] = CefValueWrapperHelper::ConvertCefValueToWrapper(javascript_args->GetValue(i));
        }

        for (int i = 0; i < (int) state.javascriptPythonBindings.size(); ++i)
        {
            if (state.javascriptPythonBindings[i].FunctionName == funcName)
            {
                state.javascriptPythonBindings[i].CallHandler(argsSize, valueWrapper.data(), argList->GetInt(3));
                break;
            }
        }
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

            for (const auto &stateHandler: state.stateHandlerPythonBindings)
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
        state.currentContextMenuNamespace = argList->GetString(0);
    }
    return false;
}

void CefWrapperClientHandler::OnLoadingStateChange(
        CefRefPtr<CefBrowser> browser, bool isLoading, bool canGoBack,
        bool canGoForward)
{
    GetBrowserState(browser->GetIdentifier()).isReadyToExecuteJs = !isLoading;
}

void CefWrapperClientHandler::SetCurrentContextMenuName(int browserId, const std::string& context_menu_namespace)
{
    GetBrowserState(browserId).currentContextMenuNamespace = context_menu_namespace;
}

void CefWrapperClientHandler::SetShowDebugContextMenu(int browserId, bool show)
{
    GetBrowserState(browserId).showDebugContextMenu = show;
}

void CefWrapperClientHandler::SetContextMenuBindings(int browserId, std::vector<ContextMenuBinding> contextMenuBindings)
{
    auto& state = GetBrowserState(browserId);
    state.contextMenuBindings = std::move(contextMenuBindings);
    state.contextMenuBindingsMap.clear();
    for (const auto& contextMenuEntry: state.contextMenuBindings)
    {
        state.contextMenuBindingsMap[contextMenuEntry.Namespace].emplace_back(contextMenuEntry);
    }
}

void CefWrapperClientHandler::SetOnTitleChangeCallback(int browserId, window_event_string_callback_ptr callback, void* user_data)
{
    auto& state = GetBrowserState(browserId);
    state.onTitleChangeCallback = callback;
    state.onTitleChangeUserData = user_data;
}

void CefWrapperClientHandler::SetOnAddressChangeCallback(int browserId, window_event_string_callback_ptr callback, void* user_data)
{
    auto& state = GetBrowserState(browserId);
    state.onAddressChangeCallback = callback;
    state.onAddressChangeUserData = user_data;
}

void CefWrapperClientHandler::SetOnFullscreenChangeCallback(int browserId, window_event_bool_callback_ptr callback, void* user_data)
{
    auto& state = GetBrowserState(browserId);
    state.onFullscreenChangeCallback = callback;
    state.onFullscreenChangeUserData = user_data;
}
