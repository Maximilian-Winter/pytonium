//
// Created by maxim on 24.09.2023.
//
#include <iostream>
#include <unordered_map>
#include <string>
#include <map>
#include <vector>
#include "javascript_binding.h"

#ifndef PYTONIUM_APPLICATIONSTATEMANAGEMENT_H
#define PYTONIUM_APPLICATIONSTATEMANAGEMENT_H
#include <iostream>
#include <unordered_map>
#include <string>
#include "nlohmann/json.hpp"


class ApplicationStateManagerHelper
{
public:
    static CefRefPtr<CefValue> jsonToCefValue(const nlohmann::json& jValue) {
        CefRefPtr<CefValue> cefValue = CefValue::Create();

        if (jValue.is_null()) {
            cefValue->SetNull();
        } else if (jValue.is_boolean()) {
            cefValue->SetBool(jValue.get<bool>());
        } else if (jValue.is_number_integer()) {
            cefValue->SetInt(jValue.get<int>());
        } else if (jValue.is_number_float()) {
            cefValue->SetDouble(jValue.get<double>());
        } else if (jValue.is_string()) {
            cefValue->SetString(jValue.get<std::string>());
        } else if (jValue.is_object()) {
            CefRefPtr<CefDictionaryValue> dict = CefDictionaryValue::Create();
            for (auto& [key, value] : jValue.items()) {
                dict->SetValue(key, jsonToCefValue(value));
            }
            cefValue->SetDictionary(dict);
        } else if (jValue.is_array()) {
            CefRefPtr<CefListValue> list = CefListValue::Create();
            int index = 0;
            for (const auto& elem : jValue) {
                list->SetValue(index, jsonToCefValue(elem));
                index++;
            }
            cefValue->SetList(list);
        } else {
            cefValue->SetNull(); // Or handle as you see fit
        }

        return cefValue;
    }

    static nlohmann::json cefValueToJson(CefRefPtr<CefValue> cefValue) {
        CefValueType type = cefValue->GetType();
        switch (type) {
            case VTYPE_NULL:
                return nlohmann::json(nullptr);
            case VTYPE_BOOL:
                return nlohmann::json(cefValue->GetBool());
            case VTYPE_INT:
                return nlohmann::json(cefValue->GetInt());
            case VTYPE_DOUBLE:
                return nlohmann::json(cefValue->GetDouble());
            case VTYPE_STRING: {
                CefString cefStr = cefValue->GetString();
                return nlohmann::json(cefStr.ToString());
            }
            case VTYPE_DICTIONARY: {
                nlohmann::json obj = nlohmann::json::object();
                CefRefPtr<CefDictionaryValue> dict = cefValue->GetDictionary();
                CefDictionaryValue::KeyList keys;
                dict->GetKeys(keys);
                for (const auto& key : keys) {
                    obj[key] = cefValueToJson(dict->GetValue(key));
                }
                return obj;
            }
            case VTYPE_LIST: {
                nlohmann::json arr = nlohmann::json::array();
                CefRefPtr<CefListValue> list = cefValue->GetList();
                for (size_t i = 0; i < list->GetSize(); ++i) {
                    arr.push_back(cefValueToJson(list->GetValue(i)));
                }
                return arr;
            }
            default:
                return nlohmann::json(nullptr); // Or handle as you see fit
        }
    }

    static CefRefPtr<CefV8Value> jsonToCefV8Value(const nlohmann::json& jValue) {
        if (jValue.is_null()) {
            return CefV8Value::CreateNull();
        } else if (jValue.is_boolean()) {
            return CefV8Value::CreateBool(jValue.get<bool>());
        } else if (jValue.is_number_integer()) {
            return CefV8Value::CreateInt(jValue.get<int>());
        } else if (jValue.is_number_float()) {
            return CefV8Value::CreateDouble(jValue.get<double>());
        } else if (jValue.is_string()) {
            return CefV8Value::CreateString(jValue.get<std::string>());
        } else if (jValue.is_object()) {
            CefRefPtr<CefV8Value> obj = CefV8Value::CreateObject(nullptr, nullptr);
            for (auto& [key, value] : jValue.items()) {
                obj->SetValue(key, jsonToCefV8Value(value), V8_PROPERTY_ATTRIBUTE_NONE);
            }
            return obj;
        } else if (jValue.is_array()) {
            CefRefPtr<CefV8Value> arr = CefV8Value::CreateArray((int)jValue.size());
            int index = 0;
            for (const auto& elem : jValue) {
                arr->SetValue(index, jsonToCefV8Value(elem));
                index++;
            }
            return arr;
        } else {
            return CefV8Value::CreateUndefined(); // Or handle as you see fit
        }
    }

    static nlohmann::json cefV8ValueToJson(const CefRefPtr<CefV8Value>& cefV8Value) {
        if (cefV8Value->IsNull()) {
            return nlohmann::json(nullptr);
        } else if (cefV8Value->IsBool()) {
            return nlohmann::json(cefV8Value->GetBoolValue());
        } else if (cefV8Value->IsInt()) {
            return nlohmann::json(cefV8Value->GetIntValue());
        } else if (cefV8Value->IsDouble()) {
            return nlohmann::json(cefV8Value->GetDoubleValue());
        } else if (cefV8Value->IsString()) {
            return nlohmann::json(cefV8Value->GetStringValue().ToString());
        } else if (cefV8Value->IsObject()) {
            nlohmann::json obj = nlohmann::json::object();
            std::vector<CefString> keys;
            cefV8Value->GetKeys(keys);
            for (const auto& key : keys) {
                CefRefPtr<CefV8Value> value = cefV8Value->GetValue(key);
                obj[key.ToString()] = cefV8ValueToJson(value);
            }
            return obj;
        } else if (cefV8Value->IsArray()) {
            nlohmann::json arr = nlohmann::json::array();
            int length = cefV8Value->GetArrayLength();
            for (int i = 0; i < length; ++i) {
                CefRefPtr<CefV8Value> value = cefV8Value->GetValue(i);
                arr.push_back(cefV8ValueToJson(value));
            }
            return arr;
        } else {
            return nlohmann::json(nullptr); // Or handle as you see fit
        }
    }

    static std::string cefValueWrapperToJsonStr(CefValueWrapper& cefValue) {
        nlohmann::json jsonObj = cefValueWrapperToJson(cefValue);
        return jsonObj.dump();
    }
    static nlohmann::json cefValueWrapperToJson(CefValueWrapper& cefValue) {
        if (cefValue.Type == CefValueWrapper::TYPE_INT) {
            return nlohmann::json(cefValue.GetInt());
        }
        if (cefValue.Type == CefValueWrapper::TYPE_BOOL) {
            return nlohmann::json(cefValue.GetBool());
        }
        if (cefValue.Type == CefValueWrapper::TYPE_DOUBLE) {
            return nlohmann::json(cefValue.GetDouble());
        }
        if (cefValue.Type == CefValueWrapper::TYPE_STRING) {
            return nlohmann::json(cefValue.GetString());
        }
        if (cefValue.Type == CefValueWrapper::TYPE_OBJECT) {
            nlohmann::json obj = nlohmann::json::object();
            for (auto& [key, value] : cefValue.GetObject_()) {
                obj[key] = cefValueWrapperToJson(value);
            }
            return obj;
        }
        if (cefValue.Type == CefValueWrapper::TYPE_LIST) {
            nlohmann::json arr = nlohmann::json::array();
            for (auto& elem : cefValue.GetList()) {
                arr.push_back(cefValueWrapperToJson(elem));
            }
            return arr;
        }
        if (cefValue.Type == CefValueWrapper::TYPE_NULL) {
            return nlohmann::json(nullptr);
        }
        // Handle other types as you see fit, e.g., TYPE_BINARY, TYPE_INVALID, TYPE_UNDEFINED
        return nlohmann::json(nullptr); // default case, you can also throw an exception here
    }
    static CefValueWrapper jsonToCefValueWrapper(const nlohmann::json& jValue) {
        CefValueWrapper cefValue;

        if (jValue.is_null()) {
            cefValue.SetNull();
        } else if (jValue.is_boolean()) {
            cefValue.SetBool(jValue.get<bool>());
        } else if (jValue.is_number_integer()) {
            cefValue.SetInt(jValue.get<int>());
        } else if (jValue.is_number_float()) {
            cefValue.SetDouble(jValue.get<double>());
        } else if (jValue.is_string()) {
            cefValue.SetString(jValue.get<std::string>());
        } else if (jValue.is_object()) {
            std::map<std::string, CefValueWrapper> obj;

            for (auto& [key, value] : jValue.items()) {
                obj[key] = jsonToCefValueWrapper(value);
            }

            cefValue.SetObject(obj);
        } else if (jValue.is_array()) {
            std::vector<CefValueWrapper> list;

            for (const auto& elem : jValue) {
                list.push_back(jsonToCefValueWrapper(elem));
            }

            cefValue.SetList(list);
        } else {
            cefValue.SetInvalid();
        }

        return cefValue;
    }
};

class ApplicationStateManager {
private:
    std::unordered_map<std::string, std::unordered_map<std::string, nlohmann::json>> namespaces;

    void ensureNamespaceExists(const std::string& namespaceName) {
        if (namespaces.find(namespaceName) == namespaces.end()) {
            namespaces[namespaceName] = std::unordered_map<std::string, nlohmann::json>();
        }
    }

public:
    void setState(const std::string& namespaceName, const std::string& key, const nlohmann::json& value) {
        ensureNamespaceExists(namespaceName);
        namespaces[namespaceName][key] = value;
    }


    nlohmann::json getState(const std::string& namespaceName, const std::string& key) {
        ensureNamespaceExists(namespaceName);
        if (namespaces[namespaceName].find(key) != namespaces[namespaceName].end()) {
            return namespaces[namespaceName][key];
        }
        return nullptr;  // Return null json if key not found
    }

    void removeState(const std::string& namespaceName, const std::string& key) {
        ensureNamespaceExists(namespaceName);
        if (namespaces[namespaceName].find(key) != namespaces[namespaceName].end()) {
            namespaces[namespaceName].erase(key);
        }
    }

    std::string serializeToJson() {
        nlohmann::json jsonObj = namespaces;
        return jsonObj.dump();
    }

    void deserializeFromJson(const std::string& jsonStr) {
        try {
            nlohmann::json jsonObj = nlohmann::json::parse(jsonStr);
            namespaces = jsonObj.get<decltype(namespaces)>();
        } catch (nlohmann::json::parse_error&) {
            throw std::runtime_error("Invalid JSON string provided for deserialization.");
        }
    }

    std::string serializeNamespaceToJson(const std::string& namespaceName) {
        ensureNamespaceExists(namespaceName);  // Make sure the namespace exists
        nlohmann::json jsonObj = namespaces[namespaceName];
        return jsonObj.dump();
    }

    void deserializeNamespaceFromJson(const std::string& namespaceName, const std::string& jsonStr) {
        try {
            nlohmann::json jsonObj = nlohmann::json::parse(jsonStr);
            auto namespaceMap = jsonObj.get<std::unordered_map<std::string, nlohmann::json>>();
            namespaces[namespaceName] = namespaceMap;  // This will create or update the namespace
        } catch (nlohmann::json::parse_error&) {
            throw std::runtime_error("Invalid JSON string provided for deserializing namespace.");
        }
    }

    CefValueWrapper namespaceToCefValueWrapper(const std::string& namespaceName) {
        ensureNamespaceExists(namespaceName);  // Make sure the namespace exists

        // Create an empty CefValueWrapper object to hold the converted namespace
        CefValueWrapper cefNamespace;
        std::map<std::string, CefValueWrapper> cefObject;

        // Iterate over each key-value pair in the namespace and convert it to CefValueWrapper
        for (const auto& [key, value] : namespaces[namespaceName]) {
            cefObject[key] = ApplicationStateManagerHelper::jsonToCefValueWrapper(value);
        }

        // Set the object to the CefValueWrapper and return
        cefNamespace.SetObject(cefObject);
        return cefNamespace;
    }

    CefValueWrapper allNamespacesToCefValueWrapper(const std::string& globalNamespaceName) {
        // Create an empty CefValueWrapper object to hold all namespaces
        CefValueWrapper globalCefNamespace;
        std::map<std::string, CefValueWrapper> globalCefObject;

        // Iterate over each namespace in the StateManager and convert it to a CefValueWrapper
        for (const auto& [namespaceName, namespaceMap] : namespaces) {
            CefValueWrapper cefNamespace = namespaceToCefValueWrapper(namespaceName);
            globalCefObject[namespaceName] = cefNamespace;
        }

        // Set the global namespace name and bundle all the individual namespaces under it
        globalCefNamespace.SetObject(globalCefObject);

        // Create another CefValueWrapper object to hold the global namespace
        CefValueWrapper rootCefObject;
        std::map<std::string, CefValueWrapper> rootCefMap;
        rootCefMap[globalNamespaceName] = globalCefNamespace;
        rootCefObject.SetObject(rootCefMap);

        return rootCefObject;
    }

};


#endif //PYTONIUM_APPLICATIONSTATEMANAGEMENT_H
