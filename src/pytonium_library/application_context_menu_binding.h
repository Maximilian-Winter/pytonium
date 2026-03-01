//
// Created by maxim on 29.09.2023.
//

#ifndef PYTONIUM_APPLICATION_CONTEXT_MENU_BINDING_H
#define PYTONIUM_APPLICATION_CONTEXT_MENU_BINDING_H

#include <utility>
#include <string>
#include "cef_value_wrapper.h"

using context_menu_handler_object_ptr = void (*);
using context_menu_handler_function_ptr = void (*)(context_menu_handler_object_ptr python_callback_object, std::string contextMenuNamespace, int contextMenuIndex, std::string paramsJson);

// Callback type for the on_before_context_menu event
using before_context_menu_callback_ptr = void (*)(void* user_data, const char* params_json);

enum class ContextMenuItemType
{
    COMMAND,      // Standard clickable item (existing behavior)
    CHECK,        // Checkable item (toggled on click)
    RADIO,        // Radio button item (one active per group)
    SEPARATOR,    // Visual divider (no callback)
    SUBMENU       // Opens a nested submenu
};


class ContextMenuBinding
{
public:
    // Callback pointers (nullptr for separators and submenus)
    context_menu_handler_function_ptr ContextMenuHandlerCallbackFunction = nullptr;
    context_menu_handler_object_ptr ContextMenuHandlerCallbackObject = nullptr;

    std::string DisplayName;
    std::string Namespace;
    int CommandId = 0;

    // Item type and properties
    ContextMenuItemType ItemType = ContextMenuItemType::COMMAND;
    int RadioGroupId = 0;          // For RADIO items: group identifier
    bool Checked = false;          // For CHECK and RADIO items
    bool Enabled = true;           // Whether the item is clickable
    bool Visible = true;           // Whether the item appears in the menu
    std::string SubMenuNamespace;  // For SUBMENU items: namespace of children

    // Accelerator (keyboard shortcut label)
    int AccelKeyCode = 0;
    bool AccelShift = false;
    bool AccelCtrl = false;
    bool AccelAlt = false;

    ContextMenuBinding()
    = default;

    // Original constructor (backward compatible — creates COMMAND type)
    ContextMenuBinding(std::string displayName, int commandId,
                       context_menu_handler_function_ptr contextMenuCallbackFunction,
                       context_menu_handler_object_ptr contextMenuCallbackObject,
                       std::string contextMenuNamespace)
        : ContextMenuHandlerCallbackFunction(contextMenuCallbackFunction),
          ContextMenuHandlerCallbackObject(contextMenuCallbackObject),
          DisplayName(std::move(displayName)),
          Namespace(std::move(contextMenuNamespace)),
          CommandId(commandId),
          ItemType(ContextMenuItemType::COMMAND)
    {}

    // Full constructor with item type
    ContextMenuBinding(std::string displayName, int commandId,
                       context_menu_handler_function_ptr contextMenuCallbackFunction,
                       context_menu_handler_object_ptr contextMenuCallbackObject,
                       std::string contextMenuNamespace,
                       ContextMenuItemType itemType,
                       int radioGroupId = 0,
                       bool checked = false,
                       const std::string& subMenuNamespace = "")
        : ContextMenuHandlerCallbackFunction(contextMenuCallbackFunction),
          ContextMenuHandlerCallbackObject(contextMenuCallbackObject),
          DisplayName(std::move(displayName)),
          Namespace(std::move(contextMenuNamespace)),
          CommandId(commandId),
          ItemType(itemType),
          RadioGroupId(radioGroupId),
          Checked(checked),
          SubMenuNamespace(subMenuNamespace)
    {}

    // Separator factory
    static ContextMenuBinding MakeSeparator(const std::string& ns, int commandId)
    {
        ContextMenuBinding b;
        b.Namespace = ns;
        b.CommandId = commandId;
        b.ItemType = ContextMenuItemType::SEPARATOR;
        return b;
    }

    // Submenu factory
    static ContextMenuBinding MakeSubMenu(const std::string& displayName,
                                           const std::string& ns, int commandId,
                                           const std::string& subNs)
    {
        ContextMenuBinding b;
        b.DisplayName = displayName;
        b.Namespace = ns;
        b.CommandId = commandId;
        b.ItemType = ContextMenuItemType::SUBMENU;
        b.SubMenuNamespace = subNs;
        return b;
    }

    void OnContextMenuEntryClicked(const std::string& paramsJson = "") const
    {
        if (ContextMenuHandlerCallbackFunction)
        {
            ContextMenuHandlerCallbackFunction(ContextMenuHandlerCallbackObject, Namespace, CommandId, paramsJson);
        }
    }
};

#endif //PYTONIUM_APPLICATION_CONTEXT_MENU_BINDING_H
