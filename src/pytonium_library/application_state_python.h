//
// Created by maxim on 25.09.2023.
//

#ifndef PYTONIUM_APPLICATION_STATE_PYTHON_H
#define PYTONIUM_APPLICATION_STATE_PYTHON_H

#include <utility>
#include "cef_value_wrapper.h"

using state_callback_object_ptr = void (*);
using state_handler_function_ptr = void (*)(state_callback_object_ptr python_callback_object,
                                            std::string stateNamespace, std::string stateKey,
                                            CefValueWrapper callback_args);


class StateHandlerPythonBinding
{
public:
    state_handler_function_ptr StateHandlerCallbackFunction;
    state_callback_object_ptr StateHandlerCallbackObject;
    std::vector<std::string> StateNamespacesToSubscribeTo;
    StateHandlerPythonBinding()
    = default;

    StateHandlerPythonBinding(void (*stateHandlerCallbackFunction)(state_callback_object_ptr, std::string, std::string,
                                                                   CefValueWrapper),
                              void *stateHandlerCallbackObject, std::vector<std::string> stateNamespacesToSubscribeTo) : StateHandlerCallbackFunction(
            stateHandlerCallbackFunction), StateHandlerCallbackObject(stateHandlerCallbackObject), StateNamespacesToSubscribeTo(std::move(stateNamespacesToSubscribeTo))
    {}

    void UpdateState(std::string stateNamespace, std::string stateKey, CefValueWrapper callback_args) const
    {
        for (const auto& namespaceName: StateNamespacesToSubscribeTo)
        {
            if(namespaceName == stateNamespace)
            {
                StateHandlerCallbackFunction(StateHandlerCallbackObject, std::move(stateNamespace), std::move(stateKey),
                                             std::move(callback_args));

                break;
            }
        }

    }
};

#endif //PYTONIUM_APPLICATION_STATE_PYTHON_H
