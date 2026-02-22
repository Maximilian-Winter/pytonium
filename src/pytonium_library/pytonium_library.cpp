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
#if defined(OS_WIN)
    if (m_OsrMode) {
        return CreateBrowserOsr(url, width, height, iconPath, false);
    }
#endif

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

    if (frameless) {
        window_info.style = WS_POPUP | WS_VISIBLE | WS_CLIPCHILDREN | WS_CLIPSIBLINGS;
        window_info.parent_window = nullptr;
        window_info.bounds.x = CW_USEDEFAULT;
        window_info.bounds.y = CW_USEDEFAULT;
    } else {
        window_info.SetAsPopup(nullptr, "");
    }
#elif defined(OS_LINUX)
    if (frameless) {
        window_info.SetAsWindowless(nullptr, true);
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
        CefWindowHandle hwnd = m_Browser->GetHost()->GetWindowHandle();
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

void PytoniumLibrary::UpdateMessageLoop() { CefDoMessageLoopWork(); }

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

void PytoniumLibrary::MinimizeWindow()
{
#if defined(OS_WIN)
    if (!m_Browser) return;
    CefWindowHandle hwnd = m_Browser->GetHost()->GetWindowHandle();
    if (hwnd && IsWindow(hwnd)) {
        ShowWindow(hwnd, SW_MINIMIZE);
    }
#endif
}

void PytoniumLibrary::MaximizeWindow()
{
#if defined(OS_WIN)
    if (!m_Browser) return;
    m_Browser->GetHost()->SetFocus(true);
    CefWindowHandle hwnd = m_Browser->GetHost()->GetWindowHandle();
    if (hwnd && IsWindow(hwnd)) {
        ShowWindow(hwnd, SW_MAXIMIZE);
    }
#endif
}

void PytoniumLibrary::RestoreWindow()
{
#if defined(OS_WIN)
    if (!m_Browser) return;
    CefWindowHandle hwnd = m_Browser->GetHost()->GetWindowHandle();
    if (hwnd && IsWindow(hwnd)) {
        ShowWindow(hwnd, SW_RESTORE);
    }
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
    CefWindowHandle hwnd = m_Browser->GetHost()->GetWindowHandle();
    if (hwnd && IsWindow(hwnd)) {
        WINDOWPLACEMENT wp;
        wp.length = sizeof(WINDOWPLACEMENT);
        if (GetWindowPlacement(hwnd, &wp)) {
            return wp.showCmd == SW_SHOWMAXIMIZED;
        }
    }
#endif
    return false;
}

void PytoniumLibrary::DragWindow(int deltaX, int deltaY)
{
#if defined(OS_WIN)
    if (!m_Browser) return;
    CefWindowHandle hwnd = m_Browser->GetHost()->GetWindowHandle();
    if (hwnd && IsWindow(hwnd)) {
        RECT rect;
        if (GetWindowRect(hwnd, &rect)) {
            int newX = rect.left + deltaX;
            int newY = rect.top + deltaY;
            SetWindowPos(hwnd, NULL, newX, newY, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
        }
    }
#endif
}

void PytoniumLibrary::GetWindowPosition(int& x, int& y)
{
    x = 0;
    y = 0;
#if defined(OS_WIN)
    if (!m_Browser) return;
    CefWindowHandle hwnd = m_Browser->GetHost()->GetWindowHandle();
    if (hwnd && IsWindow(hwnd)) {
        RECT rect;
        if (GetWindowRect(hwnd, &rect)) {
            x = rect.left;
            y = rect.top;
        }
    }
#endif
}

void PytoniumLibrary::SetWindowPosition(int x, int y)
{
#if defined(OS_WIN)
    if (!m_Browser) return;
    CefWindowHandle hwnd = m_Browser->GetHost()->GetWindowHandle();
    if (hwnd && IsWindow(hwnd)) {
        SetWindowPos(hwnd, NULL, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
    }
#endif
}

void PytoniumLibrary::GetWindowSize(int& width, int& height)
{
    width = 0;
    height = 0;

#if defined(OS_WIN)
    if (!m_Browser) return;

    CefWindowHandle hwnd = m_Browser->GetHost()->GetWindowHandle();
    if (!hwnd || !IsWindow(hwnd)) return;

    RECT rect;
    if (GetWindowRect(hwnd, &rect)) {
        width = rect.right - rect.left;
        height = rect.bottom - rect.top;
    }
#endif
}

void PytoniumLibrary::SetWindowSize(int width, int height)
{
#if defined(OS_WIN)
    if (!m_Browser) return;

    CefWindowHandle hwnd = m_Browser->GetHost()->GetWindowHandle();
    if (!hwnd || !IsWindow(hwnd)) return;
    if (IsZoomed(hwnd)) return;

    SetWindowPos(hwnd, NULL, 0, 0, width, height,
                 SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED);
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
    // For OSR browsers, return the layered window handle
    if (m_OsrMode && m_OsrWindow) {
        return reinterpret_cast<void*>(m_OsrWindow->GetHwnd());
    }
#endif
    if (!m_Browser || !m_Browser->GetHost()) {
        return nullptr;
    }
    return reinterpret_cast<void*>(m_Browser->GetHost()->GetWindowHandle());
}

void PytoniumLibrary::ResizeWindow(int newWidth, int newHeight, int anchor)
{
#if defined(OS_WIN)
    if (!m_Browser) return;

    CefWindowHandle hwnd = m_Browser->GetHost()->GetWindowHandle();
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
#endif
}

void PytoniumLibrary::SetOsrMode(bool osr) {
    m_OsrMode = osr;
}

#if defined(OS_WIN)
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

    // Create the OSR window (layered Win32 window)
    m_OsrWindow = new OsrWindowWin(width, height, clickThrough);
    HWND osrHwnd = m_OsrWindow->Create();
    if (!osrHwnd) {
        std::cerr << "CreateBrowserOsr: Failed to create OSR window!" << std::endl;
        m_OsrWindow = nullptr;
        return -1;
    }

    // Configure browser settings for OSR
    cef_browser_settings_t cefBrowserSettings;
    memset(&cefBrowserSettings, 0, sizeof(cef_browser_settings_t));
    cefBrowserSettings.size = sizeof(cef_browser_settings_t);
    cefBrowserSettings.windowless_frame_rate = 60;
    cefBrowserSettings.background_color = 0x00000000;  // Fully transparent
    CefBrowserSettings browser_settings(cefBrowserSettings);

    // Configure window info for windowless (OSR) rendering
    CefWindowInfo window_info;
    window_info.SetAsWindowless(osrHwnd);
    window_info.runtime_style = CEF_RUNTIME_STYLE_ALLOY;

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
        m_OsrWindow->Destroy();
        m_OsrWindow = nullptr;
        return -1;
    }

    m_BrowserId = m_Browser->GetIdentifier();
    s_InstanceCount++;

    // Connect the browser to the OSR window
    m_OsrWindow->SetBrowser(m_Browser);

    // Register with the OSR dispatcher
    handler->GetOsrDispatcher()->RegisterWindow(m_BrowserId, m_OsrWindow);

    // Register per-browser bindings and mark as OSR
    handler->RegisterBrowserBindings(m_BrowserId,
        m_Javascript_Bindings, m_Javascript_Python_Bindings,
        m_StateHandlerPythonBindings, m_ContextMenuBindings);
    handler->GetBrowserState(m_BrowserId).isOsr = true;

    return m_BrowserId;
}
#endif
