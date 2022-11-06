#ifndef JAVASCRIPT_BINDING_H
#define JAVASCRIPT_BINDING_H

#include "include/cef_client.h"
#include "include/cef_render_process_handler.h"
#include "include/wrapper/cef_helpers.h"
#include <list>
#include <utility>

class CefValueWrapper
{
public:
        CefValueWrapper()
        {
          Type = -1;
          IntValue = 0;
          BoolValue = false;
          DoubleValue = 0.0;
          StringValue = "";
		}

	bool IsInt()
	{
		return Type == 0;
	}

	bool IsBool()
	{
		return Type == 1;
	}

	bool IsDouble()
	{
		return Type == 2;
	}

	bool IsString()
	{
		return Type == 3;
	}

	int GetInt()
	{
		return IntValue;
	}

	bool GetBool()
	{
		return BoolValue;
	}

	double GetDouble()
	{
		return DoubleValue;
	}

	std::string GetString()
	{
		return StringValue;
	}

	int Type;
	int IntValue;
	bool BoolValue;
	double DoubleValue;
	std::string StringValue;
};

using js_python_callback_object_ptr = void(*);
using js_python_bindings_handler_function_ptr = void(*)(void* python_callback_object, int argsSize,
                                                        CefValueWrapper* callback_args);
using js_binding_function_ptr = void(*)(int argsSize, CefValueWrapper* callback_args);

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

	JavascriptPythonBinding(void (*handlerFunction)(void*, int, CefValueWrapper*),
	                        std::string messageTopic,
	                        void* pythonCallbackObject, std::string javascriptObject = "")
		: HandlerFunction(handlerFunction), MessageTopic(messageTopic),
		  PythonCallbackObject(pythonCallbackObject), JavascriptObject(javascriptObject)
	{
	}

	void CallHandler(int argsSize, CefValueWrapper* args) const
	{
		HandlerFunction(PythonCallbackObject, argsSize, args);
	}

};


class JavascriptBinding
{
public:
	JavascriptBinding()
	{
	}

	JavascriptBinding(std::string name, js_binding_function_ptr pFunction, std::string javascriptObject = "")
	{
		functionName = name;
		function = pFunction;
                JavascriptObject = javascriptObject;
	}

	std::string functionName;
        std::string JavascriptObject;
	js_binding_function_ptr function;
};
#endif // JAVASCRIPT_BINDING_H
