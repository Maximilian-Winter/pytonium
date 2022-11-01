

#include "cef_wrapper_browser_process_handler.h"
#include "cef_wrapper_client_handler.h"
#include "cef_wrapper_render_process_handler.h"
#include "custom_protocol_scheme_handler.h"
#include "javascript_binding.h"


CefWrapperBrowserProcessHandler::CefWrapperBrowserProcessHandler() = default;

/* Null, because instance will be initialized on demand. */
CefRefPtr<CefWrapperBrowserProcessHandler>
    CefWrapperBrowserProcessHandler::instance = nullptr;

CefRefPtr<CefWrapperBrowserProcessHandler>
CefWrapperBrowserProcessHandler::GetInstance() {
  if (instance == nullptr) {
    instance = CefRefPtr<CefWrapperBrowserProcessHandler>(
        new CefWrapperBrowserProcessHandler());
    instance->init_width = 1024;
    instance->init_height = 768;
  }

  return instance;
}
void CefWrapperBrowserProcessHandler::SetJavascriptBindings(
    std::vector<JavascriptBinding> javascript_bindings,
    std::vector<JavascriptPythonBinding> javascript_python_bindings) {
  GetInstance()->m_JavascriptBindings = javascript_bindings;
  GetInstance()->m_JavascriptPythonBindings = javascript_python_bindings;
}

CefRefPtr<CefClient> CefWrapperBrowserProcessHandler::GetDefaultClient() {
  return CefWrapperClientHandler::GetInstance();
}

void CefWrapperBrowserProcessHandler::OnContextInitialized() {
  CEF_REQUIRE_UI_THREAD();

  CefRefPtr<CefCommandLine> command_line =
      CefCommandLine::GetGlobalCommandLine();

  bool use_views = command_line->HasSwitch("use-views");

  // RegisterSchemeHandlerFactory();

  CefRefPtr<CefWrapperClientHandler> handler(new CefWrapperClientHandler(
      use_views, m_JavascriptBindings, m_JavascriptPythonBindings));
  SimpleRenderProcessHandler::getInstance()->SetJavascriptBindings(
      m_JavascriptBindings, m_JavascriptPythonBindings);

  CefBrowserSettings browser_settings;

  std::string url;
  url = StartUrl;

  CefWindowInfo window_info;

#if defined(OS_WIN)
  // On Windows we need to specify certain flags that will be passed to
  // CreateWindowEx().
  window_info.SetAsPopup(nullptr, "");
#endif

  CefRefPtr<CefDictionaryValue> extra = CefDictionaryValue::Create();
  if (!m_JavascriptBindings.empty())
  {
    CefRefPtr<CefListValue> bindings = CefListValue::Create();
    bindings->SetSize(m_JavascriptBindings.size());
    int listIndex = 0;
    for (const auto &binding : m_JavascriptBindings) {
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
                  static_cast<int>(m_JavascriptBindings.size()));
  }

  if (!m_JavascriptPythonBindings.empty()) {

    CefRefPtr<CefListValue> bindings = CefListValue::Create();
    bindings->SetSize(m_JavascriptPythonBindings.size());
    int listIndex = 0;
    for (const auto &binding : m_JavascriptPythonBindings) {
      CefRefPtr<CefDictionaryValue> dic = CefDictionaryValue::Create();
      dic->SetString("MessageTopic", binding.MessageTopic);
      dic->SetString("JavascriptObject", binding.JavascriptObject);
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
                  static_cast<int>(m_JavascriptPythonBindings.size()));
  }

  window_info.bounds.width = init_width;
  window_info.bounds.height = init_height;

  Browser = CefBrowserHost::CreateBrowserSync(window_info, handler, url,
                                              browser_settings, extra, nullptr);

  // m_Browser->GetHost()->ShowDevTools(window_info, nullptr, browser_settings,
  // CefPoint());
}
void CefWrapperBrowserProcessHandler::SetStartUrl(std::string url) {
  CefWrapperBrowserProcessHandler::GetInstance()->StartUrl = url;
}
void CefWrapperBrowserProcessHandler::LoadUrl(std::string url) {
  CefWrapperBrowserProcessHandler::GetInstance()
      ->Browser->GetMainFrame()
      ->LoadURL(url);
}
void CefWrapperBrowserProcessHandler::SetInitialResolution(int width,
                                                           int height) {
  GetInstance()->init_width = width;
  GetInstance()->init_height = height;
}
