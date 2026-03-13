"""Core data types for Pytonium reactive components.

Defines the UpdateType enum, UpdateCommand dataclass, and Binding dataclass
used throughout the reactive component system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class UpdateType(Enum):
    """Types of DOM mutations the MutationCompiler can generate."""
    SET_TEXT_CONTENT = "text_content"
    SET_ATTRIBUTE = "set_attribute"
    REMOVE_ATTRIBUTE = "remove_attribute"
    ADD_CLASS = "add_class"
    REMOVE_CLASS = "remove_class"
    TOGGLE_CLASS = "toggle_class"
    SET_STYLE = "set_style"
    SET_VALUE = "set_value"
    INSERT_CHILD = "insert_child"
    REMOVE_CHILD = "remove_child"
    MOVE_CHILD = "move_child"
    REPLACE_INNER_HTML = "replace_inner_html"


@dataclass
class UpdateCommand:
    """A single DOM mutation to be compiled into JavaScript.

    Attributes:
        node_id: Target element's data-pyt-id value.
        update_type: What kind of mutation to perform.
        key: Attribute name, class name, or style property (context-dependent).
        value: New value to set.
        index: Position index for child operations.
        html: HTML string for insert/replace operations.
    """
    node_id: str
    update_type: UpdateType
    key: str = ""
    value: str = ""
    index: int = -1
    html: str = ""


@dataclass
class Binding:
    """A reactive binding between a State field and a DOM node.

    Created during dependency analysis of render(). When the bound State field
    changes, the transform lambda is re-evaluated and an UpdateCommand is
    emitted.

    Attributes:
        node_id: Target element's data-pyt-id value.
        update_type: What kind of mutation this binding produces.
        key: Attribute name, class name, or style property (for non-text bindings).
        transform: Lambda that produces the current value when called.
        _dynamic_manager_element: Element with DynamicChildrenManager (for children_from bindings).
        _conditional_element: Element with conditional logic (for Show/Switch bindings).
    """
    node_id: str
    update_type: UpdateType
    key: str = ""
    transform: Optional[Callable] = None
    _dynamic_manager_element: Any = None
    _conditional_element: Any = None


class BindingType(Enum):
    """Internal classification of element bindings for analysis."""
    TEXT_CONTENT = "text_content"
    ATTRIBUTE = "attribute"
    CLASS_TOGGLE = "class_toggle"
    STYLE = "style"
    VALUE = "value"
    CHILDREN_FROM = "children_from"
    CONDITIONAL = "conditional"
