#include "pytonium_library.h"

#include "global_vars.h"
#include "javascript_binding.h"
#include <filesystem>
#include <iostream>
#undef CEF_USE_SANDBOX


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
  CefEnableHighDPISupport();

  void *sandbox_info = nullptr;
  std::string name = "pytonium_library";
  int argc = 1;
  char* argv[1] { std::data(name) };

  CefMainArgs main_args;
  CefRefPtr<CefCommandLine> command_line = CefCommandLine::CreateCommandLine();
  command_line->InitFromArgv(argc, argv);

  command_line->AppendSwitch("no-sandbox");
  //command_line->AppendSwitch("disable-gpu");
  m_App = CefRefPtr<CefWrapperApp>(new CefWrapperApp( start_url, m_Javascript_Bindings, m_Javascript_Python_Bindings));
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
void PytoniumLibrary::ExecuteJavascript(std::string code) {
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
  m_Javascript_Bindings.push_back(JavascriptBinding(std::move(name), jsNativeApiFunctionPtr, std::move(javascript_object)));
}
PytoniumLibrary::PytoniumLibrary() {}
void PytoniumLibrary::AddJavascriptPythonBinding(
    std::string name,
    js_python_bindings_handler_function_ptr python_bindings_handler,
    js_python_callback_object_ptr python_callback_object, std::string javascript_object) {
  m_Javascript_Python_Bindings.push_back(
      JavascriptPythonBinding(python_bindings_handler, name, python_callback_object, javascript_object));
}
void PytoniumLibrary::SetCustomSubprocessPath(std::string cefsub_path) {
  m_UseCustomCefSubPath = true;
  m_CustomCefSubPath = cefsub_path;
}
void PytoniumLibrary::SetCustomCachePath(std::string cef_cache_path) {
  m_UseCustomCefCachePath = true;
  m_CustomCefCachePath = cef_cache_path;
}
void PytoniumLibrary::LoadUrl(std::string url) {
 m_App->LoadUrl(url);
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
