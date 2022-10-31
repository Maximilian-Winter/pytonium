#ifndef JAVASCRIPT_PYTHON_BINDING_HANDLER_H
#define JAVASCRIPT_PYTHON_BINDING_HANDLER_H

#include "include/cef_client.h"

#include <list>

#include "include/cef_render_process_handler.h"
#include "include/wrapper/cef_helpers.h"
#include "javascript_binding.h"

class JavascriptPythonBindingsHandler : public CefV8Handler {

public:
  JavascriptPythonBindingsHandler(std::vector<JavascriptPythonBinding> pythonBindings,
                 CefRefPtr<CefBrowser> browser) {
    m_Browser = browser;
    m_PythonBindings = pythonBindings;
  };
  virtual bool Execute(const CefString &name, CefRefPtr<CefV8Value> object,
                       const CefV8ValueList &arguments,
                       CefRefPtr<CefV8Value> &retval,
                       CefString &exception) override {

    for (int i = 0; i < m_PythonBindings.size(); ++i) {
      if (name == m_PythonBindings[i].MessageTopic) {

        CefRefPtr<CefProcessMessage> javascript_binding_message =
            CefProcessMessage::Create("javascript-python-binding");

        CefRefPtr<CefListValue> javascript_binding_message_args =
            javascript_binding_message->GetArgumentList();

        javascript_binding_message_args->SetString(0, m_PythonBindings[i].MessageTopic);

        CefRefPtr<CefListValue> javascript_args = CefListValue::Create();
        CefRefPtr<CefListValue> javascript_arg_types = CefListValue::Create();

        int jsArgsIndex = 0;

        for (const auto & argument : arguments)
        {
          if(argument->IsInt())
          {
            int value = argument->GetIntValue();
            javascript_args->SetInt(jsArgsIndex, value);
            javascript_arg_types->SetString(jsArgsIndex, "int");
            jsArgsIndex++;
          }
          else if(argument->IsBool())
          {
            bool value = argument->GetBoolValue();
            javascript_args->SetBool(jsArgsIndex, value);
            javascript_arg_types->SetString(jsArgsIndex, "bool");
            jsArgsIndex++;
          }
          else if(argument->IsDouble())
          {
            double value = argument->GetDoubleValue();
            javascript_args->SetDouble(jsArgsIndex, value);
            javascript_arg_types->SetString(jsArgsIndex, "double");
            jsArgsIndex++;
          }
          else if(argument->IsString())
          {
            std::string value = argument->GetStringValue();
            javascript_args->SetString(jsArgsIndex, value);
            javascript_arg_types->SetString(jsArgsIndex, "string");
            jsArgsIndex++;
          }
        }
        javascript_binding_message_args->SetList(1, javascript_arg_types);
        javascript_binding_message_args->SetList(2, javascript_args);
        m_Browser->GetMainFrame()->SendProcessMessage(PID_BROWSER, javascript_binding_message);

        return true;
      }
    }
    // Function does not exist.
    return false;
  }
  CefRefPtr<CefBrowser> m_Browser;
  std::vector<JavascriptPythonBinding> m_PythonBindings;
  // Provide the reference counting implementation for this class.
  IMPLEMENT_REFCOUNTING(JavascriptPythonBindingsHandler);
};
#endif // JAVASCRIPT_PYTHON_BINDING_HANDLER_H
