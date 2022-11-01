#ifndef LIBRARY_LIBRARY_H
#define LIBRARY_LIBRARY_H

#include <Windows.h>

#include "cef_wrapper_app.h"
#include "cef_wrapper_client_handler.h"
#include "include/cef_command_line.h"
#include "include/cef_sandbox_win.h"
#include "javascript_binding.h"

class PytoniumLibrary {
public:
  PytoniumLibrary();
  void InitPytonium(std::string start_url, int init_width, int init_height);
  void ExecuteJavascript(std::string code);
  void ShutdownPytonium();
  bool IsRunning();
  bool IsReadyToExecuteJavascript();
  void UpdateMessageLoop();
  void AddJavascriptBinding(std::string name,
                                js_binding_function_ptr jsNativeApiFunctionPtr, std::string javascript_object);
  void AddJavascriptPythonBinding(std::string name,
      js_python_bindings_handler_function_ptr python_bindings_handler,
      js_python_callback_object_ptr python_callback_object, std::string javascript_object);
  void SetCustomCefSubprocessPath(std::string cefsub_path);
  void SetCustomCefCachePath(std::string cef_cache_path);
  void SetCustomCefResourcePath(std::string cef_resources_path);
  void SetCustomCefLocalesPath(std::string cef_locales_path);

  void SetCustomIconPath(std::string icon_path);
  void LoadUrl(std::string url);
private:

    CefRefPtr<CefWrapperApp> m_App;

    bool m_UseCustomCefSubPath = false;
    std::string m_CustomCefSubPath = "";

    bool m_UseCustomCefCachePath = false;
    std::string m_CustomCefCachePath = "";

    bool m_UseCustomCefResourcesPath = false;
    std::string m_CustomCefResourcesPath = "";

    bool m_UseCustomCefLocalesPath = false;
    std::string m_CustomCefLocalesPath = "";

    bool m_UseCustomIcon = false;
    std::string m_CustomIconPath = "";

    std::vector<JavascriptBinding> m_Javascript_Bindings;
    std::vector<JavascriptPythonBinding> m_Javascript_Python_Bindings;
}
;

#endif//LIBRARY_LIBRARY_H
