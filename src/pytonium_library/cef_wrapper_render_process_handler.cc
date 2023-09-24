#include "cef_wrapper_render_process_handler.h"

#include "include/cef_render_process_handler.h"
#include "include/internal/cef_ptr.h"
#include "javascript_binding.h"
#include "javascript_bindings_handler.h"
#include "javascript_python_binding_handler.h"

void SimpleRenderProcessHandler::OnBrowserCreated(
        CefRefPtr<CefBrowser> browser, CefRefPtr<CefDictionaryValue> extra_info)
{
    CEF_REQUIRE_RENDERER_THREAD();

    if (extra_info->HasKey("JavascriptBindings"))
    {
        const CefRefPtr<CefListValue> bindings =
                extra_info->GetList("JavascriptBindings");
        const int size = extra_info->GetInt("JavascriptBindingsSize");

        for (int i = 0; i < size; ++i)
        {
            CefRefPtr<CefDictionaryValue> dic = bindings->GetDictionary(i);
            CefRefPtr<CefBinaryValue> functionPointer =
                    dic->GetBinary("FunctionPointer");

            JavascriptBinding binding;
            binding.functionName = dic->GetString("MessageTopic");
            binding.JavascriptObject = dic->GetString("JavascriptObject");
            functionPointer->GetData(&binding.function,
                                     sizeof(binding.function), 0);

            m_Javascript_Bindings.push_back(binding);
        }
    }

    if (extra_info->HasKey("JavascriptPythonBindings"))
    {
        const CefRefPtr<CefListValue> bindings =
                extra_info->GetList("JavascriptPythonBindings");
        const int size = extra_info->GetInt("JavascriptPythonBindingsSize");

        for (int i = 0; i < size; ++i)
        {
            CefRefPtr<CefDictionaryValue> dic = bindings->GetDictionary(i);
            CefRefPtr<CefBinaryValue> handlerFunc = dic->GetBinary("HandlerFunction");
            CefRefPtr<CefBinaryValue> pythonFunctionObject =
                    dic->GetBinary("PythonFunctionObject");

            JavascriptPythonBinding binding;
            binding.FunctionName = dic->GetString("MessageTopic");
            binding.JavascriptObject = dic->GetString("JavascriptObject");
            handlerFunc->GetData(&binding.HandlerFunction,
                                 sizeof(binding.HandlerFunction), 0);
            pythonFunctionObject->GetData(&binding.PythonCallbackObject,
                                          sizeof(binding.PythonCallbackObject), 0);
            binding.ReturnsValue = dic->GetBool("ReturnsValue");
            m_Javascript_Python_Bindings.push_back(binding);
        }
    }
}

/* Null, because instance will be initialized on demand. */
CefRefPtr<SimpleRenderProcessHandler> SimpleRenderProcessHandler::instance =
        nullptr;

CefRefPtr<SimpleRenderProcessHandler>
SimpleRenderProcessHandler::getInstance()
{
    if (instance == nullptr)
    {
        instance =
                CefRefPtr<SimpleRenderProcessHandler>(new SimpleRenderProcessHandler());
    }

    return instance;
}

void SimpleRenderProcessHandler::SetJavascriptBindings(
        std::vector<JavascriptBinding> javascript_bindings,
        std::vector<JavascriptPythonBinding> javascript_python_bindings)
{
    getInstance()->m_Javascript_Bindings = javascript_bindings;
    getInstance()->m_Javascript_Python_Bindings = javascript_python_bindings;
}

SimpleRenderProcessHandler::SimpleRenderProcessHandler() = default;

void SimpleRenderProcessHandler::OnContextCreated(
        CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
        CefRefPtr<CefV8Context> context)
{
    // CEF_REQUIRE_RENDERER_THREAD();
    // Retrieve the context's window object.
    CefRefPtr<CefV8Value> global = context->GetGlobal();

    CefRefPtr<CefV8Value> pytonium_namespace = CefV8Value::CreateObject(nullptr, nullptr);
    if (!m_Javascript_Bindings.empty())
    {

        m_JavascriptBindingHandler =
                new JavascriptBindingsHandler(m_Javascript_Bindings, browser);
        for (int i = 0; i < (int) m_Javascript_Bindings.size(); ++i)
        {

            if (m_Javascript_Bindings[i].JavascriptObject.empty())
            {
                CefRefPtr<CefV8Value> func = CefV8Value::CreateFunction(
                        m_Javascript_Bindings[i].functionName, m_JavascriptBindingHandler);
                pytonium_namespace->SetValue(m_Javascript_Bindings[i].functionName, func,
                                             V8_PROPERTY_ATTRIBUTE_NONE);
            } else
            {
                CefRefPtr<CefV8Value> func = CefV8Value::CreateFunction(
                        m_Javascript_Bindings[i].functionName, m_JavascriptBindingHandler);
                std::vector<CefString> keys;
                pytonium_namespace->GetKeys(keys);

                if (auto it =
                            std::find(keys.begin(), keys.end(),
                                      m_Javascript_Bindings[i].JavascriptObject);
                        it != keys.end())
                {
                    CefRefPtr<CefV8Value> jsObj = pytonium_namespace->GetValue(
                            m_Javascript_Bindings[i].JavascriptObject);
                    jsObj->SetValue(m_Javascript_Bindings[i].functionName, func,
                                    V8_PROPERTY_ATTRIBUTE_NONE);
                    pytonium_namespace->SetValue(m_Javascript_Bindings[i].JavascriptObject,
                                                 jsObj, V8_PROPERTY_ATTRIBUTE_NONE);
                } else
                {
                    CefRefPtr<CefV8Value> retVal =
                            CefV8Value::CreateObject(nullptr, nullptr);
                    retVal->SetValue(m_Javascript_Bindings[i].functionName, func,
                                     V8_PROPERTY_ATTRIBUTE_NONE);
                    pytonium_namespace->SetValue(m_Javascript_Bindings[i].JavascriptObject,
                                                 retVal, V8_PROPERTY_ATTRIBUTE_NONE);
                }
            }
        }
    }

    if (!m_Javascript_Python_Bindings.empty())
    {
        m_JavascriptPythonBindingHandler = new JavascriptPythonBindingsHandler(
                m_Javascript_Python_Bindings, browser);
        for (int i = 0; i < (int) m_Javascript_Python_Bindings.size(); ++i)
        {
            if (m_Javascript_Python_Bindings[i].JavascriptObject.empty())
            {
                CefRefPtr<CefV8Value> func = CefV8Value::CreateFunction(
                        m_Javascript_Python_Bindings[i].FunctionName, m_JavascriptPythonBindingHandler);
                pytonium_namespace->SetValue(m_Javascript_Python_Bindings[i].FunctionName, func,
                                             V8_PROPERTY_ATTRIBUTE_NONE);
            } else
            {
                CefRefPtr<CefV8Value> func = CefV8Value::CreateFunction(
                        m_Javascript_Python_Bindings[i].FunctionName, m_JavascriptPythonBindingHandler);
                std::vector<CefString> keys;
                pytonium_namespace->GetKeys(keys);

                if (auto it =
                            std::find(keys.begin(), keys.end(),
                                      m_Javascript_Python_Bindings[i].JavascriptObject);
                        it != keys.end())
                {
                    CefRefPtr<CefV8Value> jsObj = pytonium_namespace->GetValue(
                            m_Javascript_Python_Bindings[i].JavascriptObject);
                    jsObj->SetValue(m_Javascript_Python_Bindings[i].FunctionName, func,
                                    V8_PROPERTY_ATTRIBUTE_NONE);
                    pytonium_namespace->SetValue(m_Javascript_Python_Bindings[i].JavascriptObject,
                                                 jsObj, V8_PROPERTY_ATTRIBUTE_NONE);
                } else
                {
                    CefRefPtr<CefV8Value> jsObj =
                            CefV8Value::CreateObject(nullptr, nullptr);
                    jsObj->SetValue(m_Javascript_Python_Bindings[i].FunctionName, func,
                                    V8_PROPERTY_ATTRIBUTE_NONE);
                    pytonium_namespace->SetValue(m_Javascript_Python_Bindings[i].JavascriptObject,
                                                 jsObj, V8_PROPERTY_ATTRIBUTE_NONE);
                }
            }
        }
    }

    global->SetValue("Pytonium", pytonium_namespace, V8_PROPERTY_ATTRIBUTE_NONE);
    frame->ExecuteJavaScript("window.PytoniumReady = true;", frame->GetURL(), 0);
    frame->ExecuteJavaScript("var event = new Event('PytoniumReady'); window.dispatchEvent(event);", frame->GetURL(), 0);
}

bool SimpleRenderProcessHandler::OnProcessMessageReceived(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
                                                          CefProcessId source_process,
                                                          CefRefPtr<CefProcessMessage> message)
{

    const std::string& message_name = message->GetName();

    if(message_name == "return-to-javascript")
    {
        CefRefPtr<CefListValue> argList = message->GetArgumentList();
        int message_id = argList->GetInt(0);
        m_JavascriptPythonBindingHandler->ResolvePromise(message_id, argList->GetValue(1));
    }
    return true;
}
