#include "pytonium_library.h"

#include "global_vars.h"
#include "javascript_binding.h"
#include "cef_value_wrapper.h"
#include "include/internal/cef_types.h"
#include <cstring>
#include <filesystem>
#include <iostream>
#include <utility>
#include <vector>
#undef CEF_USE_SANDBOX

#if defined(OS_WIN)
#include <Windows.h>
#endif


std::string ExePath() {
#if OS_WIN
  // Try multiple locations for the subprocess executable
  std::vector<std::filesystem::path> possiblePaths;
  
  // From current working directory
  possiblePaths.push_back(std::filesystem::current_path() / "bin" / "pytonium_subprocess.exe");
  possiblePaths.push_back(std::filesystem::current_path() / "pytonium_subprocess.exe");
  
  // From executable directory
  char exePath[MAX_PATH];
  if (GetModuleFileNameA(NULL, exePath, MAX_PATH) > 0) {
    std::filesystem::path exeDir = std::filesystem::path(exePath).parent_path();
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
  std::filesystem::path cwd = std::filesystem::current_path() /"bin" ;   //"C:\\Dev\\cef-binaries\\cef_binary_106.0.27+g20ed841+chromium-106.0.5249.103_windows64\\cmake-build-debug-visual-studio\\src\\pytonium_subprocess\\Debug\\pytonium_subprocess.exe";
  return cwd.string();
}

std::string LocalesPath() {
  std::filesystem::path cwd = std::filesystem::current_path() /"bin" / "locales";   //"C:\\Dev\\cef-binaries\\cef_binary_106.0.27+g20ed841+chromium-106.0.5249.103_windows64\\cmake-build-debug-visual-studio\\src\\pytonium_subprocess\\Debug\\pytonium_subprocess.exe";
  return cwd.string();
}

std::string CachePath() {
  std::filesystem::path cwd = std::filesystem::current_path() / "cache";   //"C:\\Dev\\cef-binaries\\cef_binary_106.0.27+g20ed841+chromium-106.0.5249.103_windows64\\cmake-build-debug-visual-studio\\src\\pytonium_subprocess\\Debug\\pytonium_subprocess.exe";
  return cwd.string();
}

void PytoniumLibrary::InitPytonium(std::string start_url, int init_width, int init_height) {
  //CefEnableHighDPISupport();

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
  //int argc = 0;
  //char* argv[1] { };
  CefMainArgs main_args;
  CefRefPtr<CefCommandLine> command_line = CefCommandLine::CreateCommandLine();
  command_line->InitFromString(std::data(name));
#endif

  // Disable Chrome Runtime - must be done before CefExecuteProcess
  // This removes the Chrome UI (tabs, address bar, etc.)
  command_line->AppendSwitch("disable-chrome-runtime");
  command_line->AppendSwitchWithValue("disable-features", "ChromeRuntime");
  
  // Fix Release build GPU/Network service crashes
  command_line->AppendSwitch("disable-gpu-sandbox");
  command_line->AppendSwitch("disable-setuid-sandbox");
  command_line->AppendSwitch("disable-network-service-sandbox");
  command_line->AppendSwitch("no-sandbox");
  
  // Alternative: Run GPU in browser process (slower but more stable)
  // Uncomment the next line if GPU process still crashes:
  // command_line->AppendSwitch("in-process-gpu");
  
  // Disable GPU if all else fails (software rendering):
  // command_line->AppendSwitch("disable-gpu");
  // command_line->AppendSwitch("disable-software-rasterizer");
  
  // Debug: print command line to verify switches
  CefString cmdLineStr = command_line->GetCommandLineString();
  std::cout << "Command line: " << cmdLineStr.ToString() << std::endl;




  m_App = CefRefPtr<CefWrapperApp>(new CefWrapperApp( std::move(start_url), m_Javascript_Bindings, m_Javascript_Python_Bindings, m_StateHandlerPythonBindings, m_ContextMenuBindings, m_CustomSchemes, m_MimeTypeMap, m_FramelessWindow));
  CefWrapperBrowserProcessHandler::SetInitialResolution(init_width, init_height);
  CefExecuteProcess(main_args, m_App.get(), sandbox_info);



  // Initialize CEF settings using the underlying C struct
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

  // settings.multi_threaded_message_loop = true;
  settings.no_sandbox = true;

  if(m_UseCustomCefSubPath)
  {
    CefString(&settings.browser_subprocess_path).FromASCII(m_CustomCefSubPath.c_str());
  }
  else
  {
    CefString(&settings.browser_subprocess_path).FromASCII(ExePath().c_str());
  }

  //settings.log_severity = LOGSEVERITY_VERBOSE;
  CefInitialize(main_args, settings, m_App.get(), sandbox_info);
  g_IsRunning = true;

  if(m_UseCustomIcon)
  {
#if defined(OS_WIN)
    std::wstring temp = std::wstring(m_CustomIconPath.begin(), m_CustomIconPath.end());
    LPCWSTR w_icon_path = temp.c_str();

    CefWindowHandle hwnd = m_App->GetBrowser()->GetHost()->GetWindowHandle();

    if (hwnd)
    {
      HICON hIcon = (HICON)LoadImage(NULL, w_icon_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE);
      SendMessage(hwnd, WM_SETICON, ICON_BIG, (LPARAM)hIcon);
    }

#endif

  }
}
void PytoniumLibrary::ExecuteJavascript(const std::string& code) {
  CefRefPtr<CefFrame> frame = m_App->GetBrowser()->GetMainFrame();
  if (g_IsRunning) {
    if (CefWrapperClientHandler::GetInstance()->IsReadyToExecuteJs()) {
      frame->ExecuteJavaScript(code, frame->GetURL(), 0);
    }
  }
}
void PytoniumLibrary::ShutdownPytonium() { CefShutdown(); }

bool PytoniumLibrary::IsRunning() { return g_IsRunning; }

void PytoniumLibrary::UpdateMessageLoop() { CefDoMessageLoopWork(); }
bool PytoniumLibrary::IsReadyToExecuteJavascript() {
  return CefWrapperClientHandler::GetInstance()->IsReadyToExecuteJs();
}

void PytoniumLibrary::AddJavascriptBinding(std::string name, js_binding_function_ptr jsNativeApiFunctionPtr, std::string javascript_object)
{
  m_Javascript_Bindings.emplace_back(std::move(name), jsNativeApiFunctionPtr, std::move(javascript_object));
}
PytoniumLibrary::PytoniumLibrary() = default;
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
 m_App->LoadUrl(std::move(url));
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
    CefRefPtr<CefProcessMessage> return_to_javascript_message =
            CefProcessMessage::Create("return-to-javascript");

    CefRefPtr<CefListValue> return_value_message_args =
            return_to_javascript_message->GetArgumentList();

    return_value_message_args->SetInt(0, message_id);

    return_value_message_args->SetValue(1, CefValueWrapperHelper::ConvertWrapperToCefValue(returnValue));


    //CefRefPtr<CefValue> val = return_to_javascript_message->GetArgumentList()->GetValue(1);

    //CefRefPtr<CefV8Value> val2 = CefValueWrapperHelper::ConvertCefValueToV8Value(val);
    m_App->GetBrowser()->GetMainFrame()->SendProcessMessage(PID_RENDERER, return_to_javascript_message);

}

void PytoniumLibrary::AddStateHandlerPythonBinding(state_handler_function_ptr stateHandlerFunctionPtr,
                                                   state_callback_object_ptr stateCallbackObjectPtr, const std::vector<std::string>& namespacesToSubscribeTo)
{
    m_StateHandlerPythonBindings.emplace_back(stateHandlerFunctionPtr, stateCallbackObjectPtr, namespacesToSubscribeTo);
}

void PytoniumLibrary::SetState(const std::string& stateNamespace, const std::string& key, CefValueWrapper value)
{
    if(g_IsRunning)
    {
        CefRefPtr<CefProcessMessage> return_to_javascript_message =
                CefProcessMessage::Create("set-app-state");

        CefRefPtr<CefListValue> return_value_message_args =
                return_to_javascript_message->GetArgumentList();

        return_value_message_args->SetString(0, stateNamespace);

        return_value_message_args->SetString(1, key);

        return_value_message_args->SetValue(2, CefValueWrapperHelper::ConvertWrapperToCefValue(value));


        //CefRefPtr<CefValue> val = return_to_javascript_message->GetArgumentList()->GetValue(1);

        //CefRefPtr<CefV8Value> val2 = CefValueWrapperHelper::ConvertCefValueToV8Value(val);
        m_App->GetBrowser()->GetMainFrame()->SendProcessMessage(PID_RENDERER, return_to_javascript_message);
    }

}

void PytoniumLibrary::RemoveState(const std::string& stateNamespace, const std::string& key)
{
    CefRefPtr<CefProcessMessage> return_to_javascript_message =
            CefProcessMessage::Create("remove-app-state");

    CefRefPtr<CefListValue> return_value_message_args =
            return_to_javascript_message->GetArgumentList();

    return_value_message_args->SetString(0, stateNamespace);

    return_value_message_args->SetString(1, key);

    m_App->GetBrowser()->GetMainFrame()->SendProcessMessage(PID_RENDERER, return_to_javascript_message);
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
    CefWrapperClientHandler* client = (CefWrapperClientHandler*)CefWrapperBrowserProcessHandler::GetInstance()->GetDefaultClient().get();
    client->SetCurrentContextMenuName(contextMenuNamespace);
}

void PytoniumLibrary::SetShowDebugContextMenu(bool show)
{
    CefWrapperClientHandler* client = (CefWrapperClientHandler*)CefWrapperBrowserProcessHandler::GetInstance()->GetDefaultClient().get();
    client->SetShowDebugContextMenu(show);
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
    // Store the frameless setting - it will be applied when InitPytonium is called
    // via the CefWrapperApp constructor
    m_FramelessWindow = frameless;
}

void PytoniumLibrary::MinimizeWindow()
{
#if defined(OS_WIN)
    if (m_App && m_App->GetBrowser()) {
        CefWindowHandle hwnd = m_App->GetBrowser()->GetHost()->GetWindowHandle();
        if (hwnd) {
            ShowWindow(hwnd, SW_MINIMIZE);
        }
    }
#endif
}

void PytoniumLibrary::MaximizeWindow()
{
#if defined(OS_WIN)
    if (m_App && m_App->GetBrowser()) {
        m_App->GetBrowser()->GetHost()->SetFocus(true);
        // Use Windows API for maximize since CEF doesn't have a direct maximize method
        CefWindowHandle hwnd = m_App->GetBrowser()->GetHost()->GetWindowHandle();
        if (hwnd) {
            ShowWindow(hwnd, SW_MAXIMIZE);
        }
    }
#endif
}

void PytoniumLibrary::RestoreWindow()
{
#if defined(OS_WIN)
    if (m_App && m_App->GetBrowser()) {
        CefWindowHandle hwnd = m_App->GetBrowser()->GetHost()->GetWindowHandle();
        if (hwnd) {
            ShowWindow(hwnd, SW_RESTORE);
        }
    }
#endif
}

void PytoniumLibrary::CloseWindow()
{
    if (m_App && m_App->GetBrowser()) {
        m_App->GetBrowser()->GetHost()->CloseBrowser(false);
    }
}

bool PytoniumLibrary::IsMaximized()
{
#if defined(OS_WIN)
    if (m_App && m_App->GetBrowser()) {
        CefWindowHandle hwnd = m_App->GetBrowser()->GetHost()->GetWindowHandle();
        if (hwnd) {
            WINDOWPLACEMENT wp;
            wp.length = sizeof(WINDOWPLACEMENT);
            if (GetWindowPlacement(hwnd, &wp)) {
                return wp.showCmd == SW_SHOWMAXIMIZED;
            }
        }
    }
#endif
    return false;
}

void PytoniumLibrary::DragWindow(int deltaX, int deltaY)
{
#if defined(OS_WIN)
    if (m_App && m_App->GetBrowser()) {
        CefWindowHandle hwnd = m_App->GetBrowser()->GetHost()->GetWindowHandle();
        if (hwnd) {
            RECT rect;
            if (GetWindowRect(hwnd, &rect)) {
                int newX = rect.left + deltaX;
                int newY = rect.top + deltaY;
                // Use SWP_FRAMECHANGED to force a redraw and SWP_ASYNCWINDOWPOS for smoother movement
                SetWindowPos(hwnd, NULL, newX, newY, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
            }
        }
    }
#endif
}

void PytoniumLibrary::GetWindowPosition(int& x, int& y)
{
#if defined(OS_WIN)
    if (m_App && m_App->GetBrowser()) {
        CefWindowHandle hwnd = m_App->GetBrowser()->GetHost()->GetWindowHandle();
        if (hwnd) {
            RECT rect;
            if (GetWindowRect(hwnd, &rect)) {
                x = rect.left;
                y = rect.top;
                return;
            }
        }
    }
#endif
    x = 0;
    y = 0;
}

void PytoniumLibrary::SetWindowPosition(int x, int y)
{
#if defined(OS_WIN)
    if (m_App && m_App->GetBrowser()) {
        CefWindowHandle hwnd = m_App->GetBrowser()->GetHost()->GetWindowHandle();
        if (hwnd) {
            SetWindowPos(hwnd, NULL, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
        }
    }
#endif
}

void PytoniumLibrary::GetWindowSize(int& width, int& height)
{
    width = 0;
    height = 0;
    
#if defined(OS_WIN)
    if (!m_App || !m_App->GetBrowser()) {
        std::cout << "[Pytonium] GetWindowSize: app or browser is null" << std::endl;
        return;
    }
    
    CefWindowHandle hwnd = m_App->GetBrowser()->GetHost()->GetWindowHandle();
    std::cout << "[Pytonium] GetWindowSize: hwnd=" << hwnd << std::endl;
    
    if (!hwnd) {
        std::cout << "[Pytonium] GetWindowSize: hwnd is null" << std::endl;
        return;
    }
    
    if (!IsWindow(hwnd)) {
        std::cout << "[Pytonium] GetWindowSize: hwnd is not a valid window" << std::endl;
        return;
    }
    
    RECT rect;
    if (GetWindowRect(hwnd, &rect)) {
        width = rect.right - rect.left;
        height = rect.bottom - rect.top;
        std::cout << "[Pytonium] GetWindowSize: success, " << width << "x" << height << std::endl;
    } else {
        std::cout << "[Pytonium] GetWindowSize: GetWindowRect failed, error=" << GetLastError() << std::endl;
    }
#endif
}

void PytoniumLibrary::SetWindowSize(int width, int height)
{
#if defined(OS_WIN)
    std::cout << "[Pytonium] SetWindowSize called: " << width << "x" << height << std::endl;
    
    if (!m_App || !m_App->GetBrowser()) {
        std::cout << "[Pytonium] SetWindowSize failed: app or browser is null" << std::endl;
        return;
    }
    
    CefWindowHandle hwnd = m_App->GetBrowser()->GetHost()->GetWindowHandle();
    std::cout << "[Pytonium] Window handle: " << hwnd << std::endl;
    
    if (!hwnd) {
        std::cout << "[Pytonium] SetWindowSize failed: hwnd is null" << std::endl;
        return;
    }
    
    if (!IsWindow(hwnd)) {
        std::cout << "[Pytonium] SetWindowSize failed: hwnd is not a valid window" << std::endl;
        return;
    }
    
    if (IsZoomed(hwnd)) {
        std::cout << "[Pytonium] SetWindowSize failed: window is maximized" << std::endl;
        return;
    }
    
    BOOL result = SetWindowPos(hwnd, NULL, 0, 0, width, height, 
                               SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED);
    
    if (!result) {
        std::cout << "[Pytonium] SetWindowPos failed, error=" << GetLastError() << std::endl;
    } else {
        std::cout << "[Pytonium] SetWindowSize succeeded" << std::endl;
    }
#endif
}

void PytoniumLibrary::ResizeWindow(int newWidth, int newHeight, int anchor)
{
#if defined(OS_WIN)
    std::cout << "[Pytonium] ResizeWindow called: " << newWidth << "x" << newHeight << ", anchor=" << anchor << std::endl;
    
    if (!m_App) {
        std::cout << "[Pytonium] ResizeWindow failed: m_App is null" << std::endl;
        return;
    }
    
    CefRefPtr<CefBrowser> browser = m_App->GetBrowser();
    if (!browser) {
        std::cout << "[Pytonium] ResizeWindow failed: browser is null" << std::endl;
        return;
    }
    
    CefWindowHandle hwnd = browser->GetHost()->GetWindowHandle();
    if (!hwnd) {
        std::cout << "[Pytonium] ResizeWindow failed: hwnd is null" << std::endl;
        return;
    }
    
    // Check if window is maximized - can't resize maximized windows
    if (IsZoomed(hwnd)) {
        std::cout << "[Pytonium] ResizeWindow failed: window is maximized" << std::endl;
        return;
    }
    
    // Get current position and size
    RECT rect;
    if (!GetWindowRect(hwnd, &rect)) {
        std::cout << "[Pytonium] ResizeWindow failed: GetWindowRect failed, error=" << GetLastError() << std::endl;
        return;
    }
    
    int currX = rect.left;
    int currY = rect.top;
    int currWidth = rect.right - rect.left;
    int currHeight = rect.bottom - rect.top;
    
    std::cout << "[Pytonium] Current: pos=(" << currX << "," << currY << ") size=" << currWidth << "x" << currHeight << std::endl;
    
    int newX = currX;
    int newY = currY;
    
    // Adjust position based on anchor to keep that corner fixed
    // anchor 0 (top-left): no position change
    // anchor 1 (top-right): adjust X based on width change
    // anchor 2 (bottom-left): adjust Y based on height change  
    // anchor 3 (bottom-right): adjust both X and Y
    if (anchor == 1 || anchor == 3) {
        newX = currX + (currWidth - newWidth);
    }
    if (anchor == 2 || anchor == 3) {
        newY = currY + (currHeight - newHeight);
    }
    
    std::cout << "[Pytonium] Setting new pos=(" << newX << "," << newY << ") size=" << newWidth << "x" << newHeight << std::endl;
    
    // Move and resize in one atomic operation
    BOOL result = SetWindowPos(hwnd, NULL, newX, newY, newWidth, newHeight, 
                               SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED);
    
    if (!result) {
        std::cout << "[Pytonium] SetWindowPos failed, error=" << GetLastError() << std::endl;
    } else {
        std::cout << "[Pytonium] ResizeWindow succeeded" << std::endl;
    }
#endif
}
