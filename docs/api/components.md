# Components API Reference

Complete reference for the Pytonium reactive components system.

```python
from Pytonium.components import (
    Component, State, Computed, Element,
    Div, Span, P, H1, H2, H3, H4, H5, H6,
    Button, Input, Textarea, Select, Option, Label, Form,
    A, Img, Ul, Ol, Li, Table, Tr, Td, Th, Thead, Tbody,
    Header, Footer, Nav, Section, Article, Main,
    Pre, Code, Hr, Br, Strong, Em,
    Show, Switch, EventData,
)
```

---

## Component

Base class for reactive components.  Subclass it, define `State` fields, and
implement `render()`.

### `setup`

<div class="api-method" markdown>

```python
@staticmethod
Component.setup(pytonium) -> None
```

</div>

Pre-register event handlers and the page-ready sentinel with CEF.  **Must** be
called before `pytonium.initialize()`.

| Name | Type | Description |
|------|------|-------------|
| `pytonium` | `Pytonium` | A Pytonium instance that has **not** been initialized yet. |

---

### `__init__`

<div class="api-method" markdown>

```python
Component(**kwargs)
```

</div>

Create a component instance.  Keyword arguments matching `State` field names
set initial values.

```python
counter = Counter(count=10)
```

---

### `render`

<div class="api-method" markdown>

```python
render() -> Element
```

</div>

Return the element tree for this component.  Called once during `mount()`.
Must be overridden by subclasses.

---

### `mount`

<div class="api-method" markdown>

```python
mount(pytonium, container_id: str | None = None) -> None
```

</div>

Mount the component into a browser.  Calls `render()`, injects HTML, analyzes
dependencies, and registers events.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `pytonium` | `Pytonium` | *(required)* | Pytonium instance with an initialized browser. |
| `container_id` | `str` or `None` | `None` | HTML element ID to mount into.  If `None`, replaces `document.body`. |

---

### `unmount`

<div class="api-method" markdown>

```python
unmount() -> None
```

</div>

Unmount the component.  Removes event handlers, cleans up the dependency graph,
and calls `on_unmount()`.

---

### `on_mount`

<div class="api-method" markdown>

```python
on_mount() -> None
```

</div>

Lifecycle hook called after `mount()` completes.  Override to initialize
resources.

---

### `on_update`

<div class="api-method" markdown>

```python
on_update(changed_fields: set[str]) -> None
```

</div>

Lifecycle hook called after state changes are applied to the DOM.

| Name | Type | Description |
|------|------|-------------|
| `changed_fields` | `set[str]` | Names of the `State` fields that changed. |

---

### `on_unmount`

<div class="api-method" markdown>

```python
on_unmount() -> None
```

</div>

Lifecycle hook called when the component is unmounted.  Override to clean up
resources.

---

## State

Reactive state descriptor.  Declare as a class attribute on a `Component`
subclass.

<div class="api-method" markdown>

```python
State(default=None)
```

</div>

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `default` | `Any` | `None` | Default value for this field. |

```python
class Counter(Component):
    count = State(0)
    name = State("World")
    items = State([])
```

Reads trigger dependency tracking during `render()`.  Writes trigger DOM
updates through the dependency graph.

!!! note "Mutable defaults"
    `State([])` shares the same list instance across all component instances.
    For per-instance mutable defaults, set them in `__init__` or `on_mount`.

---

## Computed

Cached, auto-invalidating derived property.

<div class="api-method" markdown>

```python
@Computed
def property_name(self) -> Any:
    ...
```

</div>

The return value is cached until any upstream `State` field changes.  DOM
bindings that reference the `Computed` property update automatically.

```python
class Cart(Component):
    items = State([])

    @Computed
    def total(self):
        return sum(item["price"] for item in self.items)
```

---

## Element

HTML element builder with fluent API.

### Constructor

<div class="api-method" markdown>

```python
Element(tag: str, **attrs) -> Element
```

</div>

Create an element with the given HTML tag.  Keyword arguments set static HTML
attributes.

| Name | Type | Description |
|------|------|-------------|
| `tag` | `str` | HTML tag name. |
| `**attrs` | `str` | Static HTML attributes (Python names converted automatically). |

```python
Element("div", class_name="container", data_role="main")
# → <div class="container" data-role="main" data-pyt-id="...">
```

---

### `child`

<div class="api-method" markdown>

```python
child(element: Element) -> Element
```

</div>

Append a single child element.  Returns `self`.

---

### `children`

<div class="api-method" markdown>

```python
children(*elements: Element) -> Element
```

</div>

Append multiple child elements.  Returns `self`.

---

### `text`

<div class="api-method" markdown>

```python
text(content: str | Callable) -> Element
```

</div>

Set text content.  Pass a string for static content or a lambda for reactive
content.

---

### `attr`

<div class="api-method" markdown>

```python
attr(name: str, value: str | Callable) -> Element
```

</div>

Set an HTML attribute.  Pass a lambda for reactive attributes.

---

### `id`

<div class="api-method" markdown>

```python
id(html_id: str) -> Element
```

</div>

Set the HTML `id` attribute.

---

### `class_name`

<div class="api-method" markdown>

```python
class_name(name: str) -> Element
```

</div>

Add one or more static CSS classes (space-separated).

---

### `class_toggle`

<div class="api-method" markdown>

```python
class_toggle(name: str, condition: Callable) -> Element
```

</div>

Toggle a CSS class based on a reactive boolean condition.

| Name | Type | Description |
|------|------|-------------|
| `name` | `str` | CSS class name. |
| `condition` | `Callable` | Lambda returning `True` (add) or `False` (remove). |

---

### `style`

<div class="api-method" markdown>

```python
style(prop: str, value: str | Callable) -> Element
```

</div>

Set an inline style property.  Pass a lambda for reactive styles.

| Name | Type | Description |
|------|------|-------------|
| `prop` | `str` | CSS property name (e.g., `"background-color"`, `"font-size"`). |
| `value` | `str` or `Callable` | Value string or reactive lambda. |

---

### `bind_value`

<div class="api-method" markdown>

```python
bind_value(component: Component, field_name: str, debounce_ms: int = 0) -> Element
```

</div>

Two-way binding between an input element's value and a `State` field.

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `component` | `Component` | *(required)* | Component instance owning the state field. |
| `field_name` | `str` | *(required)* | Name of the `State` field. |
| `debounce_ms` | `int` | `0` | Debounce delay in ms (0 = frame-buffered). |

---

### Event Methods

All event methods take a single `handler` parameter and return `self`.

<div class="api-method" markdown>

```python
on_click(handler: Callable) -> Element
on_dblclick(handler: Callable) -> Element
on_keydown(handler: Callable) -> Element
on_keyup(handler: Callable) -> Element
on_input(handler: Callable) -> Element
on_change(handler: Callable) -> Element
on_submit(handler: Callable) -> Element
on_mouseenter(handler: Callable) -> Element
on_mouseleave(handler: Callable) -> Element
on_focus(handler: Callable) -> Element
on_blur(handler: Callable) -> Element
```

</div>

Handlers may take zero arguments or one `EventData` argument.

---

### `children_from`

<div class="api-method" markdown>

```python
children_from(source: Callable, key: Callable, render_item: Callable) -> Element
```

</div>

Render dynamic children from a reactive list source with keyed reconciliation.

| Name | Type | Description |
|------|------|-------------|
| `source` | `Callable` | Lambda returning the current list. |
| `key` | `Callable` | Function extracting a stable key from each item. |
| `render_item` | `Callable` | `(item, index) → Element` for each item. |

---

### `to_html`

<div class="api-method" markdown>

```python
to_html() -> str
```

</div>

Generate the HTML string with `data-pyt-id` markers.  Reactive bindings are
evaluated once for initial values.

---

## Convenience Constructors

Functions that return `Element(tag)`.  All accept `**attrs`.

| Text & Container | Headings | Form | Lists | Tables | Semantic | Misc |
|-----------------|----------|------|-------|--------|----------|------|
| `Div` | `H1` | `Button` | `Ul` | `Table` | `Header` | `A` |
| `Span` | `H2` | `Input` | `Ol` | `Thead` | `Footer` | `Img` |
| `P` | `H3` | `Textarea` | `Li` | `Tbody` | `Nav` | `Hr` |
| `Pre` | `H4` | `Select` | | `Tr` | `Section` | `Br` |
| `Code` | `H5` | `Option` | | `Td` | `Article` | |
| `Strong` | `H6` | `Label` | | `Th` | `Main` | |
| `Em` | | `Form` | | | | |

---

## EventData

Deserialized DOM event data passed to Python handlers.

<div class="api-method" markdown>

```python
@dataclass
class EventData:
    type: str = ""
    value: str = ""
    key: str = ""
    key_code: int = 0
    client_x: float = 0.0
    client_y: float = 0.0
    shift_key: bool = False
    ctrl_key: bool = False
    alt_key: bool = False
    meta_key: bool = False
    checked: bool = False
```

</div>

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | Event type (e.g., `"click"`, `"keydown"`). |
| `value` | `str` | `e.target.value` (input/textarea/select elements). |
| `key` | `str` | Keyboard key name (e.g., `"Enter"`, `"Escape"`). |
| `key_code` | `int` | Keyboard key code. |
| `client_x` | `float` | Mouse X relative to viewport. |
| `client_y` | `float` | Mouse Y relative to viewport. |
| `shift_key` | `bool` | Shift key held. |
| `ctrl_key` | `bool` | Ctrl key held. |
| `alt_key` | `bool` | Alt key held. |
| `meta_key` | `bool` | Meta/Cmd key held. |
| `checked` | `bool` | `e.target.checked` (checkboxes). |

---

## Show

Conditional rendering element with two branches.

<div class="api-method" markdown>

```python
Show(when: Callable, then: Callable, fallback: Callable | None = None)
```

</div>

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `when` | `Callable` | *(required)* | Lambda returning `True` or `False`. |
| `then` | `Callable` | *(required)* | Lambda returning an Element for the `True` branch. |
| `fallback` | `Callable` or `None` | `None` | Lambda returning an Element for the `False` branch. |

Renders as a `<div>` placeholder.  When the condition changes, the old branch
is unmounted and the new branch is mounted in its place.

---

## Switch

Multi-branch conditional rendering element.

<div class="api-method" markdown>

```python
Switch(selector: Callable)
```

</div>

| Name | Type | Description |
|------|------|-------------|
| `selector` | `Callable` | Lambda returning the value to match against cases. |

### `case`

<div class="api-method" markdown>

```python
case(value: Any, element_fn: Callable) -> Switch
```

</div>

Register a branch for a specific selector value.  Returns `self` for chaining.

### `default`

<div class="api-method" markdown>

```python
default(element_fn: Callable) -> Switch
```

</div>

Register the fallback branch (when no case matches).  Returns `self`.

---

## EventRouter

Routes DOM events from JavaScript to Python handlers.  Typically used
internally by `Component`, but available for advanced use.

### `prepare`

<div class="api-method" markdown>

```python
@classmethod
EventRouter.prepare(pytonium) -> None
```

</div>

Pre-register the global event handler with CEF.  Called by `Component.setup()`.
Must be called before `pytonium.initialize()`.

### `register_events`

<div class="api-method" markdown>

```python
register_events(element: Element, bind_to_js: bool = True) -> None
```

</div>

Register event listeners for an element tree.  Walks the tree recursively.

### `cleanup`

<div class="api-method" markdown>

```python
cleanup() -> None
```

</div>

Remove all handlers and unregister this router.

---

## DependencyTracker

Tracks dependencies between `State` fields and DOM bindings.  All methods are
classmethods operating on shared class state.

### `reset`

<div class="api-method" markdown>

```python
@classmethod
DependencyTracker.reset() -> None
```

</div>

Reset all tracking state.  Used in tests and between mounts.

### `register_component`

<div class="api-method" markdown>

```python
@classmethod
DependencyTracker.register_component(component: Component) -> None
```

</div>

Register a component for dependency tracking.  Called during `mount()`.

### `unregister_component`

<div class="api-method" markdown>

```python
@classmethod
DependencyTracker.unregister_component(component: Component) -> None
```

</div>

Remove all dependency mappings for a component.  Called during `unmount()`.

---

## UpdateType

Enum of DOM mutation types used internally by the `MutationCompiler`.

```python
class UpdateType(Enum):
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
```
