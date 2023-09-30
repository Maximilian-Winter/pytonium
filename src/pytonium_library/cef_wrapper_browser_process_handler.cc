

#include "cef_wrapper_browser_process_handler.h"

#include <utility>
#include "cef_wrapper_client_handler.h"
#include "cef_wrapper_render_process_handler.h"
#include "custom_protocol_scheme_handler.h"
#include "javascript_binding.h"
#include "cef_value_wrapper.h"


CefWrapperBrowserProcessHandler::CefWrapperBrowserProcessHandler() = default;

/* Null, because instance will be initialized on demand. */
CefRefPtr<CefWrapperBrowserProcessHandler>
        CefWrapperBrowserProcessHandler::instance = nullptr;

CefRefPtr<CefWrapperBrowserProcessHandler>
CefWrapperBrowserProcessHandler::GetInstance()
{
    if (instance == nullptr)
    {
        instance = CefRefPtr<CefWrapperBrowserProcessHandler>(
                new CefWrapperBrowserProcessHandler());
        instance->init_width = 1024;
        instance->init_height = 768;
    }

    return instance;
}

void CefWrapperBrowserProcessHandler::SetJavascriptBindings(
        std::vector<JavascriptBinding> javascript_bindings,
        std::vector<JavascriptPythonBinding> javascript_python_bindings,
        std::vector<StateHandlerPythonBinding> stateHandlerPythonBindings,
        std::vector<ContextMenuBinding> contextMenuBindings,
        std::vector<CefCustomScheme> customSchemes, std::unordered_map<std::string, std::string> mimeTypeMap)
{
    GetInstance()->m_JavascriptBindings = std::move(javascript_bindings);
    GetInstance()->m_JavascriptPythonBindings = std::move(javascript_python_bindings);
    GetInstance()->m_StateHandlerPythonBindings = std::move(stateHandlerPythonBindings);
    GetInstance()->m_ContextMenuBindings = std::move(contextMenuBindings);
    GetInstance()->m_CustomSchemes = std::move(customSchemes);
    GetInstance()->m_MimeTypeMap = std::move(mimeTypeMap);
    if (GetInstance()->GetDefaultClient() != nullptr)
    {
        CefWrapperClientHandler* client = static_cast<CefWrapperClientHandler*>(GetInstance()->GetDefaultClient().get());

        client->SetContextMenuBindings(GetInstance()->m_ContextMenuBindings);
    }

}

CefRefPtr<CefClient> CefWrapperBrowserProcessHandler::GetDefaultClient()
{
    return CefWrapperClientHandler::GetInstance();
}

void CefWrapperBrowserProcessHandler::OnContextInitialized()
{
    CEF_REQUIRE_UI_THREAD();

    CefRefPtr<CefCommandLine> command_line =
            CefCommandLine::GetGlobalCommandLine();

    bool use_views = command_line->HasSwitch("use-views");

    RegisterSchemeHandlerFactory(m_CustomSchemes, m_MimeTypeMap);

    CefRefPtr<CefWrapperClientHandler> handler(new CefWrapperClientHandler(
            use_views, m_JavascriptBindings, m_JavascriptPythonBindings, m_StateHandlerPythonBindings, m_ContextMenuBindings));
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
        for (const auto &binding: m_JavascriptBindings)
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
                      static_cast<int>(m_JavascriptBindings.size()));
    }

    if (!m_JavascriptPythonBindings.empty())
    {

        CefRefPtr<CefListValue> bindings = CefListValue::Create();
        bindings->SetSize(m_JavascriptPythonBindings.size());
        int listIndex = 0;
        for (const auto &binding: m_JavascriptPythonBindings)
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
                      static_cast<int>(m_JavascriptPythonBindings.size()));
    }

    window_info.bounds.width = init_width;
    window_info.bounds.height = init_height;

    Browser = CefBrowserHost::CreateBrowserSync(window_info, handler, url,
                                                browser_settings, extra, nullptr);

    // m_Browser->GetHost()->ShowDevTools(window_info, nullptr, browser_settings,
    // CefPoint());
}

void CefWrapperBrowserProcessHandler::SetStartUrl(std::string url)
{
    CefWrapperBrowserProcessHandler::GetInstance()->StartUrl = url;
}

void CefWrapperBrowserProcessHandler::LoadUrl(std::string url)
{
    CefWrapperBrowserProcessHandler::GetInstance()
            ->Browser->GetMainFrame()
            ->LoadURL(url);
}

void CefWrapperBrowserProcessHandler::SetInitialResolution(int width,
                                                           int height)
{
    GetInstance()->init_width = width;
    GetInstance()->init_height = height;
}

void CefWrapperBrowserProcessHandler::SendReturnValueToJavascript(int message_id, CefValueWrapper returnValue)
{

}
