//
// Created by maxim on 24.09.2023.
//
#include "include/cef_client.h"

#include <list>

#include "include/cef_render_process_handler.h"
#include "include/wrapper/cef_helpers.h"
#include "application_state_manager.h"
#ifndef PYTONIUM_APPLICATION_STATE_JAVASCRIPT_HANDLER_H
#define PYTONIUM_APPLICATION_STATE_JAVASCRIPT_HANDLER_H

#include <iostream>
#include <fstream>
#include <string>

class Logging {
public:
    // Constructor
    Logging(const std::string &path) : log_file_path(path) {
        // Open the file in append mode
        log_stream.open(log_file_path, std::ios::app);
        if (!log_stream.is_open()) {
            std::cerr << "Failed to open log file: " << log_file_path << std::endl;
        }
    }

    // Destructor
    ~Logging() {
        if (log_stream.is_open()) {
            log_stream.close();
        }
    }

    // Append a log message to the file
    void appendLog(const std::string &message) {
        if (log_stream.is_open()) {
            log_stream << message << std::endl;
        } else {
            std::cerr << "Log stream is not open. Could not log message." << std::endl;
        }
    }

private:
    std::string log_file_path;
    std::ofstream log_stream;
};


class AppStateV8Handler : public CefV8Handler {
private:
    std::shared_ptr<ApplicationStateManager> m_ApplicationStateManager;
    CefRefPtr<CefBrowser> m_Browser;
public:
    AppStateV8Handler(std::shared_ptr<ApplicationStateManager>  manager, CefRefPtr<CefBrowser> browser) : m_ApplicationStateManager(manager), m_Browser(browser), logging("test_v8.txt") {}

    virtual bool Execute(const CefString& name,
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
        }
        // Handle other methods as needed

        return false;
    }
    Logging logging;
    IMPLEMENT_REFCOUNTING(AppStateV8Handler);
};
#endif //PYTONIUM_APPLICATION_STATE_JAVASCRIPT_HANDLER_H
