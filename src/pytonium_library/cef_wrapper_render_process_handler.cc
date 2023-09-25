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

    m_ApplicationStateManager = std::make_unique<ApplicationStateManager>();
    m_AppStateV8Handler = new AppStateV8Handler(m_ApplicationStateManager, browser);

    CefRefPtr<CefV8Value> stateObj = CefV8Value::CreateObject(nullptr, nullptr);

    CefRefPtr<CefV8Value> funcSetState = CefV8Value::CreateFunction("setState", m_AppStateV8Handler);
    CefRefPtr<CefV8Value> funcGetState = CefV8Value::CreateFunction("getState", m_AppStateV8Handler);
    CefRefPtr<CefV8Value> funcRemoveState = CefV8Value::CreateFunction("removeState", m_AppStateV8Handler);


    stateObj->SetValue("setState", funcSetState, V8_PROPERTY_ATTRIBUTE_NONE);
    stateObj->SetValue("getState", funcGetState, V8_PROPERTY_ATTRIBUTE_NONE);
    stateObj->SetValue("removeState", funcRemoveState, V8_PROPERTY_ATTRIBUTE_NONE);

    pytonium_namespace->SetValue("appState", stateObj, V8_PROPERTY_ATTRIBUTE_NONE);


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
    m_ApplicationStateManager = std::make_shared<ApplicationStateManager>();
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
    else if(message_name == "set-app-state")
    {
        CefRefPtr<CefListValue> argList = message->GetArgumentList();
        if (argList->GetSize() == 3 ) {
            std::string namespaceName = argList->GetValue(0)->GetType() == VTYPE_STRING ? argList->GetValue(0)->GetString() : "";
            std::string key = argList->GetValue(1)->GetType() == VTYPE_STRING ? argList->GetValue(1)->GetString() : "";
            if(namespaceName.empty() || key.empty())
            {
                return false;
            }
            nlohmann::json value = ApplicationStateManagerHelper::cefValueToJson(argList->GetValue(2));  // Assuming you have implemented this function
            m_ApplicationStateManager->setState(namespaceName, key, value);
            return true;
        } else {
            return false;
        }
    }
    else if(message_name == "get-app-state")
    {
        CefRefPtr<CefListValue> argList = message->GetArgumentList();
        if (argList->GetSize() == 2 ) {
            std::string namespaceName = argList->GetValue(0)->GetType() == VTYPE_STRING ? argList->GetValue(0)->GetString() : "";
            std::string key = argList->GetValue(1)->GetType() == VTYPE_STRING ? argList->GetValue(1)->GetString() : "";
            if(namespaceName.empty() || key.empty())
            {
                return false;
            }
            auto state = m_ApplicationStateManager->getState(namespaceName, key);

            auto cefState = ApplicationStateManagerHelper::jsonToCefValue(state);
            CefRefPtr<CefProcessMessage> messageReturn =
                    CefProcessMessage::Create("get-app-state-return");

            CefRefPtr<CefListValue> message_args_return =
                    messageReturn->GetArgumentList();

            message_args_return->SetSize(3);
            message_args_return->SetString(0, namespaceName);
            message_args_return->SetString(1, key);
            message_args_return->SetValue(2, cefState);
            frame->SendProcessMessage(PID_BROWSER, messageReturn);
            return true;
        } else {
            return false;
        }
    }
    else if(message_name == "remove-app-state")
    {
        CefRefPtr<CefListValue> argList = message->GetArgumentList();
        if (argList->GetSize() == 2 ) {
            std::string namespaceName = argList->GetValue(0)->GetType() == VTYPE_STRING ? argList->GetValue(0)->GetString() : "";
            std::string key = argList->GetValue(1)->GetType() == VTYPE_STRING ? argList->GetValue(1)->GetString() : "";
            if(namespaceName.empty() || key.empty())
            {
                return false;
            }
            m_ApplicationStateManager->removeState(namespaceName, key);

            return true;
        } else {
            return false;
        }
    }
    return true;
}
