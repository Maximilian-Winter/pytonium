#include "pytonium_library.h"

#include "global_vars.h"
#include "javascript_binding.h"
#include "cef_value_wrapper.h"
#include "include/internal/cef_types.h"
#include "custom_protocol_scheme_handler.h"
#include <cstring>
#include <filesystem>
#include <iostream>
#include <utility>
#include <vector>
#undef CEF_USE_SANDBOX

#if defined(OS_WIN)
#include <Windows.h>
#elif defined(OS_LINUX)
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>
#include "x11_helpers.h"
// cef_get_xdisplay() is provided by CEF on Linux
extern "C" { Display* cef_get_xdisplay(); }
#endif

// Static member definitions
bool PytoniumLibrary::s_CefInitialized = false;
int PytoniumLibrary::s_InstanceCount = 0;
CefRefPtr<CefWrapperApp> PytoniumLibrary::s_App = nullptr;

std::string ExePath() {
#if OS_WIN
  std::vector<std::filesystem::path> possiblePaths;

  possiblePaths.push_back(std::filesystem::current_path() / "bin" / "pytonium_subprocess.exe");
  possiblePaths.push_back(std::filesystem::current_path() / "pytonium_subprocess.exe");

  wchar_t exePathW[MAX_PATH];
  if (GetModuleFileNameW(NULL, exePathW, MAX_PATH) > 0) {
    std::filesystem::path exeDir = std::filesystem::path(exePathW).parent_path();
    possiblePaths.push_back(exeDir / "pytonium_subprocess.exe");
    possiblePaths.push_back(exeDir / "bin" / "pytonium_subprocess.exe");
    possiblePaths.push_back(exeDir.parent_path() / "pytonium_subprocess.exe");
    possiblePaths.push_back(exeDir.parent_path() / "bin" / "pytonium_subprocess.exe");
  }

  for (const auto& path : possiblePaths) {
    if (std::filesystem::exists(path)) {
      std::cout << "Found subprocess at: " << path.string() << std::endl;
      return path.string();
    }
  }

  std::cout << "Warning: subprocess not found, trying default path" << std::endl;
  return possiblePaths[0].string();
#else
  std::filesystem::path cwd = std::filesystem::current_path() / "pytonium_subprocess";
  return cwd.string();
#endif
}

std::string ResourcePath() {
  std::filesystem::path cwd = std::filesystem::current_path() /"bin" ;
  return cwd.string();
}

std::string LocalesPath() {
  std::filesystem::path cwd = std::filesystem::current_path() /"bin" / "locales";
  return cwd.string();
}

std::string CachePath() {
  std::filesystem::path cwd = std::filesystem::current_path() / "cache";
  return cwd.string();
}

PytoniumLibrary::PytoniumLibrary() = default;

void PytoniumLibrary::InitPytonium(std::string start_url, int init_width, int init_height) {
  if (!s_CefInitialized) {
#if defined(OS_WIN)
    // Enable per-monitor DPI awareness (graceful fallback on older Windows)
    {
      HMODULE hUser32 = LoadLibraryW(L"user32.dll");
      if (hUser32) {
        typedef BOOL (WINAPI *SetProcessDpiAwarenessContextFunc)(DPI_AWARENESS_CONTEXT);
        auto pSetDpiContext = reinterpret_cast<SetProcessDpiAwarenessContextFunc>(
            GetProcAddress(hUser32, "SetProcessDpiAwarenessContext"));
        if (pSetDpiContext) {
          pSetDpiContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
        }
        FreeLibrary(hUser32);
      }
    }
#endif

    void *sandbox_info = nullptr;

#if OS_LINUX
    std::string name = "pytonium_library";
    std::string arg1 = "--no-sandbox";

    int argc = 2;
    char* argv[2] { std::data(name), std::data(arg1)};
    CefMainArgs main_args(argc, argv);
    CefRefPtr<CefCommandLine> command_line = CefCommandLine::CreateCommandLine();
    command_line->InitFromArgv(argc, argv);
#else
    std::string name = "pytonium_library";
    CefMainArgs main_args;
    CefRefPtr<CefCommandLine> command_line = CefCommandLine::CreateCommandLine();
    command_line->InitFromString(std::data(name));
#endif

    command_line->AppendSwitch("disable-chrome-runtime");
    command_line->AppendSwitchWithValue("disable-features", "ChromeRuntime");

    command_line->AppendSwitch("disable-gpu-sandbox");
    command_line->AppendSwitch("disable-setuid-sandbox");
    command_line->AppendSwitch("disable-network-service-sandbox");
    command_line->AppendSwitch("no-sandbox");

    CefString cmdLineStr = command_line->GetCommandLineString();
    std::cout << "Command line: " << cmdLineStr.ToString() << std::endl;

    s_App = CefRefPtr<CefWrapperApp>(new CefWrapperApp(
        start_url, m_Javascript_Bindings, m_Javascript_Python_Bindings,
        m_StateHandlerPythonBindings, m_ContextMenuBindings, m_CustomSchemes, m_MimeTypeMap, m_FramelessWindow));
    CefWrapperBrowserProcessHandler::SetInitialResolution(init_width, init_height);
    CefExecuteProcess(main_args, s_App.get(), sandbox_info);

    cef_settings_t cefSettings;
    memset(&cefSettings, 0, sizeof(cef_settings_t));
    cefSettings.size = sizeof(cef_settings_t);
    CefSettings settings(cefSettings);

    if(m_UseCustomCefResourcesPath)
    {
      CefString(&settings.resources_dir_path) = m_CustomCefResourcesPath;
    }

    if(m_UseCustomCefLocalesPath)
    {
      CefString(&settings.locales_dir_path) = m_CustomCefLocalesPath;
    }

    if(m_UseCustomCefCachePath)
    {
      CefString(&settings.cache_path) = m_CustomCefCachePath;
      CefString(&settings.root_cache_path) = m_CustomCefCachePath;
    }
    else
    {
      CefString(&settings.cache_path) = CachePath();
      CefString(&settings.root_cache_path) = CachePath();
    }

    settings.no_sandbox = true;
    settings.windowless_rendering_enabled = true;

    if(m_UseCustomCefSubPath)
    {
      CefString(&settings.browser_subprocess_path).FromASCII(m_CustomCefSubPath.c_str());
    }
    else
    {
      CefString(&settings.browser_subprocess_path).FromASCII(ExePath().c_str());
    }

    if (!CefInitialize(main_args, settings, s_App.get(), sandbox_info)) {
      std::cerr << "CefInitialize failed!" << std::endl;
      return;
    }
    s_CefInitialized = true;
    g_CefInitialized = true;
  }

  // Create the browser window (works for first and subsequent instances)
  CreateBrowser(start_url, init_width, init_height, m_FramelessWindow,
                m_UseCustomIcon ? m_CustomIconPath : "");
}

int PytoniumLibrary::CreateBrowser(const std::string& url, int width, int height,
                                    bool frameless, const std::string& iconPath)
{
    if (m_OsrMode) {
        return CreateBrowserOsr(url, width, height, iconPath, false);
    }

    // Get or create the shared client handler
    CefWrapperClientHandler* handler = CefWrapperClientHandler::GetInstance();
    if (!handler) {
        CefRefPtr<CefCommandLine> command_line = CefCommandLine::GetGlobalCommandLine();
        bool use_views = command_line->HasSwitch("use-views");
        new CefWrapperClientHandler(use_views);
        handler = CefWrapperClientHandler::GetInstance();
    }

    // Initialize browser settings
    cef_browser_settings_t cefBrowserSettings;
    memset(&cefBrowserSettings, 0, sizeof(cef_browser_settings_t));
    cefBrowserSettings.size = sizeof(cef_browser_settings_t);
    cefBrowserSettings.windowless_frame_rate = 30;
    CefBrowserSettings browser_settings(cefBrowserSettings);

    CefWindowInfo window_info;

#if defined(OS_WIN)
    window_info.runtime_style = CEF_RUNTIME_STYLE_ALLOY;

    if (m_ParentHwnd != nullptr) {
        // Child window mode (wallpaper embedding, etc.)
        // Created as WS_CHILD of the given parent — no post-creation reparenting needed.
        window_info.parent_window = reinterpret_cast<CefWindowHandle>(m_ParentHwnd);
        window_info.style = WS_CHILD | WS_VISIBLE | WS_CLIPCHILDREN | WS_CLIPSIBLINGS;
        window_info.bounds.x = 0;
        window_info.bounds.y = 0;
    } else if (frameless) {
        window_info.style = WS_POPUP | WS_VISIBLE | WS_CLIPCHILDREN | WS_CLIPSIBLINGS;
        window_info.parent_window = nullptr;
        window_info.bounds.x = CW_USEDEFAULT;
        window_info.bounds.y = CW_USEDEFAULT;
    } else {
        window_info.SetAsPopup(nullptr, "");
    }
#elif defined(OS_LINUX)
    if (frameless) {
        window_info.SetAsWindowless(kNullWindowHandle);
    }
#endif

    // Serialize bindings into extra_info for the renderer
    CefRefPtr<CefDictionaryValue> extra = CefDictionaryValue::Create();
    if (!m_Javascript_Bindings.empty())
    {
        CefRefPtr<CefListValue> bindings = CefListValue::Create();
        bindings->SetSize(m_Javascript_Bindings.size());
        int listIndex = 0;
        for (const auto &binding: m_Javascript_Bindings)
        {
            CefRefPtr<CefDictionaryValue> dic = CefDictionaryValue::Create();
            dic->SetString("MessageTopic", binding.functionName);
            dic->SetString("JavascriptObject", binding.JavascriptObject);
            CefRefPtr<CefBinaryValue> functionPointer = CefBinaryValue::Create(
                    &binding.function, sizeof(binding.function));
            dic->SetBinary("FunctionPointer", functionPointer);
            bindings->SetDictionary(listIndex, dic);
            listIndex++;
        }
        extra->SetList("JavascriptBindings", bindings);
        extra->SetInt("JavascriptBindingsSize",
                      static_cast<int>(m_Javascript_Bindings.size()));
    }

    if (!m_Javascript_Python_Bindings.empty())
    {
        CefRefPtr<CefListValue> bindings = CefListValue::Create();
        bindings->SetSize(m_Javascript_Python_Bindings.size());
        int listIndex = 0;
        for (const auto &binding: m_Javascript_Python_Bindings)
        {
            CefRefPtr<CefDictionaryValue> dic = CefDictionaryValue::Create();
            dic->SetString("MessageTopic", binding.FunctionName);
            dic->SetString("JavascriptObject", binding.JavascriptObject);
            dic->SetBool("ReturnsValue", binding.ReturnsValue);
            CefRefPtr<CefBinaryValue> handlerFunc = CefBinaryValue::Create(
                    &binding.HandlerFunction, sizeof(binding.HandlerFunction));
            CefRefPtr<CefBinaryValue> pythonObject = CefBinaryValue::Create(
                    &binding.PythonCallbackObject, sizeof(binding.PythonCallbackObject));
            dic->SetBinary("HandlerFunction", handlerFunc);
            dic->SetBinary("PythonFunctionObject", pythonObject);
            bindings->SetDictionary(listIndex, dic);
            listIndex++;
        }
        extra->SetList("JavascriptPythonBindings", bindings);
        extra->SetInt("JavascriptPythonBindingsSize",
                      static_cast<int>(m_Javascript_Python_Bindings.size()));
    }

    window_info.bounds.width = width;
    window_info.bounds.height = height;

    m_Browser = CefBrowserHost::CreateBrowserSync(window_info, handler, url,
                                                   browser_settings, extra, nullptr);
    if (!m_Browser) {
        std::cerr << "CreateBrowserSync failed!" << std::endl;
        return -1;
    }

    m_BrowserId = m_Browser->GetIdentifier();
    s_InstanceCount++;

    // Register per-browser bindings on the client handler
    handler->RegisterBrowserBindings(m_BrowserId,
        m_Javascript_Bindings, m_Javascript_Python_Bindings,
        m_StateHandlerPythonBindings, m_ContextMenuBindings);

    // Set icon if specified
    if (!iconPath.empty())
    {
#if defined(OS_WIN)
        std::filesystem::path iconFsPath(iconPath);
        LPCWSTR w_icon_path = iconFsPath.c_str();
        HWND hwnd = GetActiveHwnd();
        if (hwnd)
        {
            HICON hIcon = (HICON)LoadImageW(NULL, w_icon_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE);
            SendMessage(hwnd, WM_SETICON, ICON_BIG, (LPARAM)hIcon);
        }
#endif
    }

    return m_BrowserId;
}

void PytoniumLibrary::CloseBrowser()
{
    if (m_Browser) {
        m_Browser->GetHost()->CloseBrowser(true);
        m_Browser = nullptr;
        m_BrowserId = -1;
        s_InstanceCount--;
    }
}

bool PytoniumLibrary::IsBrowserRunning() const
{
    return m_Browser != nullptr && m_BrowserId >= 0 &&
           g_BrowserCount.load(std::memory_order_acquire) > 0;
}

void PytoniumLibrary::ShutdownCef()
{
    g_CefInitialized = false;
    s_CefInitialized = false;
    s_App = nullptr;
    CefShutdown();
}

void PytoniumLibrary::ExecuteJavascript(const std::string& code) {
  if (!m_Browser) return;
  CefRefPtr<CefFrame> frame = m_Browser->GetMainFrame();
  if (g_BrowserCount.load(std::memory_order_acquire) > 0) {
    auto* client = CefWrapperClientHandler::GetInstance();
    if (client && client->IsReadyToExecuteJs(m_BrowserId)) {
      frame->ExecuteJavaScript(code, frame->GetURL(), 0);
    }
  }
}

void PytoniumLibrary::ShutdownPytonium() {
  CloseBrowser();
  if (s_InstanceCount <= 0 && s_CefInitialized) {
    ShutdownCef();
  }
}

bool PytoniumLibrary::IsRunning() { return g_BrowserCount.load(std::memory_order_acquire) > 0; }

void PytoniumLibrary::UpdateMessageLoop() {
    CefDoMessageLoopWork();
#if defined(OS_LINUX)
    // Pump X11 events for OSR windows (input forwarding, expose, resize)
    if (m_OsrMode && m_OsrWindow) {
        m_OsrWindow->ProcessEvents();
    }
#endif
}

bool PytoniumLibrary::IsReadyToExecuteJavascript() {
  auto* client = CefWrapperClientHandler::GetInstance();
  if (!client || !m_Browser) return false;
  return client->IsReadyToExecuteJs(m_BrowserId);
}

void PytoniumLibrary::AddJavascriptBinding(std::string name, js_binding_function_ptr jsNativeApiFunctionPtr, std::string javascript_object)
{
  m_Javascript_Bindings.emplace_back(std::move(name), jsNativeApiFunctionPtr, std::move(javascript_object));
}

void PytoniumLibrary::AddJavascriptPythonBinding(
    const std::string& name,
    js_python_bindings_handler_function_ptr python_bindings_handler ,
    js_python_callback_object_ptr python_callback_object, const std::string& javascript_object, bool returns_value) {
  m_Javascript_Python_Bindings.emplace_back(python_bindings_handler, name, python_callback_object, javascript_object, returns_value);
}

void PytoniumLibrary::SetCustomSubprocessPath(std::string cefsub_path) {
  m_UseCustomCefSubPath = true;
  m_CustomCefSubPath = std::move(cefsub_path);
}

void PytoniumLibrary::SetCustomCachePath(std::string cef_cache_path) {
  m_UseCustomCefCachePath = true;
  m_CustomCefCachePath = std::move(cef_cache_path);
}

void PytoniumLibrary::LoadUrl(std::string url) {
  if (m_Browser && m_Browser->GetMainFrame()) {
    m_Browser->GetMainFrame()->LoadURL(url);
  }
}

void PytoniumLibrary::SetCustomResourcePath(std::string cef_resources_path) {
  m_UseCustomCefResourcesPath = true;
  m_CustomCefResourcesPath = cef_resources_path;
}

void PytoniumLibrary::SetCustomLocalesPath(std::string cef_locales_path) {
  m_UseCustomCefLocalesPath = true;
  m_CustomCefLocalesPath = cef_locales_path;
}

void PytoniumLibrary::SetCustomIconPath(std::string icon_path) {
  m_CustomIconPath = icon_path;
  m_UseCustomIcon = true;
}

void PytoniumLibrary::ReturnValueToJavascript(int message_id, CefValueWrapper returnValue)
{
    if (!m_Browser) return;

    CefRefPtr<CefProcessMessage> return_to_javascript_message =
            CefProcessMessage::Create("return-to-javascript");

    CefRefPtr<CefListValue> return_value_message_args =
            return_to_javascript_message->GetArgumentList();

    return_value_message_args->SetInt(0, message_id);
    return_value_message_args->SetValue(1, CefValueWrapperHelper::ConvertWrapperToCefValue(returnValue));

    m_Browser->GetMainFrame()->SendProcessMessage(PID_RENDERER, return_to_javascript_message);
}

void PytoniumLibrary::AddStateHandlerPythonBinding(state_handler_function_ptr stateHandlerFunctionPtr,
                                                   state_callback_object_ptr stateCallbackObjectPtr, const std::vector<std::string>& namespacesToSubscribeTo)
{
    m_StateHandlerPythonBindings.emplace_back(stateHandlerFunctionPtr, stateCallbackObjectPtr, namespacesToSubscribeTo);
}

void PytoniumLibrary::SetState(const std::string& stateNamespace, const std::string& key, CefValueWrapper value)
{
    if(!m_Browser || g_BrowserCount.load(std::memory_order_acquire) <= 0) return;

    CefRefPtr<CefProcessMessage> msg = CefProcessMessage::Create("set-app-state");
    CefRefPtr<CefListValue> args = msg->GetArgumentList();
    args->SetString(0, stateNamespace);
    args->SetString(1, key);
    args->SetValue(2, CefValueWrapperHelper::ConvertWrapperToCefValue(value));
    m_Browser->GetMainFrame()->SendProcessMessage(PID_RENDERER, msg);
}

void PytoniumLibrary::RemoveState(const std::string& stateNamespace, const std::string& key)
{
    if(!m_Browser || g_BrowserCount.load(std::memory_order_acquire) <= 0) return;

    CefRefPtr<CefProcessMessage> msg = CefProcessMessage::Create("remove-app-state");
    CefRefPtr<CefListValue> args = msg->GetArgumentList();
    args->SetString(0, stateNamespace);
    args->SetString(1, key);
    m_Browser->GetMainFrame()->SendProcessMessage(PID_RENDERER, msg);
}

void PytoniumLibrary::AddContextMenuEntry(context_menu_handler_function_ptr context_menuHandlerFunctionPtr,
                                          context_menu_handler_object_ptr context_menuCallbackObjectPtr,
                                          const std::string& contextMenuNameSpace, const std::string& contextMenuDisplayName,
                                          int contextMenuId)
{
    m_ContextMenuBindings.emplace_back(contextMenuDisplayName, contextMenuId, context_menuHandlerFunctionPtr, context_menuCallbackObjectPtr, contextMenuNameSpace);
}

void PytoniumLibrary::AddContextMenuSeparator(const std::string& contextMenuNameSpace)
{
    m_ContextMenuBindings.push_back(ContextMenuBinding::MakeSeparator(contextMenuNameSpace, static_cast<int>(m_ContextMenuBindings.size())));
}

void PytoniumLibrary::AddContextMenuCheckItem(context_menu_handler_function_ptr cb, context_menu_handler_object_ptr obj,
                                               const std::string& ns, const std::string& displayName, int id, bool checked)
{
    m_ContextMenuBindings.emplace_back(displayName, id, cb, obj, ns,
                                        ContextMenuItemType::CHECK, 0, checked);
}

void PytoniumLibrary::AddContextMenuRadioItem(context_menu_handler_function_ptr cb, context_menu_handler_object_ptr obj,
                                               const std::string& ns, const std::string& displayName, int id, int groupId)
{
    m_ContextMenuBindings.emplace_back(displayName, id, cb, obj, ns,
                                        ContextMenuItemType::RADIO, groupId);
}

void PytoniumLibrary::AddContextMenuSubMenu(const std::string& ns, const std::string& displayName, int id,
                                             const std::string& subNamespace)
{
    m_ContextMenuBindings.push_back(ContextMenuBinding::MakeSubMenu(displayName, ns, id, subNamespace));
}

void PytoniumLibrary::SetContextMenuItemEnabled(const std::string& ns, int index, bool enabled)
{
    auto* client = CefWrapperClientHandler::GetInstance();
    if (client && m_BrowserId >= 0) {
        client->SetContextMenuItemEnabled(m_BrowserId, ns, index, enabled);
    }
}

void PytoniumLibrary::SetContextMenuItemChecked(const std::string& ns, int index, bool checked)
{
    auto* client = CefWrapperClientHandler::GetInstance();
    if (client && m_BrowserId >= 0) {
        client->SetContextMenuItemChecked(m_BrowserId, ns, index, checked);
    }
}

void PytoniumLibrary::SetContextMenuItemVisible(const std::string& ns, int index, bool visible)
{
    auto* client = CefWrapperClientHandler::GetInstance();
    if (client && m_BrowserId >= 0) {
        client->SetContextMenuItemVisible(m_BrowserId, ns, index, visible);
    }
}

void PytoniumLibrary::SetContextMenuItemAccelerator(const std::string& ns, int index,
                                                     int keyCode, bool shift, bool ctrl, bool alt)
{
    auto* client = CefWrapperClientHandler::GetInstance();
    if (client && m_BrowserId >= 0) {
        client->SetContextMenuItemAccelerator(m_BrowserId, ns, index, keyCode, shift, ctrl, alt);
    }
}

void PytoniumLibrary::ClearContextMenuEntries(const std::string& ns)
{
    auto* client = CefWrapperClientHandler::GetInstance();
    if (client && m_BrowserId >= 0) {
        client->ClearContextMenuEntries(m_BrowserId, ns);
    }
}

void PytoniumLibrary::SetOnBeforeContextMenuCallback(before_context_menu_callback_ptr callback, void* user_data)
{
    auto* client = CefWrapperClientHandler::GetInstance();
    if (client && m_BrowserId >= 0) {
        client->SetOnBeforeContextMenuCallback(m_BrowserId, callback, user_data);
    }
}

void PytoniumLibrary::SetCurrentContextMenuNamespace(const std::string& contextMenuNamespace)
{
    auto* client = CefWrapperClientHandler::GetInstance();
    if (client && m_BrowserId >= 0) {
        client->SetCurrentContextMenuName(m_BrowserId, contextMenuNamespace);
    }
}

void PytoniumLibrary::SetShowDebugContextMenu(bool show)
{
    auto* client = CefWrapperClientHandler::GetInstance();
    if (client && m_BrowserId >= 0) {
        client->SetShowDebugContextMenu(m_BrowserId, show);
    }
}

void PytoniumLibrary::AddCustomScheme(std::string schemeIdentifier, std::string contentRootFolder)
{
    m_CustomSchemes.emplace_back(schemeIdentifier, contentRootFolder);
}

void PytoniumLibrary::AddMimeTypeMapping(const std::string& fileExtension, std::string mimeType)
{
    m_MimeTypeMap[fileExtension] = std::move(mimeType);
}

void PytoniumLibrary::SetFramelessWindow(bool frameless)
{
    m_FramelessWindow = frameless;
}

void PytoniumLibrary::SetParentWindow(void* parentHwnd)
{
    m_ParentHwnd = parentHwnd;
}

void PytoniumLibrary::MinimizeWindow()
{
#if defined(OS_WIN)
    if (!m_Browser) return;
    HWND hwnd = GetActiveHwnd();
    if (hwnd && IsWindow(hwnd)) {
        ShowWindow(hwnd, SW_MINIMIZE);
    }
#elif defined(OS_LINUX)
    if (!m_Browser) return;
    Display* display = GetX11Display();
    ::Window window = GetActiveX11Window();
    if (!display || window == None) return;
    XIconifyWindow(display, window, DefaultScreen(display));
    XFlush(display);
#endif
}

void PytoniumLibrary::MaximizeWindow()
{
#if defined(OS_WIN)
    if (!m_Browser) return;
    m_Browser->GetHost()->SetFocus(true);
    HWND hwnd = GetActiveHwnd();
    if (hwnd && IsWindow(hwnd)) {
        ShowWindow(hwnd, SW_MAXIMIZE);
    }
#elif defined(OS_LINUX)
    if (!m_Browser) return;
    Display* display = GetX11Display();
    ::Window window = GetActiveX11Window();
    if (!display || window == None) return;
    Atom maxH = XInternAtom(display, "_NET_WM_STATE_MAXIMIZED_HORZ", False);
    Atom maxV = XInternAtom(display, "_NET_WM_STATE_MAXIMIZED_VERT", False);
    x11_helpers::SendNetWmStateEvent(display, window, 1, maxH, maxV);  // 1 = add
#endif
}

void PytoniumLibrary::RestoreWindow()
{
#if defined(OS_WIN)
    if (!m_Browser) return;
    HWND hwnd = GetActiveHwnd();
    if (hwnd && IsWindow(hwnd)) {
        ShowWindow(hwnd, SW_RESTORE);
    }
#elif defined(OS_LINUX)
    if (!m_Browser) return;
    Display* display = GetX11Display();
    ::Window window = GetActiveX11Window();
    if (!display || window == None) return;
    // Remove maximized state
    Atom maxH = XInternAtom(display, "_NET_WM_STATE_MAXIMIZED_HORZ", False);
    Atom maxV = XInternAtom(display, "_NET_WM_STATE_MAXIMIZED_VERT", False);
    x11_helpers::SendNetWmStateEvent(display, window, 0, maxH, maxV);  // 0 = remove
    // Remove fullscreen state if set
    Atom fullscreen = XInternAtom(display, "_NET_WM_STATE_FULLSCREEN", False);
    x11_helpers::SendNetWmStateEvent(display, window, 0, fullscreen);
    // Ensure window is mapped (un-iconify)
    XMapWindow(display, window);
    XFlush(display);
#endif
}

void PytoniumLibrary::CloseWindow()
{
    if (m_Browser) {
        m_Browser->GetHost()->CloseBrowser(false);
    }
}

bool PytoniumLibrary::IsMaximized()
{
#if defined(OS_WIN)
    if (!m_Browser) return false;
    HWND hwnd = GetActiveHwnd();
    if (hwnd && IsWindow(hwnd)) {
        WINDOWPLACEMENT wp;
        wp.length = sizeof(WINDOWPLACEMENT);
        if (GetWindowPlacement(hwnd, &wp)) {
            return wp.showCmd == SW_SHOWMAXIMIZED;
        }
    }
#elif defined(OS_LINUX)
    if (!m_Browser) return false;
    Display* display = GetX11Display();
    ::Window window = GetActiveX11Window();
    if (!display || window == None) return false;
    Atom maxH = XInternAtom(display, "_NET_WM_STATE_MAXIMIZED_HORZ", False);
    Atom maxV = XInternAtom(display, "_NET_WM_STATE_MAXIMIZED_VERT", False);
    return x11_helpers::HasNetWmState(display, window, maxH) &&
           x11_helpers::HasNetWmState(display, window, maxV);
#endif
    return false;
}

void PytoniumLibrary::SetFullscreen(bool fullscreen)
{
#if defined(OS_WIN)
    if (!m_Browser) return;
    HWND hwnd = GetActiveHwnd();
    if (!hwnd || !IsWindow(hwnd)) return;

    if (fullscreen == m_IsFullscreen) return;

    if (fullscreen) {
        // Save current window state before going fullscreen
        GetWindowRect(hwnd, &m_FullscreenState.savedRect);
        m_FullscreenState.savedStyle = static_cast<LONG>(GetWindowLongPtrW(hwnd, GWL_STYLE));
        m_FullscreenState.savedExStyle = static_cast<LONG>(GetWindowLongPtrW(hwnd, GWL_EXSTYLE));

        // Strip window chrome
        LONG newStyle = m_FullscreenState.savedStyle;
        newStyle &= ~(WS_CAPTION | WS_THICKFRAME);
        LONG newExStyle = m_FullscreenState.savedExStyle;
        newExStyle &= ~(WS_EX_DLGMODALFRAME | WS_EX_WINDOWEDGE |
                        WS_EX_CLIENTEDGE | WS_EX_STATICEDGE);

        SetWindowLongPtrW(hwnd, GWL_STYLE, newStyle);
        SetWindowLongPtrW(hwnd, GWL_EXSTYLE, newExStyle);

        // Get the monitor this window is on
        HMONITOR hMonitor = MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST);
        MONITORINFO mi;
        mi.cbSize = sizeof(MONITORINFO);
        if (GetMonitorInfoW(hMonitor, &mi)) {
            SetWindowPos(hwnd, HWND_TOP,
                         mi.rcMonitor.left, mi.rcMonitor.top,
                         mi.rcMonitor.right - mi.rcMonitor.left,
                         mi.rcMonitor.bottom - mi.rcMonitor.top,
                         SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED);
        }
    } else {
        // Restore saved window state
        SetWindowLongPtrW(hwnd, GWL_STYLE, m_FullscreenState.savedStyle);
        SetWindowLongPtrW(hwnd, GWL_EXSTYLE, m_FullscreenState.savedExStyle);

        SetWindowPos(hwnd, NULL,
                     m_FullscreenState.savedRect.left,
                     m_FullscreenState.savedRect.top,
                     m_FullscreenState.savedRect.right - m_FullscreenState.savedRect.left,
                     m_FullscreenState.savedRect.bottom - m_FullscreenState.savedRect.top,
                     SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED);
    }

    m_IsFullscreen = fullscreen;
#elif defined(OS_LINUX)
    if (!m_Browser) return;
    Display* display = GetX11Display();
    ::Window window = GetActiveX11Window();
    if (!display || window == None) return;

    if (fullscreen == m_IsFullscreen) return;

    if (fullscreen) {
        // Save current geometry before going fullscreen
        x11_helpers::GetRootRelativePosition(display, window,
            m_FullscreenState.savedX, m_FullscreenState.savedY);
        XWindowAttributes attrs;
        if (XGetWindowAttributes(display, window, &attrs)) {
            m_FullscreenState.savedWidth = attrs.width;
            m_FullscreenState.savedHeight = attrs.height;
        }
    }

    Atom fullscreenAtom = XInternAtom(display, "_NET_WM_STATE_FULLSCREEN", False);
    // 1=add, 0=remove
    x11_helpers::SendNetWmStateEvent(display, window, fullscreen ? 1 : 0, fullscreenAtom);

    if (!fullscreen) {
        // Restore saved geometry
        XMoveResizeWindow(display, window,
            m_FullscreenState.savedX, m_FullscreenState.savedY,
            m_FullscreenState.savedWidth, m_FullscreenState.savedHeight);
        XFlush(display);
    }

    m_IsFullscreen = fullscreen;
#endif
}

bool PytoniumLibrary::IsFullscreen()
{
    return m_IsFullscreen;
}

void PytoniumLibrary::ToggleFullscreen()
{
    SetFullscreen(!m_IsFullscreen);
}

#if defined(OS_WIN)
HWND PytoniumLibrary::GetActiveHwnd()
{
    if (m_OsrMode && m_OsrWindow) {
        return m_OsrWindow->GetHwnd();
    }
    if (m_Browser && m_Browser->GetHost()) {
        return m_Browser->GetHost()->GetWindowHandle();
    }
    return nullptr;
}
#elif defined(OS_LINUX)
::Display* PytoniumLibrary::GetX11Display()
{
    return cef_get_xdisplay();
}

::Window PytoniumLibrary::GetActiveX11Window()
{
    if (m_OsrMode && m_OsrWindow) {
        return m_OsrWindow->GetWindow();
    }
    if (m_Browser && m_Browser->GetHost()) {
        // CEF returns the X11 Window handle on Linux
        return static_cast<::Window>(m_Browser->GetHost()->GetWindowHandle());
    }
    return None;
}
#endif

void PytoniumLibrary::DragWindow(int deltaX, int deltaY)
{
#if defined(OS_WIN)
    if (!m_Browser) return;
    HWND hwnd = GetActiveHwnd();
    if (hwnd && IsWindow(hwnd)) {
        RECT rect;
        if (GetWindowRect(hwnd, &rect)) {
            int newX = rect.left + deltaX;
            int newY = rect.top + deltaY;
            SetWindowPos(hwnd, NULL, newX, newY, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
        }
    }
#elif defined(OS_LINUX)
    if (!m_Browser) return;
    Display* display = GetX11Display();
    ::Window window = GetActiveX11Window();
    if (!display || window == None) return;
    int x = 0, y = 0;
    x11_helpers::GetRootRelativePosition(display, window, x, y);
    XMoveWindow(display, window, x + deltaX, y + deltaY);
    XFlush(display);
#endif
}

void PytoniumLibrary::StartWindowDrag()
{
#if defined(OS_WIN)
    HWND hwnd = GetActiveHwnd();
    if (hwnd && IsWindow(hwnd)) {
        // Release any existing mouse capture (CEF sets capture on LBUTTONDOWN)
        ReleaseCapture();
        // Tell Windows to start a native title-bar drag from the current cursor position.
        // This enters a modal move loop handled entirely by the OS — zero latency.
        SendMessage(hwnd, WM_NCLBUTTONDOWN, HTCAPTION, 0);
    }
#elif defined(OS_LINUX)
    Display* display = GetX11Display();
    ::Window window = GetActiveX11Window();
    if (!display || window == None) return;

    // Get current pointer position (root coordinates) for _NET_WM_MOVERESIZE
    ::Window root_return, child_return;
    int root_x, root_y, win_x, win_y;
    unsigned int mask;
    XQueryPointer(display, window, &root_return, &child_return,
                  &root_x, &root_y, &win_x, &win_y, &mask);

    // direction=8 means _NET_WM_MOVERESIZE_MOVE
    x11_helpers::SendNetWmMoveResize(display, window, root_x, root_y, 8);
#endif
}

void PytoniumLibrary::CenterWindow()
{
#if defined(OS_WIN)
    HWND hwnd = GetActiveHwnd();
    if (!hwnd || !IsWindow(hwnd)) return;

    // Get the window's current size
    RECT windowRect;
    if (!GetWindowRect(hwnd, &windowRect)) return;
    int winWidth = windowRect.right - windowRect.left;
    int winHeight = windowRect.bottom - windowRect.top;

    // Get the work area of the monitor the window is currently on
    HMONITOR monitor = MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST);
    MONITORINFO mi = {};
    mi.cbSize = sizeof(MONITORINFO);
    if (!GetMonitorInfo(monitor, &mi)) return;

    int monX = mi.rcWork.left;
    int monY = mi.rcWork.top;
    int monWidth = mi.rcWork.right - mi.rcWork.left;
    int monHeight = mi.rcWork.bottom - mi.rcWork.top;

    int x = monX + (monWidth - winWidth) / 2;
    int y = monY + (monHeight - winHeight) / 2;

    SetWindowPos(hwnd, nullptr, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
#elif defined(OS_LINUX)
    Display* display = GetX11Display();
    ::Window window = GetActiveX11Window();
    if (!display || window == None) return;

    // Get window size
    XWindowAttributes attrs;
    if (!XGetWindowAttributes(display, window, &attrs)) return;
    int winWidth = attrs.width;
    int winHeight = attrs.height;

    // Get work area
    int waX, waY, waWidth, waHeight;
    if (!x11_helpers::GetWorkArea(display, waX, waY, waWidth, waHeight)) return;

    int x = waX + (waWidth - winWidth) / 2;
    int y = waY + (waHeight - winHeight) / 2;

    XMoveWindow(display, window, x, y);
    XFlush(display);
#endif
}

void PytoniumLibrary::GetWindowPosition(int& x, int& y)
{
    x = 0;
    y = 0;
#if defined(OS_WIN)
    if (!m_Browser) return;
    HWND hwnd = GetActiveHwnd();
    if (hwnd && IsWindow(hwnd)) {
        RECT rect;
        if (GetWindowRect(hwnd, &rect)) {
            x = rect.left;
            y = rect.top;
        }
    }
#elif defined(OS_LINUX)
    if (!m_Browser) return;
    Display* display = GetX11Display();
    ::Window window = GetActiveX11Window();
    if (!display || window == None) return;
    x11_helpers::GetRootRelativePosition(display, window, x, y);
#endif
}

void PytoniumLibrary::SetWindowPosition(int x, int y)
{
#if defined(OS_WIN)
    if (!m_Browser) return;
    HWND hwnd = GetActiveHwnd();
    if (hwnd && IsWindow(hwnd)) {
        SetWindowPos(hwnd, NULL, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
    }
#elif defined(OS_LINUX)
    if (!m_Browser) return;
    Display* display = GetX11Display();
    ::Window window = GetActiveX11Window();
    if (!display || window == None) return;
    XMoveWindow(display, window, x, y);
    XFlush(display);
#endif
}

void PytoniumLibrary::GetWindowSize(int& width, int& height)
{
    width = 0;
    height = 0;

#if defined(OS_WIN)
    if (!m_Browser) return;

    HWND hwnd = GetActiveHwnd();
    if (!hwnd || !IsWindow(hwnd)) return;

    RECT rect;
    if (GetWindowRect(hwnd, &rect)) {
        width = rect.right - rect.left;
        height = rect.bottom - rect.top;
    }
#elif defined(OS_LINUX)
    if (!m_Browser) return;
    Display* display = GetX11Display();
    ::Window window = GetActiveX11Window();
    if (!display || window == None) return;
    XWindowAttributes attrs;
    if (XGetWindowAttributes(display, window, &attrs)) {
        width = attrs.width;
        height = attrs.height;
    }
#endif
}

void PytoniumLibrary::SetWindowSize(int width, int height)
{
#if defined(OS_WIN)
    if (!m_Browser) return;

    HWND hwnd = GetActiveHwnd();
    if (!hwnd || !IsWindow(hwnd)) return;
    if (IsZoomed(hwnd)) return;

    SetWindowPos(hwnd, NULL, 0, 0, width, height,
                 SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED);
#elif defined(OS_LINUX)
    if (!m_Browser) return;
    if (IsMaximized()) return;  // Don't resize while maximized
    Display* display = GetX11Display();
    ::Window window = GetActiveX11Window();
    if (!display || window == None) return;
    XResizeWindow(display, window, width, height);
    XFlush(display);
#endif
}

void PytoniumLibrary::SetOnTitleChangeCallback(void (*callback)(void*, const char*), void* user_data)
{
    auto* client = CefWrapperClientHandler::GetInstance();
    if (client && m_BrowserId >= 0) {
        client->SetOnTitleChangeCallback(m_BrowserId, callback, user_data);
    }
}

void PytoniumLibrary::SetOnAddressChangeCallback(void (*callback)(void*, const char*), void* user_data)
{
    auto* client = CefWrapperClientHandler::GetInstance();
    if (client && m_BrowserId >= 0) {
        client->SetOnAddressChangeCallback(m_BrowserId, callback, user_data);
    }
}

void PytoniumLibrary::SetOnFullscreenChangeCallback(void (*callback)(void*, bool), void* user_data)
{
    auto* client = CefWrapperClientHandler::GetInstance();
    if (client && m_BrowserId >= 0) {
        client->SetOnFullscreenChangeCallback(m_BrowserId, callback, user_data);
    }
}

void* PytoniumLibrary::GetNativeWindowHandle()
{
#if defined(OS_WIN)
    return reinterpret_cast<void*>(GetActiveHwnd());
#else
    if (!m_Browser || !m_Browser->GetHost()) {
        return nullptr;
    }
    return reinterpret_cast<void*>(m_Browser->GetHost()->GetWindowHandle());
#endif
}

void PytoniumLibrary::ResizeWindow(int newWidth, int newHeight, int anchor)
{
#if defined(OS_WIN)
    if (!m_Browser) return;

    HWND hwnd = GetActiveHwnd();
    if (!hwnd || !IsWindow(hwnd)) return;
    if (IsZoomed(hwnd)) return;

    RECT rect;
    if (!GetWindowRect(hwnd, &rect)) return;

    int currX = rect.left;
    int currY = rect.top;
    int currWidth = rect.right - rect.left;
    int currHeight = rect.bottom - rect.top;

    int newX = currX;
    int newY = currY;

    if (anchor == 1 || anchor == 3) {
        newX = currX + (currWidth - newWidth);
    }
    if (anchor == 2 || anchor == 3) {
        newY = currY + (currHeight - newHeight);
    }

    SetWindowPos(hwnd, NULL, newX, newY, newWidth, newHeight,
                 SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED);
#elif defined(OS_LINUX)
    if (!m_Browser) return;
    if (IsMaximized()) return;
    Display* display = GetX11Display();
    ::Window window = GetActiveX11Window();
    if (!display || window == None) return;

    // Get current position and size
    int currX = 0, currY = 0;
    x11_helpers::GetRootRelativePosition(display, window, currX, currY);
    XWindowAttributes attrs;
    if (!XGetWindowAttributes(display, window, &attrs)) return;
    int currWidth = attrs.width;
    int currHeight = attrs.height;

    int newX = currX;
    int newY = currY;

    // anchor: 0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right
    if (anchor == 1 || anchor == 3) {
        newX = currX + (currWidth - newWidth);
    }
    if (anchor == 2 || anchor == 3) {
        newY = currY + (currHeight - newHeight);
    }

    XMoveResizeWindow(display, window, newX, newY, newWidth, newHeight);
    XFlush(display);
#endif
}

void PytoniumLibrary::SetOsrMode(bool osr) {
    m_OsrMode = osr;
}

void PytoniumLibrary::SetHeadlessMode(bool headless) {
    m_HeadlessMode = headless;
    if (headless) {
        m_OsrMode = true;  // headless implies OSR
    }
}

void PytoniumLibrary::SetOnPaintCallback(headless_paint_callback_ptr callback, void* user_data) {
    if (m_OsrWindowHeadless) {
        m_OsrWindowHeadless->SetPaintCallback(callback, user_data);
    }
}

void PytoniumLibrary::SetHeadlessSize(int width, int height) {
    if (m_OsrWindowHeadless) {
        m_OsrWindowHeadless->SetSize(width, height);
    }
}

const void* PytoniumLibrary::GetPaintBuffer(int& width, int& height) {
    if (!m_OsrWindowHeadless || !m_OsrWindowHeadless->HasFrame()) {
        width = 0;
        height = 0;
        return nullptr;
    }
    width = m_OsrWindowHeadless->GetWidth();
    height = m_OsrWindowHeadless->GetHeight();
    return m_OsrWindowHeadless->GetBuffer();
}

void PytoniumLibrary::SendMouseMoveEvent(int x, int y, bool mouseLeave, uint32_t modifiers) {
    if (!m_Browser || !m_Browser->GetHost()) return;
    CefMouseEvent event;
    event.x = x;
    event.y = y;
    event.modifiers = modifiers;
    m_Browser->GetHost()->SendMouseMoveEvent(event, mouseLeave);
}

void PytoniumLibrary::SendMouseClickEvent(int x, int y, int button, bool mouseUp,
                                           int clickCount, uint32_t modifiers) {
    if (!m_Browser || !m_Browser->GetHost()) return;
    CefMouseEvent event;
    event.x = x;
    event.y = y;
    event.modifiers = modifiers;

    CefBrowserHost::MouseButtonType cefButton;
    switch (button) {
        case 0: cefButton = MBT_LEFT; break;
        case 1: cefButton = MBT_MIDDLE; break;
        case 2: cefButton = MBT_RIGHT; break;
        default: cefButton = MBT_LEFT; break;
    }

    m_Browser->GetHost()->SendMouseClickEvent(event, cefButton, mouseUp, clickCount);
}

void PytoniumLibrary::SendMouseWheelEvent(int x, int y, int deltaX, int deltaY, uint32_t modifiers) {
    if (!m_Browser || !m_Browser->GetHost()) return;
    CefMouseEvent event;
    event.x = x;
    event.y = y;
    event.modifiers = modifiers;
    m_Browser->GetHost()->SendMouseWheelEvent(event, deltaX, deltaY);
}

void PytoniumLibrary::SendKeyEvent(int windowsKeyCode, int nativeKeyCode, int type,
                                    uint32_t modifiers, bool isSystemKey) {
    if (!m_Browser || !m_Browser->GetHost()) return;
    CefKeyEvent event;
    event.windows_key_code = windowsKeyCode;
    event.native_key_code = nativeKeyCode;
    event.modifiers = modifiers;
    event.is_system_key = isSystemKey;

    switch (type) {
        case 0: event.type = KEYEVENT_RAWKEYDOWN; break;
        case 1: event.type = KEYEVENT_KEYUP; break;
        case 2: event.type = KEYEVENT_CHAR; break;
        default: event.type = KEYEVENT_RAWKEYDOWN; break;
    }

    m_Browser->GetHost()->SendKeyEvent(event);
}

void PytoniumLibrary::SendCharEvent(int charCode, uint32_t modifiers) {
    if (!m_Browser || !m_Browser->GetHost()) return;
    CefKeyEvent event;
    event.type = KEYEVENT_CHAR;
    event.windows_key_code = charCode;
    event.character = static_cast<char16_t>(charCode);
    event.unmodified_character = static_cast<char16_t>(charCode);
    event.native_key_code = 0;
    event.modifiers = modifiers;
    event.is_system_key = false;
    m_Browser->GetHost()->SendKeyEvent(event);
}

void PytoniumLibrary::SendFocusEvent(bool setFocus) {
    if (!m_Browser || !m_Browser->GetHost()) return;
    m_Browser->GetHost()->SetFocus(setFocus);
}

void PytoniumLibrary::SetShowInTaskbar(bool show) {
    m_ShowInTaskbar = show;
}

int PytoniumLibrary::CreateBrowserOsr(const std::string& url, int width, int height,
                                       const std::string& iconPath, bool clickThrough)
{
    // Get or create the shared client handler
    CefWrapperClientHandler* handler = CefWrapperClientHandler::GetInstance();
    if (!handler) {
        CefRefPtr<CefCommandLine> command_line = CefCommandLine::GetGlobalCommandLine();
        bool use_views = command_line->HasSwitch("use-views");
        new CefWrapperClientHandler(use_views);
        handler = CefWrapperClientHandler::GetInstance();
    }

    // Create the OSR host window (or headless handler)
    CefWindowHandle osrWindowHandle = kNullWindowHandle;

    if (m_HeadlessMode) {
        // Headless: no OS window, just a buffer + callback
        m_OsrWindowHeadless = new OsrWindowHeadless(width, height);
        // osrWindowHandle stays kNullWindowHandle — CEF supports this for headless
    }
#if defined(OS_WIN)
    else {
        // Create the OSR window (layered Win32 window)
        m_OsrWindow = new OsrWindowWin(width, height, clickThrough, m_ShowInTaskbar);
        HWND osrHwnd = m_OsrWindow->Create();
        if (!osrHwnd) {
            std::cerr << "CreateBrowserOsr: Failed to create OSR window!" << std::endl;
            m_OsrWindow = nullptr;
            return -1;
        }
        osrWindowHandle = osrHwnd;
    }
#elif defined(OS_LINUX)
    else {
        // On Linux, create an OsrWindowX11 for transparent rendering
        m_OsrWindow = new OsrWindowX11(width, height, clickThrough, m_ShowInTaskbar);
        ::Window x11Window = m_OsrWindow->Create();
        if (x11Window == None) {
            std::cerr << "CreateBrowserOsr: Failed to create OSR X11 window!" << std::endl;
            m_OsrWindow = nullptr;
            return -1;
        }
        osrWindowHandle = x11Window;
    }
#endif

    // Configure browser settings for OSR
    cef_browser_settings_t cefBrowserSettings;
    memset(&cefBrowserSettings, 0, sizeof(cef_browser_settings_t));
    cefBrowserSettings.size = sizeof(cef_browser_settings_t);
    cefBrowserSettings.windowless_frame_rate = 60;
    cefBrowserSettings.background_color = 0x00000000;  // Fully transparent
    CefBrowserSettings browser_settings(cefBrowserSettings);

    // Configure window info for windowless (OSR) rendering
    CefWindowInfo window_info;
    window_info.SetAsWindowless(osrWindowHandle);
#if defined(OS_WIN)
    window_info.runtime_style = CEF_RUNTIME_STYLE_ALLOY;
#endif

    // Serialize bindings into extra_info for the renderer
    CefRefPtr<CefDictionaryValue> extra = CefDictionaryValue::Create();
    if (!m_Javascript_Bindings.empty())
    {
        CefRefPtr<CefListValue> bindings = CefListValue::Create();
        bindings->SetSize(m_Javascript_Bindings.size());
        int listIndex = 0;
        for (const auto &binding: m_Javascript_Bindings)
        {
            CefRefPtr<CefDictionaryValue> dic = CefDictionaryValue::Create();
            dic->SetString("MessageTopic", binding.functionName);
            dic->SetString("JavascriptObject", binding.JavascriptObject);
            CefRefPtr<CefBinaryValue> functionPointer = CefBinaryValue::Create(
                    &binding.function, sizeof(binding.function));
            dic->SetBinary("FunctionPointer", functionPointer);
            bindings->SetDictionary(listIndex, dic);
            listIndex++;
        }
        extra->SetList("JavascriptBindings", bindings);
        extra->SetInt("JavascriptBindingsSize",
                      static_cast<int>(m_Javascript_Bindings.size()));
    }

    if (!m_Javascript_Python_Bindings.empty())
    {
        CefRefPtr<CefListValue> bindings = CefListValue::Create();
        bindings->SetSize(m_Javascript_Python_Bindings.size());
        int listIndex = 0;
        for (const auto &binding: m_Javascript_Python_Bindings)
        {
            CefRefPtr<CefDictionaryValue> dic = CefDictionaryValue::Create();
            dic->SetString("MessageTopic", binding.FunctionName);
            dic->SetString("JavascriptObject", binding.JavascriptObject);
            dic->SetBool("ReturnsValue", binding.ReturnsValue);
            CefRefPtr<CefBinaryValue> handlerFunc = CefBinaryValue::Create(
                    &binding.HandlerFunction, sizeof(binding.HandlerFunction));
            CefRefPtr<CefBinaryValue> pythonObject = CefBinaryValue::Create(
                    &binding.PythonCallbackObject, sizeof(binding.PythonCallbackObject));
            dic->SetBinary("HandlerFunction", handlerFunc);
            dic->SetBinary("PythonFunctionObject", pythonObject);
            bindings->SetDictionary(listIndex, dic);
            listIndex++;
        }
        extra->SetList("JavascriptPythonBindings", bindings);
        extra->SetInt("JavascriptPythonBindingsSize",
                      static_cast<int>(m_Javascript_Python_Bindings.size()));
    }

    m_Browser = CefBrowserHost::CreateBrowserSync(window_info, handler, url,
                                                   browser_settings, extra, nullptr);
    if (!m_Browser) {
        std::cerr << "CreateBrowserOsr: CreateBrowserSync failed!" << std::endl;
        if (m_HeadlessMode) {
            m_OsrWindowHeadless = nullptr;
        } else {
#if defined(OS_WIN) || defined(OS_LINUX)
            m_OsrWindow->Destroy();
            m_OsrWindow = nullptr;
#endif
        }
        return -1;
    }

    m_BrowserId = m_Browser->GetIdentifier();
    s_InstanceCount++;

    // Connect the browser to the appropriate OSR handler and register with dispatcher
    if (m_HeadlessMode) {
        m_OsrWindowHeadless->SetBrowser(m_Browser);
        handler->GetOsrDispatcher()->RegisterWindow(m_BrowserId, m_OsrWindowHeadless);
    } else {
#if defined(OS_WIN) || defined(OS_LINUX)
        m_OsrWindow->SetBrowser(m_Browser);
        handler->GetOsrDispatcher()->RegisterWindow(m_BrowserId, m_OsrWindow);
#endif
    }

    // Register per-browser bindings and mark as OSR
    handler->RegisterBrowserBindings(m_BrowserId,
        m_Javascript_Bindings, m_Javascript_Python_Bindings,
        m_StateHandlerPythonBindings, m_ContextMenuBindings);
    handler->GetBrowserState(m_BrowserId).isOsr = true;
    handler->GetBrowserState(m_BrowserId).isHeadless = m_HeadlessMode;

    return m_BrowserId;
}
