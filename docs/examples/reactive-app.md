# Reactive Components App

A comprehensive reactive application demonstrating all major features of the
component system: state, computed properties, events, two-way binding, dynamic
lists, and conditional rendering.

---

## What It Shows

| Section | Features |
|---------|----------|
| **Counter** | State, Computed (`parity`, `doubled`), click events, CSS class toggling |
| **Todo List** | `bind_value`, `children_from` with keyed reconciliation, Computed filters, `keydown` events |
| **Tab Navigation** | `Switch` multi-branch conditional, dynamic class toggling |
| **Login Status** | `Show` conditional with `then`/`fallback` branches |
| **Color Picker** | Reactive styles, multiple `bind_value` inputs, Computed hex/rgb strings |
| **Clock** | State driven from the Python main loop (not from events) |

---

## Running the Example

```bash
pip install Pytonium
cd pytonium_examples/pytonium_example_reactive
python main.py
```

---

## Key Patterns

### Setup & Initialization

```python
from Pytonium import Pytonium
from Pytonium.components import Component

p = Pytonium()
Component.setup(p)           # Register bindings before initialize
p.initialize(url, 960, 900)  # Create browser window

app = ReactiveApp()
app.mount(p, container_id="app")
```

### Counter Component

```python
class CounterSection(Component):
    count = State(0)

    @Computed
    def parity(self):
        return "even" if self.count % 2 == 0 else "odd"

    def increment(self):
        self.count += 1

    def render(self):
        return (
            Div(class_name="card")
                .child(H2().text("Counter"))
                .child(
                    Span(class_name="counter-value")
                        .text(lambda: str(self.count))
                )
                .child(Button().text("+").on_click(self.increment))
                .child(
                    Strong()
                        .text(lambda: self.parity)
                        .class_toggle("even", lambda: self.parity == "even")
                        .class_toggle("odd", lambda: self.parity == "odd")
                )
        )
```

### Todo List with Dynamic Children

```python
class TodoSection(Component):
    todos = State([])
    new_text = State("")
    filter_mode = State("all")

    @Computed
    def visible_todos(self):
        if self.filter_mode == "all":
            return self.todos
        elif self.filter_mode == "active":
            return [t for t in self.todos if not t["done"]]
        else:
            return [t for t in self.todos if t["done"]]

    def render(self):
        return (
            Div()
                .child(
                    Input(type="text", placeholder="What needs to be done?")
                        .bind_value(self, "new_text")
                        .on_keydown(self.on_keydown)
                )
                .child(
                    Ul().children_from(
                        source=lambda: self.visible_todos,
                        key=lambda t: t["id"],
                        render_item=lambda t, i: (
                            Li()
                                .class_toggle("done", lambda t=t: t["done"])
                                .child(Span().text(lambda t=t: t["text"]))
                                .on_click(lambda t=t: self.toggle_todo(t["id"]))
                        ),
                    )
                )
        )
```

### Tab Navigation with Switch

```python
class TabDemoSection(Component):
    current_tab = State("welcome")

    def render(self):
        return (
            Div()
                .child(
                    Button()
                        .text("Welcome")
                        .class_toggle("active", lambda: self.current_tab == "welcome")
                        .on_click(lambda: self.set_tab("welcome"))
                )
                .child(
                    Switch(lambda: self.current_tab)
                        .case("welcome", lambda: P().text("Welcome page content"))
                        .case("features", lambda: P().text("Features page content"))
                        .default(lambda: P().text("Unknown tab"))
                )
        )
```

### Conditional Rendering with Show

```python
class ShowDemoSection(Component):
    logged_in = State(False)

    def render(self):
        return (
            Div()
                .child(
                    Show(
                        when=lambda: self.logged_in,
                        then=lambda: (
                            Div()
                                .child(P().text("Welcome! You are logged in."))
                                .child(Button().text("Log out").on_click(self.toggle_login))
                        ),
                        fallback=lambda: (
                            Div()
                                .child(P().text("You are not logged in."))
                                .child(Button().text("Log in").on_click(self.toggle_login))
                        ),
                    )
                )
        )
```

### Color Picker with Reactive Styles

```python
class ColorPickerSection(Component):
    red = State(187)
    green = State(154)
    blue = State(247)

    @Computed
    def hex_color(self):
        return f"#{self.red:02x}{self.green:02x}{self.blue:02x}"

    @Computed
    def rgb_string(self):
        return f"rgb({self.red}, {self.green}, {self.blue})"

    def render(self):
        return (
            Div()
                .child(
                    Div(class_name="color-preview")
                        .style("background-color", lambda: self.rgb_string)
                )
                .child(
                    Span(class_name="color-value")
                        .text(lambda: self.hex_color)
                )
        )
```

---

## Source Code

The full example (~760 lines including CSS) is in the repository at
[`pytonium_examples/pytonium_example_reactive/main.py`](https://github.com/Maximilian-Winter/pytonium/tree/master/pytonium_examples/pytonium_example_reactive/main.py).
