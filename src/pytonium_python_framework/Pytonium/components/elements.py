"""Element builder for reactive components.

Provides the Element class with a fluent builder pattern for constructing
HTML element trees. Each element gets a unique data-pyt-id attribute for
surgical DOM updates. Convenience constructors (Div, Button, etc.) create
elements with pre-set tag names.

Lambdas passed to builder methods (text, attr, style, class_toggle) become
reactive bindings — the DependencyTracker discovers their State dependencies
during render analysis, and updates only the affected DOM nodes when state
changes.
"""

from typing import Any, Callable, Optional, Union
import html as html_module

from .types import UpdateType

# Module-level ID counter — reset per component mount
_next_id: int = 0


def reset_id_counter():
    """Reset the element ID counter. Called before each component render."""
    global _next_id
    _next_id = 0


def _generate_id() -> str:
    """Generate a unique node ID like 'n_0001'."""
    global _next_id
    _next_id += 1
    return f"n_{_next_id:04d}"


# HTML void elements (self-closing, no end tag)
_VOID_ELEMENTS = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
})

# Python attribute names → HTML attribute names
_ATTR_RENAMES = {
    "class_name": "class",
    "html_for": "for",
    "for_": "for",
    "http_equiv": "http-equiv",
    "accept_charset": "accept-charset",
    "tab_index": "tabindex",
    "access_key": "accesskey",
    "content_editable": "contenteditable",
    "cross_origin": "crossorigin",
    "col_span": "colspan",
    "row_span": "rowspan",
    "no_validate": "novalidate",
    "read_only": "readonly",
    "max_length": "maxlength",
    "min_length": "minlength",
}


def _html_attr_name(python_name: str) -> str:
    """Convert a Python-style attribute name to HTML attribute name.

    Handles renames (class_name → class, for_ → for) and converts
    remaining underscores to hyphens for data-* attributes.
    """
    if python_name in _ATTR_RENAMES:
        return _ATTR_RENAMES[python_name]
    # Convert data_foo → data-foo, aria_label → aria-label
    if python_name.startswith("data_") or python_name.startswith("aria_"):
        return python_name.replace("_", "-")
    return python_name


def _escape_attr(value: str) -> str:
    """Escape a string for safe use in an HTML attribute value."""
    return html_module.escape(str(value), quote=True)


def _escape_text(value: str) -> str:
    """Escape a string for safe use as HTML text content."""
    return html_module.escape(str(value), quote=False)


class Element:
    """Builder for HTML elements with reactive binding support.

    Elements form a tree that is rendered to HTML once during mount. Reactive
    bindings (lambdas) are registered with the DependencyTracker for surgical
    DOM updates on state changes.

    Usage:
        Div(class_name="container")
            .child(H1().text("Hello"))
            .child(Button().text(lambda: f"Count: {self.count}").on_click(self.increment))
    """

    def __init__(self, tag: str, **attrs):
        """Create an element with the given HTML tag.

        Args:
            tag: HTML tag name (e.g., "div", "button", "input").
            **attrs: Static HTML attributes as keyword arguments.
                     Python names are converted (class_name → class, etc.).
        """
        self.tag = tag
        self.node_id = _generate_id()
        self._children: list[Element] = []
        self._static_attrs: dict[str, str] = {}
        self._classes: list[str] = []
        self._static_text: Optional[str] = None
        self._static_styles: dict[str, str] = {}
        self._bindings: list[dict] = []  # Reactive bindings for DependencyTracker
        self._events: dict[str, dict] = {}  # Event handlers for EventRouter
        self._dynamic_children: Optional[dict] = None
        self._dynamic_manager = None  # Set by DynamicChildrenManager
        self._condition_binding: Optional[dict] = None  # For Show/Switch

        # Process keyword attributes
        for key, value in attrs.items():
            if key == "class_name":
                if isinstance(value, str):
                    self._classes.extend(value.split())
            else:
                html_name = _html_attr_name(key)
                self._static_attrs[html_name] = str(value)

    # --- Child management ---

    def child(self, element: "Element") -> "Element":
        """Append a child element.

        Args:
            element: Child Element to append.

        Returns:
            self for method chaining.
        """
        self._children.append(element)
        return self

    def children(self, *elements: "Element") -> "Element":
        """Append multiple child elements.

        Args:
            *elements: Child Elements to append.

        Returns:
            self for method chaining.
        """
        self._children.extend(elements)
        return self

    # --- Text content ---

    def text(self, content: Union[str, Callable]) -> "Element":
        """Set text content, either static or reactive.

        If content is a callable (lambda), it becomes a reactive binding that
        updates automatically when referenced State fields change.

        Args:
            content: Static string or lambda returning a string.

        Returns:
            self for method chaining.
        """
        if callable(content):
            self._bindings.append({
                "type": "text_content",
                "transform": content,
            })
        else:
            self._static_text = str(content)
        return self

    # --- Attributes ---

    def attr(self, name: str, value: Union[str, Callable]) -> "Element":
        """Set an HTML attribute, either static or reactive.

        Args:
            name: Attribute name (Python-style, e.g., 'data_value').
            value: Static string or lambda returning a string.

        Returns:
            self for method chaining.
        """
        html_name = _html_attr_name(name)
        if callable(value):
            self._bindings.append({
                "type": "attribute",
                "key": html_name,
                "transform": value,
            })
        else:
            self._static_attrs[html_name] = str(value)
        return self

    def id(self, html_id: str) -> "Element":
        """Set the HTML id attribute.

        Args:
            html_id: The id value.

        Returns:
            self for method chaining.
        """
        self._static_attrs["id"] = html_id
        return self

    # --- CSS classes ---

    def class_name(self, name: str) -> "Element":
        """Add one or more static CSS classes (space-separated).

        Args:
            name: Space-separated class names.

        Returns:
            self for method chaining.
        """
        self._classes.extend(name.split())
        return self

    def class_toggle(self, name: str, condition: Callable) -> "Element":
        """Toggle a CSS class based on a reactive condition.

        Args:
            name: CSS class name to toggle.
            condition: Lambda returning True/False.

        Returns:
            self for method chaining.
        """
        self._bindings.append({
            "type": "class_toggle",
            "key": name,
            "transform": condition,
        })
        return self

    # --- Inline styles ---

    def style(self, prop: str, value: Union[str, Callable]) -> "Element":
        """Set an inline style property, either static or reactive.

        Args:
            prop: CSS property name (e.g., 'background-color', 'fontSize').
            value: Static string or lambda returning a string.

        Returns:
            self for method chaining.
        """
        if callable(value):
            self._bindings.append({
                "type": "style",
                "key": prop,
                "transform": value,
            })
        else:
            self._static_styles[prop] = str(value)
        return self

    # --- Input binding ---

    def bind_value(
        self, component, field_name: str, debounce_ms: int = 0
    ) -> "Element":
        """Two-way binding between an input element's value and a State field.

        Sets the input value from state (Python → JS) and registers an input
        event listener to update state on user input (JS → Python).

        Args:
            component: The Component instance owning the State field.
            field_name: Name of the State field to bind.
            debounce_ms: Optional debounce delay for input events (ms).

        Returns:
            self for method chaining.
        """
        self._bindings.append({
            "type": "value",
            "transform": lambda: getattr(component, field_name),
        })
        self._events["input"] = {
            "handler": lambda e: setattr(component, field_name, e.value),
            "buffered": True,
            "debounce_ms": debounce_ms,
        }
        return self

    # --- Event handlers ---

    def on_click(self, handler: Callable) -> "Element":
        """Register a click event handler.

        Args:
            handler: Callable, either no-arg or receives EventData.

        Returns:
            self for method chaining.
        """
        self._events["click"] = {"handler": handler}
        return self

    def on_dblclick(self, handler: Callable) -> "Element":
        """Register a double-click event handler."""
        self._events["dblclick"] = {"handler": handler}
        return self

    def on_keydown(self, handler: Callable) -> "Element":
        """Register a keydown event handler.

        Args:
            handler: Callable receiving EventData with key info.

        Returns:
            self for method chaining.
        """
        self._events["keydown"] = {"handler": handler}
        return self

    def on_keyup(self, handler: Callable) -> "Element":
        """Register a keyup event handler."""
        self._events["keyup"] = {"handler": handler}
        return self

    def on_input(self, handler: Callable) -> "Element":
        """Register an input event handler (for text inputs)."""
        self._events["input"] = {"handler": handler}
        return self

    def on_change(self, handler: Callable) -> "Element":
        """Register a change event handler (for selects, checkboxes)."""
        self._events["change"] = {"handler": handler}
        return self

    def on_submit(self, handler: Callable) -> "Element":
        """Register a form submit event handler."""
        self._events["submit"] = {"handler": handler, "prevent_default": True}
        return self

    def on_mouseenter(self, handler: Callable) -> "Element":
        """Register a mouseenter event handler."""
        self._events["mouseenter"] = {"handler": handler}
        return self

    def on_mouseleave(self, handler: Callable) -> "Element":
        """Register a mouseleave event handler."""
        self._events["mouseleave"] = {"handler": handler}
        return self

    def on_focus(self, handler: Callable) -> "Element":
        """Register a focus event handler."""
        self._events["focus"] = {"handler": handler}
        return self

    def on_blur(self, handler: Callable) -> "Element":
        """Register a blur event handler."""
        self._events["blur"] = {"handler": handler}
        return self

    # --- Dynamic children ---

    def children_from(
        self,
        source: Callable,
        key: Callable,
        render_item: Callable,
    ) -> "Element":
        """Define dynamic children from a reactive list source.

        The children are rendered from the source list, keyed for efficient
        add/remove/reorder operations.

        Args:
            source: Lambda returning the current list of items.
            key: Function extracting a stable identity from each item.
            render_item: Function(item, index) → Element for each item.

        Returns:
            self for method chaining.
        """
        self._dynamic_children = {
            "source": source,
            "key": key,
            "render_item": render_item,
        }
        return self

    # --- HTML generation ---

    def to_html(self) -> str:
        """Generate the initial HTML string with data-pyt-id markers.

        Reactive bindings are evaluated once for initial values. Static
        attributes and text are rendered directly. The resulting HTML is
        suitable for injection into the DOM via innerHTML.

        Returns:
            HTML string for this element and all its children.
        """
        parts: list[str] = [f"<{self.tag}"]

        # data-pyt-id is always first
        parts.append(f' data-pyt-id="{self.node_id}"')

        # Collect all classes (static + initial reactive toggles)
        all_classes = list(self._classes)
        for binding in self._bindings:
            if binding["type"] == "class_toggle":
                try:
                    if binding["transform"]():
                        all_classes.append(binding["key"])
                except Exception:
                    pass

        if all_classes:
            parts.append(f' class="{_escape_attr(" ".join(all_classes))}"')

        # Static attributes
        for attr_name, attr_value in self._static_attrs.items():
            if attr_name == "class":
                continue  # Handled above
            parts.append(f' {attr_name}="{_escape_attr(attr_value)}"')

        # Reactive attributes — evaluate for initial values
        for binding in self._bindings:
            if binding["type"] == "attribute":
                try:
                    val = binding["transform"]()
                    parts.append(
                        f' {binding["key"]}="{_escape_attr(str(val))}"'
                    )
                except Exception:
                    pass

        # Static styles + reactive styles (initial)
        all_styles = dict(self._static_styles)
        for binding in self._bindings:
            if binding["type"] == "style":
                try:
                    all_styles[binding["key"]] = str(binding["transform"]())
                except Exception:
                    pass
        if all_styles:
            style_str = ";".join(f"{k}:{v}" for k, v in all_styles.items())
            parts.append(f' style="{_escape_attr(style_str)}"')

        parts.append(">")

        # Void elements — self-closing, no children or text
        if self.tag in _VOID_ELEMENTS:
            # For input elements with value binding, set initial value
            for binding in self._bindings:
                if binding["type"] == "value":
                    try:
                        val = binding["transform"]()
                        # Insert value attribute before closing >
                        parts.insert(-1, f' value="{_escape_attr(str(val))}"')
                    except Exception:
                        pass
            return "".join(parts)

        # Text content — static or reactive (evaluated for initial value)
        text = ""
        if self._static_text is not None:
            text = _escape_text(self._static_text)
        for binding in self._bindings:
            if binding["type"] == "text_content":
                try:
                    text = _escape_text(str(binding["transform"]()))
                except Exception:
                    text = ""

        if text:
            parts.append(text)

        # Children
        for child in self._children:
            parts.append(child.to_html())

        # Dynamic children — render initial items
        if self._dynamic_children:
            source_fn = self._dynamic_children["source"]
            render_item_fn = self._dynamic_children["render_item"]
            try:
                items = source_fn()
                for i, item in enumerate(items):
                    child_element = render_item_fn(item, i)
                    parts.append(child_element.to_html())
            except Exception:
                pass

        # Closing tag
        parts.append(f"</{self.tag}>")
        return "".join(parts)


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------

def Div(**attrs) -> Element:
    """Create a <div> element."""
    return Element("div", **attrs)

def Span(**attrs) -> Element:
    """Create a <span> element."""
    return Element("span", **attrs)

def P(**attrs) -> Element:
    """Create a <p> element."""
    return Element("p", **attrs)

def H1(**attrs) -> Element:
    """Create an <h1> element."""
    return Element("h1", **attrs)

def H2(**attrs) -> Element:
    """Create an <h2> element."""
    return Element("h2", **attrs)

def H3(**attrs) -> Element:
    """Create an <h3> element."""
    return Element("h3", **attrs)

def H4(**attrs) -> Element:
    """Create an <h4> element."""
    return Element("h4", **attrs)

def H5(**attrs) -> Element:
    """Create an <h5> element."""
    return Element("h5", **attrs)

def H6(**attrs) -> Element:
    """Create an <h6> element."""
    return Element("h6", **attrs)

def Button(**attrs) -> Element:
    """Create a <button> element."""
    return Element("button", **attrs)

def Input(**attrs) -> Element:
    """Create an <input> element."""
    return Element("input", **attrs)

def Textarea(**attrs) -> Element:
    """Create a <textarea> element."""
    return Element("textarea", **attrs)

def Select(**attrs) -> Element:
    """Create a <select> element."""
    return Element("select", **attrs)

def Option(**attrs) -> Element:
    """Create an <option> element."""
    return Element("option", **attrs)

def Label(**attrs) -> Element:
    """Create a <label> element."""
    return Element("label", **attrs)

def Form(**attrs) -> Element:
    """Create a <form> element."""
    return Element("form", **attrs)

def A(**attrs) -> Element:
    """Create an <a> element."""
    return Element("a", **attrs)

def Img(**attrs) -> Element:
    """Create an <img> element."""
    return Element("img", **attrs)

def Ul(**attrs) -> Element:
    """Create a <ul> element."""
    return Element("ul", **attrs)

def Ol(**attrs) -> Element:
    """Create an <ol> element."""
    return Element("ol", **attrs)

def Li(**attrs) -> Element:
    """Create a <li> element."""
    return Element("li", **attrs)

def Table(**attrs) -> Element:
    """Create a <table> element."""
    return Element("table", **attrs)

def Tr(**attrs) -> Element:
    """Create a <tr> element."""
    return Element("tr", **attrs)

def Td(**attrs) -> Element:
    """Create a <td> element."""
    return Element("td", **attrs)

def Th(**attrs) -> Element:
    """Create a <th> element."""
    return Element("th", **attrs)

def Thead(**attrs) -> Element:
    """Create a <thead> element."""
    return Element("thead", **attrs)

def Tbody(**attrs) -> Element:
    """Create a <tbody> element."""
    return Element("tbody", **attrs)

def Header(**attrs) -> Element:
    """Create a <header> element."""
    return Element("header", **attrs)

def Footer(**attrs) -> Element:
    """Create a <footer> element."""
    return Element("footer", **attrs)

def Nav(**attrs) -> Element:
    """Create a <nav> element."""
    return Element("nav", **attrs)

def Section(**attrs) -> Element:
    """Create a <section> element."""
    return Element("section", **attrs)

def Article(**attrs) -> Element:
    """Create an <article> element."""
    return Element("article", **attrs)

def Main(**attrs) -> Element:
    """Create a <main> element."""
    return Element("main", **attrs)

def Pre(**attrs) -> Element:
    """Create a <pre> element."""
    return Element("pre", **attrs)

def Code(**attrs) -> Element:
    """Create a <code> element."""
    return Element("code", **attrs)

def Hr(**attrs) -> Element:
    """Create an <hr> element."""
    return Element("hr", **attrs)

def Br(**attrs) -> Element:
    """Create a <br> element."""
    return Element("br", **attrs)

def Strong(**attrs) -> Element:
    """Create a <strong> element."""
    return Element("strong", **attrs)

def Em(**attrs) -> Element:
    """Create an <em> element."""
    return Element("em", **attrs)
