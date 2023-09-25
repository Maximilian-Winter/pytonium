//
// Created by maxim on 25.09.2023.
//

#ifndef PYTONIUM_CEF_VALUE_WRAPPER_H
#define PYTONIUM_CEF_VALUE_WRAPPER_H

#include <map>
#include <cmath>
#include <sstream>
#include <iostream>
#include <vector>
#include <string>
#include <utility>
#include <list>
#include "include/wrapper/cef_helpers.h"
#include "include/cef_render_process_handler.h"
#include "include/cef_client.h"

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



#endif //PYTONIUM_CEF_VALUE_WRAPPER_H
