#include "pytonium_library.h"

#include "global_vars.h"
#include "javascript_binding.h"
#include "cef_value_wrapper.h"
#include <filesystem>
#include <iostream>
#include <utility>
#undef CEF_USE_SANDBOX

#if defined(OS_WIN)
#include <Windows.h>
#endif


std::string ExePath() {
#if OS_WIN
  std::filesystem::path cwd = std::filesystem::current_path() / "bin" / "pytonium_subprocess.exe";   //"C:\\Dev\\cef-binaries\\cef_binary_106.0.27+g20ed841+chromium-106.0.5249.103_windows64\\cmake-build-debug-visual-studio\\src\\pytonium_subprocess\\Debug\\pytonium_subprocess.exe";
  return cwd.string();
#else
  std::filesystem::path cwd = std::filesystem::current_path() / "pytonium_subprocess";   //"C:\\Dev\\cef-binaries\\cef_binary_106.0.27+g20ed841+chromium-106.0.5249.103_windows64\\cmake-build-debug-visual-studio\\src\\pytonium_subprocess\\Debug\\pytonium_subprocess.exe";
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
  
  // Debug: print command line to verify switches
  CefString cmdLineStr = command_line->GetCommandLineString();
  std::cout << "Command line: " << cmdLineStr.ToString() << std::endl;




  m_App = CefRefPtr<CefWrapperApp>(new CefWrapperApp( std::move(start_url), m_Javascript_Bindings, m_Javascript_Python_Bindings, m_StateHandlerPythonBindings, m_ContextMenuBindings, m_CustomSchemes, m_MimeTypeMap, m_FramelessWindow));
  CefWrapperBrowserProcessHandler::SetInitialResolution(init_width, init_height);
  CefExecuteProcess(main_args, m_App.get(), sandbox_info);



  CefSettings settings;


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
    if (m_App && m_App->GetBrowser()) {
        m_App->GetBrowser()->GetHost()->SetWindowVisibility(false);
    }
}

void PytoniumLibrary::MaximizeWindow()
{
    if (m_App && m_App->GetBrowser()) {
        m_App->GetBrowser()->GetHost()->SetFocus(true);
        // Use Windows API for maximize since CEF doesn't have a direct maximize method
        CefWindowHandle hwnd = m_App->GetBrowser()->GetHost()->GetWindowHandle();
        if (hwnd) {
            ShowWindow(hwnd, SW_MAXIMIZE);
        }
    }
}

void PytoniumLibrary::RestoreWindow()
{
    if (m_App && m_App->GetBrowser()) {
        CefWindowHandle hwnd = m_App->GetBrowser()->GetHost()->GetWindowHandle();
        if (hwnd) {
            ShowWindow(hwnd, SW_RESTORE);
        }
    }
}

void PytoniumLibrary::CloseWindow()
{
    if (m_App && m_App->GetBrowser()) {
        m_App->GetBrowser()->GetHost()->CloseBrowser(false);
    }
}

bool PytoniumLibrary::IsMaximized()
{
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
    return false;
}
