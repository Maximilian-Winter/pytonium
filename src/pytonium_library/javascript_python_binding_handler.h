#ifndef JAVASCRIPT_PYTHON_BINDING_HANDLER_H
#define JAVASCRIPT_PYTHON_BINDING_HANDLER_H

#include "include/cef_client.h"

#include <list>
#include <iostream>
#include <chrono>

#include "include/cef_render_process_handler.h"
#include "include/wrapper/cef_helpers.h"
#include "javascript_binding.h"

struct PromiseEntry {
    CefRefPtr<CefV8Context> context;
    CefRefPtr<CefV8Value> promise;
    std::chrono::steady_clock::time_point created;
};

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
        // Clean up any stale promises before processing
        CleanupStalePromises();

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
        CefRefPtr<CefV8Context> context = CefV8Context::GetCurrentContext();
        CefRefPtr<CefV8Value> promise = context->GetGlobal()->CreatePromise();

        PromiseEntry entry;
        entry.context = context;
        entry.promise = promise;
        entry.created = std::chrono::steady_clock::now();
        promiseMap[request_id] = std::move(entry);

        return promise;
    }

    void ResolvePromise(int request_id, const CefRefPtr<CefValue>& value) {
        auto it = promiseMap.find(request_id);
        if (it == promiseMap.end()) {
            return;  // Promise not found — already resolved or invalid ID
        }

        auto& entry = it->second;
        entry.context->Enter();
        entry.promise->ResolvePromise(CefValueWrapperHelper::ConvertCefValueToV8Value(value));
        entry.context->Exit();

        promiseMap.erase(it);
    }

    void CleanupStalePromises(int timeoutSeconds = 30) {
        auto now = std::chrono::steady_clock::now();
        for (auto it = promiseMap.begin(); it != promiseMap.end(); ) {
            auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - it->second.created).count();
            if (elapsed > timeoutSeconds) {
                // Reject the stale promise
                auto& entry = it->second;
                entry.context->Enter();
                entry.promise->RejectPromise("Pytonium: Promise timed out");
                entry.context->Exit();
                it = promiseMap.erase(it);
            } else {
                ++it;
            }
        }
    }

    uint64_t nextRequestId = 0;
    std::unordered_map<uint64_t, PromiseEntry> promiseMap;
    CefRefPtr<CefBrowser> m_Browser;
    std::vector<JavascriptPythonBinding> m_PythonBindings;
    // Provide the reference counting implementation for this class.
IMPLEMENT_REFCOUNTING(JavascriptPythonBindingsHandler);
};

#endif // JAVASCRIPT_PYTHON_BINDING_HANDLER_H
