#ifndef JAVASCRIPT_BINDINGS_HANDLER_H
#define JAVASCRIPT_BINDINGS_HANDLER_H

#include "include/cef_client.h"

#include <list>

#include "include/cef_render_process_handler.h"
#include "include/wrapper/cef_helpers.h"
#include "javascript_binding.h"

class JavascriptBindingsHandler : public CefV8Handler {

public:
  JavascriptBindingsHandler(std::vector<JavascriptBinding> callbacks, CefRefPtr<CefBrowser> browser) {
    m_Javascript_Bindings = callbacks;
    m_Browser = browser;
  };
  virtual bool Execute(const CefString &name, CefRefPtr<CefV8Value> object,
                       const CefV8ValueList &arguments,
                       CefRefPtr<CefV8Value> &retval,
                       CefString &exception) override {

    for (int i = 0; i < m_Javascript_Bindings.size(); ++i) {
      if (name == m_Javascript_Bindings[i].functionName) {

        CefRefPtr<CefProcessMessage> javascript_binding_message =
            CefProcessMessage::Create("javascript-binding");

        CefRefPtr<CefListValue> javascript_binding_message_args =
            javascript_binding_message->GetArgumentList();

        javascript_binding_message_args->SetString(0, m_Javascript_Bindings[i].functionName);

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


    return false;
  }
  CefRefPtr<CefBrowser> m_Browser;
  std::vector<JavascriptBinding> m_Javascript_Bindings;

  IMPLEMENT_REFCOUNTING(JavascriptBindingsHandler);
};
#endif // JAVASCRIPT_BINDINGS_HANDLER_H
