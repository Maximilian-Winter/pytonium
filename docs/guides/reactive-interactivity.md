# Events & Computed Properties

This guide covers event handling, two-way input binding, computed cached
properties, and update batching -- everything that makes reactive components
interactive.

---

## Event Handling

Register event handlers using `.on_*()` methods on any element.

```python
class App(Component):
    message = State("")

    def handle_click(self):
        self.message = "Button clicked!"

    def render(self):
        return (
            Div()
                .child(Button().text("Click me").on_click(self.handle_click))
                .child(P().text(lambda: self.message))
        )
```

### Available Event Methods

| Method | DOM Event | Common use |
|--------|-----------|------------|
| `.on_click(handler)` | `click` | Buttons, links, clickable elements |
| `.on_dblclick(handler)` | `dblclick` | Double-click actions |
| `.on_keydown(handler)` | `keydown` | Keyboard shortcuts, Enter to submit |
| `.on_keyup(handler)` | `keyup` | Key release detection |
| `.on_input(handler)` | `input` | Text input changes (fires on every keystroke) |
| `.on_change(handler)` | `change` | Select dropdowns, checkboxes (fires on commit) |
| `.on_submit(handler)` | `submit` | Form submission |
| `.on_mouseenter(handler)` | `mouseenter` | Hover start |
| `.on_mouseleave(handler)` | `mouseleave` | Hover end |
| `.on_focus(handler)` | `focus` | Input focus |
| `.on_blur(handler)` | `blur` | Input blur |

---

## EventData

Event handlers can optionally receive an `EventData` object with information
about the DOM event.

```python
from Pytonium.components import EventData

def handle_keydown(self, event: EventData):
    if event.key == "Enter":
        self.submit_form()
    elif event.key == "Escape":
        self.cancel()
```

### EventData Properties

| Property | Type | Description |
|----------|------|-------------|
| `type` | `str` | Event type (e.g., `"click"`, `"keydown"`) |
| `value` | `str` | `e.target.value` (for input/textarea/select) |
| `key` | `str` | Keyboard key name (e.g., `"Enter"`, `"Escape"`, `"a"`) |
| `key_code` | `int` | Keyboard key code |
| `client_x` | `float` | Mouse X position relative to viewport |
| `client_y` | `float` | Mouse Y position relative to viewport |
| `shift_key` | `bool` | Whether Shift was held |
| `ctrl_key` | `bool` | Whether Ctrl was held |
| `alt_key` | `bool` | Whether Alt was held |
| `meta_key` | `bool` | Whether Meta/Cmd was held |
| `checked` | `bool` | `e.target.checked` (for checkboxes) |

---

## Handler Signatures

The framework inspects handler signatures to determine whether to pass event
data.

### No Arguments

If the handler takes no arguments, it is called with no event data:

```python
def increment(self):
    self.count += 1

# In render():
Button().on_click(self.increment)
```

### With EventData

If the handler has a parameter (without a default value), it receives
`EventData`:

```python
def on_key(self, event):
    if event.key == "Enter":
        self.submit()

# In render():
Input().on_keydown(self.on_key)
```

### Lambda Closures

When using lambdas to capture loop variables, use default parameter values.
Parameters with defaults are **not** treated as event data slots:

```python
# Correct: t=t captures the current value of t
.on_click(lambda t=t: self.toggle(t["id"]))

# Wrong: t would be overwritten with EventData
.on_click(lambda t: self.toggle(t["id"]))
```

!!! warning "Lambda closure trap"
    Without the `t=t` default, Python's closure captures the loop variable
    by reference.  All handlers would point to the last item.  The `t=t`
    pattern both fixes the closure and tells the framework not to pass event
    data for that parameter.

---

## Two-Way Input Binding

`.bind_value()` creates a two-way binding between an input element and a state
field:

```python
class SearchForm(Component):
    query = State("")

    def render(self):
        return (
            Div()
                .child(
                    Input(type="text", placeholder="Search...")
                        .bind_value(self, "query")
                )
                .child(P().text(lambda: f"Searching for: {self.query}"))
        )
```

This does two things:

1. **Python → JS**: Sets the input's `value` from the state field (reactive).
2. **JS → Python**: Registers an `input` event listener that updates the state
   field when the user types.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `component` | `Component` | *(required)* | The component instance owning the state field. |
| `field_name` | `str` | *(required)* | Name of the `State` field to bind. |
| `debounce_ms` | `int` | `0` | Debounce delay in milliseconds (0 = frame-buffered). |

### Debounced Input

For high-frequency events, add a debounce delay to reduce IPC calls:

```python
Input().bind_value(self, "search_text", debounce_ms=300)
```

With `debounce_ms=300`, the JavaScript side waits 300ms after the last
keystroke before sending the value to Python.

With `debounce_ms=0` (default), the value is sent on the next
`requestAnimationFrame` (~16ms at 60fps).

---

## Computed Properties

`@Computed` decorates a method to create a cached, auto-invalidating derived
property.

```python
from Pytonium.components import Component, State, Computed

class TodoApp(Component):
    todos = State([])

    @Computed
    def remaining(self):
        return sum(1 for t in self.todos if not t["done"])

    @Computed
    def summary(self):
        return f"{self.remaining} of {len(self.todos)} items left"

    def render(self):
        return P().text(lambda: self.summary)
```

### How Computed Works

1. On first access, the method is called and its return value is cached.
2. The framework tracks which `State` fields were read during computation.
3. When any of those fields change, the cached value is invalidated.
4. On next access, the method is re-evaluated and the new value is cached.
5. DOM nodes bound to a `Computed` property update automatically.

### Computed Chains

Computed properties can depend on other Computed properties:

```python
@Computed
def total_price(self):
    return sum(item["price"] for item in self.cart)

@Computed
def tax(self):
    return self.total_price * 0.1  # Depends on total_price

@Computed
def grand_total(self):
    return self.total_price + self.tax  # Depends on both
```

When `cart` changes, all three are invalidated transitively.

---

## Update Batching

When an event handler changes multiple state fields, the framework batches
all updates into a single DOM mutation:

```python
def submit_order(self):
    self.order_status = "submitted"
    self.cart = []
    self.total = 0
    self.message = "Order placed!"
    # All four changes produce ONE JavaScript batch
```

The event router wraps every handler call in a batch context.  All state
changes within the handler accumulate `UpdateCommand` objects.  When the
handler returns, the accumulated commands are compiled into a single
JavaScript string and sent in one `execute_javascript()` call.

This means:

- Multiple state changes in one handler = one IPC round-trip.
- The DOM is only mutated once, avoiding intermediate visual states.
- The `on_update()` lifecycle hook fires once with all changed field names.

---

## Preventing Default Behavior

Event handlers can optionally prevent the browser's default action:

```python
Form().on_submit(self.handle_submit)
```

To prevent default on form submission (page reload), pass `prevent_default`
in the event configuration.  The `.on_submit()` method sets this automatically
for `submit` events.

---

## Complete Example

A form with input binding, computed validation, and debounced search:

```python
class RegistrationForm(Component):
    username = State("")
    email = State("")
    password = State("")

    @Computed
    def is_valid(self):
        return (
            len(self.username) >= 3
            and "@" in self.email
            and len(self.password) >= 8
        )

    @Computed
    def validation_message(self):
        issues = []
        if len(self.username) < 3:
            issues.append("Username must be at least 3 characters")
        if "@" not in self.email:
            issues.append("Email must contain @")
        if len(self.password) < 8:
            issues.append("Password must be at least 8 characters")
        return "; ".join(issues) if issues else "All fields valid"

    def submit(self):
        if self.is_valid:
            print(f"Registering {self.username} ({self.email})")

    def render(self):
        return (
            Div(class_name="form")
                .child(
                    Div()
                        .child(Label().text("Username"))
                        .child(Input(type="text").bind_value(self, "username"))
                )
                .child(
                    Div()
                        .child(Label().text("Email"))
                        .child(Input(type="email").bind_value(self, "email"))
                )
                .child(
                    Div()
                        .child(Label().text("Password"))
                        .child(
                            Input(type="password")
                                .bind_value(self, "password")
                        )
                )
                .child(
                    P()
                        .text(lambda: self.validation_message)
                        .style("color", lambda: "#9ece6a" if self.is_valid else "#f7768e")
                )
                .child(
                    Button()
                        .text("Register")
                        .on_click(self.submit)
                        .class_toggle("disabled", lambda: not self.is_valid)
                )
        )
```

---

## Next Steps

- **[Dynamic Lists & Conditions](reactive-lists-conditions.md)** -- Render
  lists from data and conditionally show/hide UI sections.
- **[Components API Reference](../api/components.md)** -- Full reference for
  all classes and methods.
