//
// Created by maxim on 29.09.2023.
//

#ifndef PYTONIUM_APPLICATION_CONTEXT_MENU_BINDING_H
#define PYTONIUM_APPLICATION_CONTEXT_MENU_BINDING_H

#include <utility>
#include "cef_value_wrapper.h"

using context_menu_handler_object_ptr = void (*);
using context_menu_handler_function_ptr = void (*)(context_menu_handler_object_ptr python_callback_object, std::string contextMenuNamespace, int contextMenuIndex);


class ContextMenuBinding
{
public:
    context_menu_handler_function_ptr ContextMenuHandlerCallbackFunction;
    context_menu_handler_object_ptr ContextMenuHandlerCallbackObject;
    std::string DisplayName;
    std::string Namespace;
    int CommandId;
    ContextMenuBinding()
    = default;

    ContextMenuBinding( std::string displayName, int commandId, context_menu_handler_function_ptr contextMenuCallbackFunction,
                       context_menu_handler_object_ptr contextMenuCallbackObject, std::string contextMenuNamespace) : ContextMenuHandlerCallbackFunction(
            contextMenuCallbackFunction), ContextMenuHandlerCallbackObject(contextMenuCallbackObject), DisplayName(std::move(displayName)), CommandId(commandId), Namespace(std::move(contextMenuNamespace))
    {}

    void OnContextMenuEntryClicked() const
    {
        ContextMenuHandlerCallbackFunction(ContextMenuHandlerCallbackObject, Namespace, CommandId);
    }
};

#endif //PYTONIUM_APPLICATION_CONTEXT_MENU_BINDING_H
