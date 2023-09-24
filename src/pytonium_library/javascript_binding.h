#ifndef JAVASCRIPT_BINDING_H
#define JAVASCRIPT_BINDING_H

#include "include/cef_client.h"
#include "include/cef_render_process_handler.h"
#include "include/wrapper/cef_helpers.h"
#include <list>
#include <utility>
#include <string>
#include <vector>
#include <iostream>
#include <sstream>
#include <cmath>
#include <map>

class CefValueWrapper
{
public:
    enum ValueType
    {
        TYPE_INT,
        TYPE_BOOL,
        TYPE_DOUBLE,
        TYPE_STRING,
        TYPE_OBJECT,
        TYPE_BINARY,
        TYPE_LIST,
        TYPE_NULL,
        TYPE_INVALID,
        TYPE_UNDEFINED
    };

    CefValueWrapper()
            : Type(TYPE_UNDEFINED), IntValue(0), BoolValue(false), DoubleValue(0.0), StringValue("")
    {
    }

    // Checkers
    bool IsInt()
    { return Type == TYPE_INT; }

    bool IsBool()
    { return Type == TYPE_BOOL; }

    bool IsDouble()
    { return Type == TYPE_DOUBLE; }

    bool IsString()
    { return Type == TYPE_STRING; }

    bool IsObject()
    { return Type == TYPE_OBJECT; }

    bool IsList()
    { return Type == TYPE_LIST; }


    // Getters
    int GetInt()
    { return IntValue; }

    bool GetBool()
    { return BoolValue; }

    double GetDouble()
    { return DoubleValue; }

    std::string GetString()
    { return StringValue; }

    std::map<std::string, CefValueWrapper> GetObject_()
    { return ObjectValue; }

    // Setters
    void SetInt(int value)
    {
        IntValue = value;
        Type = TYPE_INT;
    }

    void SetBool(bool value)
    {
        BoolValue = value;
        Type = TYPE_BOOL;
    }

    void SetDouble(double value)
    {
        DoubleValue = value;
        Type = TYPE_DOUBLE;
    }

    void SetString(const std::string &value)
    {
        StringValue = value;
        Type = TYPE_STRING;
    }

    void SetObject(const std::map<std::string, CefValueWrapper> &value)
    {
        ObjectValue = value;
        Type = TYPE_OBJECT;
    }

    void SetBinary(std::vector<char> &value)
    {
        BinaryValue = value;
        Type = TYPE_BINARY;
    }

    void SetList(std::vector<CefValueWrapper> &value)
    {
        ListValue = value;
        Type = TYPE_LIST;
    }

    void SetNull()
    { Type = TYPE_NULL; }

    void SetInvalid()
    { Type = TYPE_INVALID; }

    std::vector<char> GetBinary()
    { return BinaryValue; }

    std::vector<CefValueWrapper> GetList()
    { return ListValue; }

    ValueType Type;

private:
    int IntValue;
    bool BoolValue;
    double DoubleValue;
    std::string StringValue;
    std::map<std::string, CefValueWrapper> ObjectValue;
    std::vector<char> BinaryValue;
    std::vector<CefValueWrapper> ListValue;
};

using js_python_callback_object_ptr = void (*);
using js_python_bindings_handler_function_ptr = void (*)(void *python_callback_object, int argsSize,
                                                         CefValueWrapper *callback_args, int message_id);
using js_binding_function_ptr = void (*)(int argsSize, CefValueWrapper *callback_args);

class JavascriptPythonBinding
{
public:
    js_python_bindings_handler_function_ptr HandlerFunction;
    std::string MessageTopic;
    js_python_callback_object_ptr PythonCallbackObject;
    std::string JavascriptObject;

    JavascriptPythonBinding()
    {
    }

    JavascriptPythonBinding(void (*handlerFunction)(void *, int, CefValueWrapper *, int),
                            std::string messageTopic,
                            void *pythonCallbackObject, std::string javascriptObject = "")
            : HandlerFunction(handlerFunction), MessageTopic(std::move(messageTopic)),
              PythonCallbackObject(pythonCallbackObject), JavascriptObject(std::move(javascriptObject))
    {
    }

    void CallHandler(int argsSize, CefValueWrapper *args, int message_id) const
    {
        HandlerFunction(PythonCallbackObject, argsSize, args, message_id);
    }

};

class JavascriptPythonEventBinding : public JavascriptPythonBinding
{
public:
    std::string EventName;
    std::string ElementID;

    JavascriptPythonEventBinding()
    {
    }

    JavascriptPythonEventBinding(void (*handlerFunction)(void *, int, CefValueWrapper *, int),
                                 std::string messageTopic,
                                 void *pythonCallbackObject,
                                 std::string eventName,
                                 std::string elementID)
            : JavascriptPythonBinding(handlerFunction, std::move(messageTopic), pythonCallbackObject),
              EventName(std::move(eventName)), ElementID(std::move(elementID))
    {}
};

class JavascriptBinding
{
public:
    JavascriptBinding()
    {
    }

    JavascriptBinding(std::string name, js_binding_function_ptr pFunction, std::string javascriptObject = "")
    {
        functionName = std::move(name);
        function = pFunction;
        JavascriptObject = std::move(javascriptObject);
    }

    std::string functionName;
    std::string JavascriptObject;
    js_binding_function_ptr function;
};

class CefValueWrapperHelper
{
public:


    constexpr static const char base64_chars[] =
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789+/";

    static std::string Base64Encode(const std::vector<char> &data)
    {
        std::string encoded_string;
        int val = 0, valb = -6;
        for (char c: data)
        {
            val = (val << 8) + c;
            valb += 8;
            while (valb >= 0)
            {
                encoded_string.push_back(base64_chars[(val >> valb) & 0x3F]);
                valb -= 6;
            }
        }
        if (valb > -6)
        {
            encoded_string.push_back(base64_chars[((val << 8) >> (valb + 8)) & 0x3F]);
        }
        while (encoded_string.size() % 4)
        {
            encoded_string.push_back('=');
        }
        return encoded_string;
    }


    static CefRefPtr<CefV8Value> ConvertCefValueToV8Value(const CefRefPtr<CefValue> &cefValue)
    {
        CefRefPtr<CefV8Value> v8Value;

        switch (cefValue->GetType())
        {
            case VTYPE_INT:
                v8Value = CefV8Value::CreateInt(cefValue->GetInt());
                break;

            case VTYPE_BOOL:
                v8Value = CefV8Value::CreateBool(cefValue->GetBool());
                break;

            case VTYPE_DOUBLE:
                v8Value = CefV8Value::CreateDouble(cefValue->GetDouble());
                break;

            case VTYPE_STRING:
                v8Value = CefV8Value::CreateString(cefValue->GetString());
                break;

            case VTYPE_BINARY:
            {
                CefRefPtr<CefBinaryValue> binaryValue = cefValue->GetBinary();
                size_t size = binaryValue->GetSize();
                std::vector<char> data(size);
                binaryValue->GetData(&data[0], size, 0);

                // Convert binary data to a Base64 string
                std::string base64String = Base64Encode(data);

                // Create a V8 string value from the Base64 string
                v8Value = CefV8Value::CreateString(base64String);
                break;
            }

            case VTYPE_DICTIONARY:
            {
                v8Value = CefV8Value::CreateObject(nullptr, nullptr);
                CefRefPtr<CefDictionaryValue> dictValue = cefValue->GetDictionary();
                CefDictionaryValue::KeyList keys;
                dictValue->GetKeys(keys);

                for (const auto &key: keys)
                {
                    CefRefPtr<CefValue> value = dictValue->GetValue(key);
                    v8Value->SetValue(key, ConvertCefValueToV8Value(value), V8_PROPERTY_ATTRIBUTE_NONE);
                }
                break;
            }

            case VTYPE_LIST:
            {
                v8Value = CefV8Value::CreateArray(static_cast<int>(cefValue->GetList()->GetSize()));
                CefRefPtr<CefListValue> listValue = cefValue->GetList();

                for (size_t i = 0; i < listValue->GetSize(); ++i)
                {
                    CefRefPtr<CefValue> value = listValue->GetValue(i);
                    v8Value->SetValue(static_cast<int>(i), ConvertCefValueToV8Value(value));
                }
                break;
            }

            case VTYPE_NULL:
                v8Value = CefV8Value::CreateNull();
                break;

            case VTYPE_INVALID:
            default:
                v8Value = CefV8Value::CreateUndefined();
                break;
        }

        return v8Value;
    }


    static CefRefPtr<CefValue> ConvertWrapperToCefValue(CefValueWrapper &wrapper)
    {
        CefRefPtr<CefValue> cefValue = CefValue::Create();

        switch (wrapper.Type)
        {
            case CefValueWrapper::TYPE_INT:
                cefValue->SetInt(wrapper.GetInt());
                break;

            case CefValueWrapper::TYPE_BOOL:
                cefValue->SetBool(wrapper.GetBool());
                break;

            case CefValueWrapper::TYPE_DOUBLE:
                cefValue->SetDouble(wrapper.GetDouble());
                break;

            case CefValueWrapper::TYPE_STRING:
                cefValue->SetString(wrapper.GetString());
                break;

            case CefValueWrapper::TYPE_BINARY:
            {
                std::vector<char> binaryData = wrapper.GetBinary();
                CefRefPtr<CefBinaryValue> binaryValue = CefBinaryValue::Create(&binaryData[0], binaryData.size());
                cefValue->SetBinary(binaryValue);
                break;
            }

            case CefValueWrapper::TYPE_OBJECT:
            {
                CefRefPtr<CefDictionaryValue> dictValue = CefDictionaryValue::Create();
                auto objectData = wrapper.GetObject_();
                for (auto &pair: objectData)
                {
                    dictValue->SetValue(pair.first, ConvertWrapperToCefValue(pair.second));
                }
                cefValue->SetDictionary(dictValue);
                break;
            }

            case CefValueWrapper::TYPE_LIST:
            {
                CefRefPtr<CefListValue> listValue = CefListValue::Create();
                auto listData = wrapper.GetList();
                for (size_t i = 0; i < listData.size(); ++i)
                {
                    listValue->SetValue(i, ConvertWrapperToCefValue(listData[i]));
                }
                cefValue->SetList(listValue);
                break;
            }

            case CefValueWrapper::TYPE_NULL:
                cefValue->SetNull();
                break;

            case CefValueWrapper::TYPE_INVALID:
            default:
                // Handle invalid types as needed.
                break;
        }

        return cefValue;
    }

    static CefValueWrapper ConvertCefValueToWrapper(const CefRefPtr<CefValue> &cefValue)
    {
        CefValueWrapper wrapper;

        if (cefValue->GetType() == VTYPE_INT)
        {
            wrapper.SetInt(cefValue->GetInt());
        } else if (cefValue->GetType() == VTYPE_BOOL)
        {
            wrapper.SetBool(cefValue->GetBool());
        } else if (cefValue->GetType() == VTYPE_DOUBLE)
        {
            wrapper.SetDouble(cefValue->GetDouble());
        } else if (cefValue->GetType() == VTYPE_STRING)
        {
            wrapper.SetString(cefValue->GetString().ToString());
        } else if (cefValue->GetType() == VTYPE_BINARY)
        {
            CefRefPtr<CefBinaryValue> binaryValue = cefValue->GetBinary();
            size_t size = binaryValue->GetSize();
            std::vector<char> data(size);
            binaryValue->GetData(&data[0], size, 0);
            wrapper.SetBinary(data);
        } else if (cefValue->GetType() == VTYPE_DICTIONARY)
        {
            CefRefPtr<CefDictionaryValue> dictValue = cefValue->GetDictionary();
            CefDictionaryValue::KeyList keys;
            dictValue->GetKeys(keys);
            std::map<std::string, CefValueWrapper> objectValue;

            for (const auto &key: keys)
            {
                CefRefPtr<CefValue> value = dictValue->GetValue(key);
                objectValue[key.ToString()] = ConvertCefValueToWrapper(value);
            }

            wrapper.SetObject(objectValue);
        } else if (cefValue->GetType() == VTYPE_LIST)
        {
            CefRefPtr<CefListValue> listValue = cefValue->GetList();
            std::vector<CefValueWrapper> listWrapper;

            for (size_t i = 0; i < listValue->GetSize(); ++i)
            {
                CefRefPtr<CefValue> value = listValue->GetValue(i);
                listWrapper.push_back(ConvertCefValueToWrapper(value));
            }

            wrapper.SetList(listWrapper);
        } else if (cefValue->GetType() == VTYPE_NULL)
        {
            wrapper.SetNull();
        } else
        {
            wrapper.SetInvalid();
        }

        return wrapper;
    }

    static void AddJavascriptArg(const CefRefPtr<CefV8Value> &argument,
                                 CefRefPtr<CefListValue> &javascript_args,
                                 CefRefPtr<CefListValue> &javascript_arg_types,
                                 int &jsArgsIndex)
    {
        if (argument->IsInt())
        {
            javascript_args->SetInt(jsArgsIndex, argument->GetIntValue());
            javascript_arg_types->SetString(jsArgsIndex, "int");
        } else if (argument->IsBool())
        {
            javascript_args->SetBool(jsArgsIndex, argument->GetBoolValue());
            javascript_arg_types->SetString(jsArgsIndex, "bool");
        } else if (argument->IsDouble())
        {
            javascript_args->SetDouble(jsArgsIndex, argument->GetDoubleValue());
            javascript_arg_types->SetString(jsArgsIndex, "double");
        } else if (argument->IsString())
        {
            javascript_args->SetString(jsArgsIndex, argument->GetStringValue());
            javascript_arg_types->SetString(jsArgsIndex, "string");
        } else if (argument->IsObject())
        {
            CefRefPtr<CefDictionaryValue> objectValue = ConvertJSObjectToDictionary(argument);
            javascript_args->SetDictionary(jsArgsIndex, objectValue);
            javascript_arg_types->SetString(jsArgsIndex, "object");
        } else if (argument->IsArray())
        {
            CefRefPtr<CefListValue> arrayValue = ConvertJSArrayToList(argument);
            javascript_args->SetList(jsArgsIndex, arrayValue);
            javascript_arg_types->SetString(jsArgsIndex, "array");
        }
        jsArgsIndex++;
    }

    static CefRefPtr<CefDictionaryValue> ConvertJSObjectToDictionary(CefRefPtr<CefV8Value> jsObject)
    {
        CefRefPtr<CefDictionaryValue> dict = CefDictionaryValue::Create();
        std::vector<CefString> keys;

        if (jsObject->GetKeys(keys))
        {
            for (const auto &key: keys)
            {
                CefRefPtr<CefV8Value> value = jsObject->GetValue(key);
                if (value->IsInt())
                {
                    dict->SetInt(key, value->GetIntValue());
                } else if (value->IsBool())
                {
                    dict->SetBool(key, value->GetBoolValue());
                } else if (value->IsDouble())
                {
                    dict->SetDouble(key, value->GetDoubleValue());
                } else if (value->IsString())
                {
                    dict->SetString(key, value->GetStringValue());
                } else if (value->IsObject())
                {
                    dict->SetDictionary(key, ConvertJSObjectToDictionary(value));
                } else if (value->IsArray())
                {
                    dict->SetList(key, ConvertJSArrayToList(value));
                }
            }
        }

        return dict;
    }

    static CefRefPtr<CefListValue> ConvertJSArrayToList(CefRefPtr<CefV8Value> jsArray)
    {
        CefRefPtr<CefListValue> list = CefListValue::Create();
        int length = jsArray->GetArrayLength();

        for (int i = 0; i < length; ++i)
        {
            CefRefPtr<CefV8Value> value = jsArray->GetValue(i);

            if (value->IsInt())
            {
                list->SetInt(i, value->GetIntValue());
            } else if (value->IsBool())
            {
                list->SetBool(i, value->GetBoolValue());
            } else if (value->IsDouble())
            {
                list->SetDouble(i, value->GetDoubleValue());
            } else if (value->IsString())
            {
                list->SetString(i, value->GetStringValue());
            } else if (value->IsObject())
            {
                list->SetDictionary(i, ConvertJSObjectToDictionary(value));
            } else if (value->IsArray())
            {
                list->SetList(i, ConvertJSArrayToList(value));
            }
        }

        return list;
    }
};

#endif // JAVASCRIPT_BINDING_H
