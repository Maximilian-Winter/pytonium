"""Pytonium Reactive Components — surgical DOM updates from pure Python.

This module provides a reactive component model that tracks dependencies
between Python state and DOM nodes, enabling minimal, targeted DOM updates
without a virtual DOM or JavaScript framework runtime.

Basic usage:
    from Pytonium import Pytonium
    from Pytonium.components import Component, State, Div, H1, Button

    class Counter(Component):
        count = State(0)

        def increment(self):
            self.count += 1

        def render(self):
            return (
                Div()
                    .child(H1().text(lambda: f"Count: {self.count}"))
                    .child(Button().text("+").on_click(self.increment))
            )

    p = Pytonium()
    Component.setup(p)                             # 1. before initialize!
    p.initialize("file:///page.html", 800, 600)    # 2. create browser
    Counter().mount(p)                             # 3. render & inject
"""

from .component import Component
from .state import State, DependencyTracker
from .computed import Computed
from .elements import (
    Element,
    Div, Span, P,
    H1, H2, H3, H4, H5, H6,
    Button, Input, Textarea, Select, Option, Label, Form,
    A, Img,
    Ul, Ol, Li,
    Table, Tr, Td, Th, Thead, Tbody,
    Header, Footer, Nav, Section, Article, Main,
    Pre, Code, Hr, Br, Strong, Em,
)
from .conditional import Show, Switch
from .event_router import EventRouter, EventData
from .mutation_compiler import MutationCompiler
from .dynamic_children import DynamicChildrenManager
from .types import UpdateType, UpdateCommand, Binding

__all__ = [
    # Core
    "Component",
    "State",
    "Computed",
    "DependencyTracker",
    # Elements
    "Element",
    "Div", "Span", "P",
    "H1", "H2", "H3", "H4", "H5", "H6",
    "Button", "Input", "Textarea", "Select", "Option", "Label", "Form",
    "A", "Img",
    "Ul", "Ol", "Li",
    "Table", "Tr", "Td", "Th", "Thead", "Tbody",
    "Header", "Footer", "Nav", "Section", "Article", "Main",
    "Pre", "Code", "Hr", "Br", "Strong", "Em",
    # Conditional
    "Show", "Switch",
    # Event routing
    "EventRouter", "EventData",
    # Internals (for advanced use)
    "MutationCompiler",
    "DynamicChildrenManager",
    "UpdateType", "UpdateCommand", "Binding",
]
