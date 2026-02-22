//
// Created by maxim on 24.09.2023.
//


#ifndef PYTONIUM_APPLICATION_STATE_JAVASCRIPT_HANDLER_H
#define PYTONIUM_APPLICATION_STATE_JAVASCRIPT_HANDLER_H
#include "include/cef_client.h"

#include <list>

#include "include/cef_render_process_handler.h"
#include "include/wrapper/cef_helpers.h"
#include "application_state_manager.h"
#include "Logging.h"
#include <iostream>
#include <fstream>
#include <string>
#include <utility>

inline std::string EscapeJsString(const std::string& input) {
    std::string result;
    result.reserve(input.size() + 8);
    for (char c : input) {
        switch (c) {
            case '\\': result += "\\\\"; break;
            case '\'': result += "\\'"; break;
            case '"':  result += "\\\""; break;
            case '\n': result += "\\n"; break;
            case '\r': result += "\\r"; break;
            case '\0': result += "\\0"; break;
            case '<':  result += "\\x3C"; break;
            case '>':  result += "\\x3E"; break;
            default:   result += c; break;
        }
    }
    return result;
}

class JavascriptStateUpdateSubscription
{
public:
    std::string EventName;
    std::vector<std::string> NameSpaces;
    bool UpdatesFromJavascript;
    bool UpdatesFromPython;
};
class AppStateV8Handler : public CefV8Handler {
private:
    std::shared_ptr<ApplicationStateManager> m_ApplicationStateManager;
    CefRefPtr<CefBrowser> m_Browser;
    std::string jsTriggerCustomEvent;
    bool JavascriptIsRegisteredForStateEvents;
    std::vector<JavascriptStateUpdateSubscription> StateUpdateSubscriptions;
public:
    AppStateV8Handler(std::shared_ptr<ApplicationStateManager>  manager, CefRefPtr<CefBrowser> browser) : m_ApplicationStateManager(std::move(manager)), m_Browser(std::move(browser))
    {
        jsTriggerCustomEvent = R"(
    if (typeof triggerCustomStateChangePytoniumEvent === 'undefined') {
        function triggerCustomStateChangePytoniumEvent(eventName, detail) {
            const event = new CustomEvent(eventName, { detail });
            document.dispatchEvent(event);
        }
    }
)";
        JavascriptIsRegisteredForStateEvents = false;
    }

    bool Execute(const CefString& name,
                         CefRefPtr<CefV8Value> object,
                         const CefV8ValueList& arguments,
                         CefRefPtr<CefV8Value>& retval,
                         CefString& exception) override {
        if (name == "setState") {
            if (arguments.size() == 3 && arguments[0]->IsString() && arguments[1]->IsString()) {
                std::string namespaceName = arguments[0]->GetStringValue().ToString();
                std::string key = arguments[1]->GetStringValue().ToString();
                nlohmann::json value = ApplicationStateManagerHelper::cefV8ValueToJson(arguments[2]);  // Assuming you have implemented this function

                m_ApplicationStateManager->setState(namespaceName, key, value);

                auto cefState = ApplicationStateManagerHelper::jsonToCefValue(value);
                CefRefPtr<CefProcessMessage> messageReturn =
                        CefProcessMessage::Create("push-app-state-update");

                CefRefPtr<CefListValue> message_args_return =
                        messageReturn->GetArgumentList();

                message_args_return->SetSize(3);
                message_args_return->SetString(0, namespaceName);
                message_args_return->SetString(1, key);
                message_args_return->SetValue(2, cefState);
                m_Browser->GetMainFrame()->SendProcessMessage(PID_BROWSER, messageReturn);
                PushToJavascript(namespaceName, key, true);
                return true;
            } else {
                exception = "Invalid arguments for setState";
                return false;
            }
        } else if (name == "getState") {
            if (arguments.size() == 2 && arguments[0]->IsString() && arguments[1]->IsString()) {
                std::string namespaceName = arguments[0]->GetStringValue().ToString();
                std::string key = arguments[1]->GetStringValue().ToString();

                nlohmann::json value = m_ApplicationStateManager->getState(namespaceName, key);
                retval = ApplicationStateManagerHelper::jsonToCefV8Value(value);  // Assuming you have implemented this function
                return true;
            } else {
                exception = "Invalid arguments for getState";
                return false;
            }
        } else if (name == "removeState") {
            if (arguments.size() == 2 && arguments[0]->IsString() && arguments[1]->IsString()) {
                std::string namespaceName = arguments[0]->GetStringValue().ToString();
                std::string key = arguments[1]->GetStringValue().ToString();

                m_ApplicationStateManager->removeState(namespaceName, key);
                return true;
            } else {
                exception = "Invalid arguments for removeState";
                return false;
            }
        } else if (name == "registerForStateUpdates") {
            if(arguments.size() == 4 && arguments[0]->IsString() && arguments[1]->IsArray( )&& arguments[2]->IsBool() && arguments[3]->IsBool())
            {
                std::string eventName = arguments[0]->GetStringValue().ToString();
                std::vector<std::string> namespaces;

                for (int i = 0; i < arguments[1]->GetArrayLength(); ++i)
                {
                    if(arguments[1]->GetValue(i)->IsString())
                    {
                        namespaces.emplace_back(arguments[1]->GetValue(i)->GetStringValue().ToString());
                    }
                    else
                    {
                        exception = "Invalid arguments for namespaces for registerForStateUpdates";
                        return false;
                    }
                }

                StateUpdateSubscriptions.emplace_back(eventName, namespaces, arguments[2]->GetBoolValue(), arguments[3]->GetBoolValue());

                RegisterJavascriptForStateUpdateEvent();

                return true;
            }else {
                exception = "Invalid arguments for registerForStateUpdates";
                return false;
            }

        }

        return false;
    }

    void RegisterJavascriptForStateUpdateEvent()
    {
        std::string jsCode = jsTriggerCustomEvent;

        // Execute the JavaScript code
        m_Browser->GetMainFrame()->ExecuteJavaScript(jsCode, m_Browser->GetMainFrame()->GetURL(), 0);
        JavascriptIsRegisteredForStateEvents = true;
    }


    void PushToJavascript(const std::string& stateNamespace, const std::string& key, bool fromJavascript = false)
    {
        if(JavascriptIsRegisteredForStateEvents)
        {
            for (const auto& registration: StateUpdateSubscriptions)
            {
                for (const auto& stateSpace: registration.NameSpaces)
                {
                    if(stateSpace == stateNamespace && fromJavascript && registration.UpdatesFromJavascript)
                    {
                        FireEvent(stateNamespace, key, registration.EventName);
                        break;
                    }
                    else if(stateSpace == stateNamespace && !fromJavascript && registration.UpdatesFromPython)
                    {
                        FireEvent(stateNamespace, key, registration.EventName);
                        break;
                    }
                }
            }

        }
    }


    void FireEvent(const std::string& stateNamespace, const std::string& stateName, const std::string& eventName)
    {
        // Serialize the updated state (or namespace) to JSON string
        auto state = m_ApplicationStateManager->getState(stateNamespace, stateName);
        std::string serialisedState = state.dump();  // json::dump() output is already safe for JS embedding
        // Construct JavaScript code to trigger custom event — escape user-controlled strings
        std::stringstream jsCodeStream;
        jsCodeStream << "triggerCustomStateChangePytoniumEvent('" << EscapeJsString(eventName) << "', {";
        jsCodeStream << "'namespace': '" << EscapeJsString(stateNamespace) << "', ";
        jsCodeStream << "'key': '" << EscapeJsString(stateName) << "', ";
        jsCodeStream << "'value': " << serialisedState;
        jsCodeStream << "});";

        std::string jsCode = jsCodeStream.str();

        // Execute the JavaScript code
        m_Browser->GetMainFrame()->ExecuteJavaScript(jsCode, m_Browser->GetMainFrame()->GetURL(), 0);
    }
    IMPLEMENT_REFCOUNTING(AppStateV8Handler);
};
#endif //PYTONIUM_APPLICATION_STATE_JAVASCRIPT_HANDLER_H
