#ifndef JAVASCRIPT_PYTHON_BINDING_HANDLER_H
#define JAVASCRIPT_PYTHON_BINDING_HANDLER_H

#include "include/cef_client.h"

#include <list>
#include <iostream>

#include "include/cef_render_process_handler.h"
#include "include/wrapper/cef_helpers.h"
#include "javascript_binding.h"


class JavascriptPythonBindingsHandler : public CefV8Handler
{

public:
    JavascriptPythonBindingsHandler(std::vector<JavascriptPythonBinding> pythonBindings,
                                    CefRefPtr<CefBrowser> browser)
    {
        m_Browser = browser;
        m_PythonBindings = pythonBindings;
    };

    bool Execute(const CefString &name, CefRefPtr<CefV8Value> object,
                         const CefV8ValueList &arguments,
                         CefRefPtr<CefV8Value> &retval,
                         CefString &exception) override
    {

        for (int i = 0; i < (int) m_PythonBindings.size(); ++i)
        {
            if (name == m_PythonBindings[i].FunctionName)
            {

                CefRefPtr<CefProcessMessage> javascript_binding_message =
                        CefProcessMessage::Create("javascript-python-binding");

                CefRefPtr<CefListValue> javascript_binding_message_args =
                        javascript_binding_message->GetArgumentList();

                javascript_binding_message_args->SetString(0, m_PythonBindings[i].FunctionName);

                CefRefPtr<CefListValue> javascript_args = CefListValue::Create();
                CefRefPtr<CefListValue> javascript_arg_types = CefListValue::Create();

                int jsArgsIndex = 0;

                for (const auto &argument: arguments)
                {
                    CefValueWrapperHelper::AddJavascriptArg(argument, javascript_args, javascript_arg_types, jsArgsIndex);
                }

                javascript_binding_message_args->SetList(1, javascript_arg_types);
                javascript_binding_message_args->SetList(2, javascript_args);

                if(m_PythonBindings[i].ReturnsValue)
                {
                    int request_id = nextRequestId++;
                    retval = CreatePromise(request_id);

                    //promiseMap[request_id]->ResolvePromise(arguments[0]);
                    // Modify the message to include request_id
                    javascript_binding_message_args->SetInt(3, request_id);
                }
                else
                {
                    javascript_binding_message_args->SetInt(3, -1);
                }

                m_Browser->GetMainFrame()->SendProcessMessage(PID_BROWSER, javascript_binding_message);

                return true;
            }
        }
        // Function does not exist.
        return false;
    }
    CefRefPtr<CefV8Value> CreatePromise(int request_id) {
        // Create a new Promise and return it
        CefRefPtr<CefV8Context> context = CefV8Context::GetCurrentContext();

        // Create a new Promise object
        CefRefPtr<CefV8Value> promise = context->GetGlobal()->CreatePromise();

        // Store the promise object for later reference using request_id
        promiseMap[request_id] = std::make_pair(context, promise);

        return promise;
    }

    void ResolvePromise(int request_id, const CefRefPtr<CefValue>& value) {
        std::pair<CefRefPtr<CefV8Context>, CefRefPtr<CefV8Value>> pair = promiseMap[request_id];

        pair.first->Enter();
        pair.second->ResolvePromise(CefValueWrapperHelper::ConvertCefValueToV8Value(value));
        pair.first->Exit();

        promiseMap.erase(request_id);
    }
    uint64_t nextRequestId = 0;
    std::unordered_map<uint64_t, std::pair<CefRefPtr<CefV8Context>, CefRefPtr<CefV8Value>>> promiseMap;
    CefRefPtr<CefBrowser> m_Browser;
    std::vector<JavascriptPythonBinding> m_PythonBindings;
    // Provide the reference counting implementation for this class.
IMPLEMENT_REFCOUNTING(JavascriptPythonBindingsHandler);
};

#endif // JAVASCRIPT_PYTHON_BINDING_HANDLER_H
