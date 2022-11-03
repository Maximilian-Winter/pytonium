#include "cef_wrapper_render_process_handler.h"

#include "include/cef_render_process_handler.h"
#include "include/internal/cef_ptr.h"
#include "javascript_binding.h"
#include "javascript_bindings_handler.h"
#include "javascript_python_binding_handler.h"

void SimpleRenderProcessHandler::OnBrowserCreated(
    CefRefPtr<CefBrowser> browser, CefRefPtr<CefDictionaryValue> extra_info) {
  CEF_REQUIRE_RENDERER_THREAD();

  if (extra_info->HasKey("JavascriptBindings")) {
    const CefRefPtr<CefListValue> bindings =
        extra_info->GetList("JavascriptBindings");
    const int size = extra_info->GetInt("JavascriptBindingsSize");

    for (int i = 0; i < size; ++i) {
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

  if (extra_info->HasKey("JavascriptPythonBindings")) {
    const CefRefPtr<CefListValue> bindings =
        extra_info->GetList("JavascriptPythonBindings");
    const int size = extra_info->GetInt("JavascriptPythonBindingsSize");

    for (int i = 0; i < size; ++i) {
      CefRefPtr<CefDictionaryValue> dic = bindings->GetDictionary(i);
      CefRefPtr<CefBinaryValue> handlerFunc = dic->GetBinary("HandlerFunction");
      CefRefPtr<CefBinaryValue> pythonFunctionObject =
          dic->GetBinary("PythonFunctionObject");

      JavascriptPythonBinding binding;
      binding.MessageTopic = dic->GetString("MessageTopic");
      binding.JavascriptObject = dic->GetString("JavascriptObject");
      handlerFunc->GetData(&binding.HandlerFunction,
                           sizeof(binding.HandlerFunction), 0);
      pythonFunctionObject->GetData(&binding.PythonCallbackObject,
                                    sizeof(binding.PythonCallbackObject), 0);

      m_Javascript_Python_Bindings.push_back(binding);
    }
  }
}
/* Null, because instance will be initialized on demand. */
CefRefPtr<SimpleRenderProcessHandler> SimpleRenderProcessHandler::instance =
    nullptr;

CefRefPtr<SimpleRenderProcessHandler>
SimpleRenderProcessHandler::getInstance() {
  if (instance == nullptr) {
    instance =
        CefRefPtr<SimpleRenderProcessHandler>(new SimpleRenderProcessHandler());
  }

  return instance;
}

void SimpleRenderProcessHandler::SetJavascriptBindings(
    std::vector<JavascriptBinding> javascript_bindings,
    std::vector<JavascriptPythonBinding> javascript_python_bindings) {
  getInstance()->m_Javascript_Bindings = javascript_bindings;
  getInstance()->m_Javascript_Python_Bindings = javascript_python_bindings;
}

SimpleRenderProcessHandler::SimpleRenderProcessHandler() = default;

void SimpleRenderProcessHandler::OnContextCreated(
    CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
    CefRefPtr<CefV8Context> context) {
  // CEF_REQUIRE_RENDERER_THREAD();

  if (!m_Javascript_Bindings.empty()) {
    // Retrieve the context's window object.
    CefRefPtr<CefV8Value> object = context->GetGlobal();
    CefRefPtr<CefV8Handler> handler =
        new JavascriptBindingsHandler(m_Javascript_Bindings, browser);
    for (int i = 0; i < (int)m_Javascript_Bindings.size(); ++i) {

      if (m_Javascript_Bindings[i].JavascriptObject.empty()) {
        CefRefPtr<CefV8Value> func = CefV8Value::CreateFunction(
            m_Javascript_Bindings[i].functionName, handler);
        object->SetValue(m_Javascript_Bindings[i].functionName, func,
                         V8_PROPERTY_ATTRIBUTE_NONE);
      } else {
        CefRefPtr<CefV8Value> func = CefV8Value::CreateFunction(
            m_Javascript_Bindings[i].functionName, handler);
        std::vector<CefString> keys;
        object->GetKeys(keys);

        if (auto it =
                std::find(keys.begin(), keys.end(),
                          m_Javascript_Bindings[i].JavascriptObject);
            it != keys.end()) {
          CefRefPtr<CefV8Value> jsObj = object->GetValue(
              m_Javascript_Bindings[i].JavascriptObject);
          jsObj->SetValue(m_Javascript_Bindings[i].functionName, func,
                          V8_PROPERTY_ATTRIBUTE_NONE);
          object->SetValue(m_Javascript_Bindings[i].JavascriptObject,
                           jsObj, V8_PROPERTY_ATTRIBUTE_NONE);
        } else {
          CefRefPtr<CefV8Value> retVal =
              CefV8Value::CreateObject(nullptr, nullptr);
          retVal->SetValue(m_Javascript_Bindings[i].functionName, func,
                           V8_PROPERTY_ATTRIBUTE_NONE);
          object->SetValue(m_Javascript_Bindings[i].JavascriptObject,
                           retVal, V8_PROPERTY_ATTRIBUTE_NONE);
        }
      }
    }
  }

  if (!m_Javascript_Python_Bindings.empty()) {
    // Retrieve the context's window object.
    CefRefPtr<CefV8Value> object = context->GetGlobal();
    CefRefPtr<CefV8Handler> handler = new JavascriptPythonBindingsHandler(
        m_Javascript_Python_Bindings, browser);
    for (int i = 0; i < (int)m_Javascript_Python_Bindings.size(); ++i) {
      if (m_Javascript_Python_Bindings[i].JavascriptObject.empty()) {
        CefRefPtr<CefV8Value> func = CefV8Value::CreateFunction(
            m_Javascript_Python_Bindings[i].MessageTopic, handler);
        object->SetValue(m_Javascript_Python_Bindings[i].MessageTopic, func,
                         V8_PROPERTY_ATTRIBUTE_NONE);
      } else {
        CefRefPtr<CefV8Value> func = CefV8Value::CreateFunction(
            m_Javascript_Python_Bindings[i].MessageTopic, handler);
        std::vector<CefString> keys;
        object->GetKeys(keys);

        if (auto it =
                std::find(keys.begin(), keys.end(),
                          m_Javascript_Python_Bindings[i].JavascriptObject);
            it != keys.end()) {
          CefRefPtr<CefV8Value> jsObj = object->GetValue(
              m_Javascript_Python_Bindings[i].JavascriptObject);
          jsObj->SetValue(m_Javascript_Python_Bindings[i].MessageTopic, func,
                          V8_PROPERTY_ATTRIBUTE_NONE);
          object->SetValue(m_Javascript_Python_Bindings[i].JavascriptObject,
                           jsObj, V8_PROPERTY_ATTRIBUTE_NONE);
        } else {
          CefRefPtr<CefV8Value> retVal =
              CefV8Value::CreateObject(nullptr, nullptr);
          retVal->SetValue(m_Javascript_Python_Bindings[i].MessageTopic, func,
                           V8_PROPERTY_ATTRIBUTE_NONE);
          object->SetValue(m_Javascript_Python_Bindings[i].JavascriptObject,
                           retVal, V8_PROPERTY_ATTRIBUTE_NONE);
        }
      }
    }
  }
}
