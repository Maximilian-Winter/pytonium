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

    int id = browser->GetIdentifier();
    auto& state = m_BrowserStates[id];

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

            state.javascriptBindings.push_back(binding);
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
            state.javascriptPythonBindings.push_back(binding);
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

SimpleRenderProcessHandler::SimpleRenderProcessHandler() = default;

PerBrowserRendererState& SimpleRenderProcessHandler::GetState(int browserId)
{
    return m_BrowserStates[browserId];
}

void SimpleRenderProcessHandler::OnBrowserDestroyed(CefRefPtr<CefBrowser> browser)
{
    m_BrowserStates.erase(browser->GetIdentifier());
}

void SimpleRenderProcessHandler::OnContextCreated(
        CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
        CefRefPtr<CefV8Context> context)
{
    // Retrieve the context's window object.
    CefRefPtr<CefV8Value> global = context->GetGlobal();

    CefRefPtr<CefV8Value> pytonium_namespace = CefV8Value::CreateObject(nullptr, nullptr);

    int id = browser->GetIdentifier();
    auto& state = GetState(id);

    state.applicationStateManager = std::make_shared<ApplicationStateManager>();
    state.appStateV8Handler = new AppStateV8Handler(state.applicationStateManager, browser);

    CefRefPtr<CefV8Value> stateObj = CefV8Value::CreateObject(nullptr, nullptr);

    CefRefPtr<CefV8Value> funcRegisterForStateUpdates = CefV8Value::CreateFunction("registerForStateUpdates", state.appStateV8Handler);
    CefRefPtr<CefV8Value> funcSetState = CefV8Value::CreateFunction("setState", state.appStateV8Handler);
    CefRefPtr<CefV8Value> funcGetState = CefV8Value::CreateFunction("getState", state.appStateV8Handler);
    CefRefPtr<CefV8Value> funcRemoveState = CefV8Value::CreateFunction("removeState", state.appStateV8Handler);

    stateObj->SetValue("registerForStateUpdates", funcRegisterForStateUpdates, V8_PROPERTY_ATTRIBUTE_NONE);
    stateObj->SetValue("setState", funcSetState, V8_PROPERTY_ATTRIBUTE_NONE);
    stateObj->SetValue("getState", funcGetState, V8_PROPERTY_ATTRIBUTE_NONE);
    stateObj->SetValue("removeState", funcRemoveState, V8_PROPERTY_ATTRIBUTE_NONE);

    pytonium_namespace->SetValue("appState", stateObj, V8_PROPERTY_ATTRIBUTE_NONE);


    if (!state.javascriptBindings.empty())
    {

        state.javascriptBindingHandler =
                new JavascriptBindingsHandler(state.javascriptBindings, browser);
        for (int i = 0; i < (int) state.javascriptBindings.size(); ++i)
        {

            if (state.javascriptBindings[i].JavascriptObject.empty())
            {
                CefRefPtr<CefV8Value> func = CefV8Value::CreateFunction(
                        state.javascriptBindings[i].functionName, state.javascriptBindingHandler);
                pytonium_namespace->SetValue(state.javascriptBindings[i].functionName, func,
                                             V8_PROPERTY_ATTRIBUTE_NONE);
            } else
            {
                CefRefPtr<CefV8Value> func = CefV8Value::CreateFunction(
                        state.javascriptBindings[i].functionName, state.javascriptBindingHandler);
                std::vector<CefString> keys;
                pytonium_namespace->GetKeys(keys);

                if (auto it =
                            std::find(keys.begin(), keys.end(),
                                      state.javascriptBindings[i].JavascriptObject);
                        it != keys.end())
                {
                    CefRefPtr<CefV8Value> jsObj = pytonium_namespace->GetValue(
                            state.javascriptBindings[i].JavascriptObject);
                    jsObj->SetValue(state.javascriptBindings[i].functionName, func,
                                    V8_PROPERTY_ATTRIBUTE_NONE);
                    pytonium_namespace->SetValue(state.javascriptBindings[i].JavascriptObject,
                                                 jsObj, V8_PROPERTY_ATTRIBUTE_NONE);
                } else
                {
                    CefRefPtr<CefV8Value> retVal =
                            CefV8Value::CreateObject(nullptr, nullptr);
                    retVal->SetValue(state.javascriptBindings[i].functionName, func,
                                     V8_PROPERTY_ATTRIBUTE_NONE);
                    pytonium_namespace->SetValue(state.javascriptBindings[i].JavascriptObject,
                                                 retVal, V8_PROPERTY_ATTRIBUTE_NONE);
                }
            }
        }
    }

    if (!state.javascriptPythonBindings.empty())
    {
        state.javascriptPythonBindingHandler = new JavascriptPythonBindingsHandler(
                state.javascriptPythonBindings, browser);
        for (int i = 0; i < (int) state.javascriptPythonBindings.size(); ++i)
        {
            if (state.javascriptPythonBindings[i].JavascriptObject.empty())
            {
                CefRefPtr<CefV8Value> func = CefV8Value::CreateFunction(
                        state.javascriptPythonBindings[i].FunctionName, state.javascriptPythonBindingHandler);
                pytonium_namespace->SetValue(state.javascriptPythonBindings[i].FunctionName, func,
                                             V8_PROPERTY_ATTRIBUTE_NONE);
            } else
            {
                CefRefPtr<CefV8Value> func = CefV8Value::CreateFunction(
                        state.javascriptPythonBindings[i].FunctionName, state.javascriptPythonBindingHandler);
                std::vector<CefString> keys;
                pytonium_namespace->GetKeys(keys);

                if (auto it =
                            std::find(keys.begin(), keys.end(),
                                      state.javascriptPythonBindings[i].JavascriptObject);
                        it != keys.end())
                {
                    CefRefPtr<CefV8Value> jsObj = pytonium_namespace->GetValue(
                            state.javascriptPythonBindings[i].JavascriptObject);
                    jsObj->SetValue(state.javascriptPythonBindings[i].FunctionName, func,
                                    V8_PROPERTY_ATTRIBUTE_NONE);
                    pytonium_namespace->SetValue(state.javascriptPythonBindings[i].JavascriptObject,
                                                 jsObj, V8_PROPERTY_ATTRIBUTE_NONE);
                } else
                {
                    CefRefPtr<CefV8Value> jsObj =
                            CefV8Value::CreateObject(nullptr, nullptr);
                    jsObj->SetValue(state.javascriptPythonBindings[i].FunctionName, func,
                                    V8_PROPERTY_ATTRIBUTE_NONE);
                    pytonium_namespace->SetValue(state.javascriptPythonBindings[i].JavascriptObject,
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
    int id = browser->GetIdentifier();
    auto& state = GetState(id);

    const std::string& message_name = message->GetName();

    if(message_name == "return-to-javascript")
    {
        CefRefPtr<CefListValue> argList = message->GetArgumentList();
        int message_id = argList->GetInt(0);
        state.javascriptPythonBindingHandler->ResolvePromise(message_id, argList->GetValue(1));
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
            nlohmann::json value = ApplicationStateManagerHelper::cefValueToJson(argList->GetValue(2));

            state.applicationStateManager->setState(namespaceName, key, value);
            state.appStateV8Handler->PushToJavascript(namespaceName, key);
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
            auto appState = state.applicationStateManager->getState(namespaceName, key);

            auto cefState = ApplicationStateManagerHelper::jsonToCefValue(appState);
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
            state.applicationStateManager->removeState(namespaceName, key);

            return true;
        } else {
            return false;
        }
    }
    return true;
}
