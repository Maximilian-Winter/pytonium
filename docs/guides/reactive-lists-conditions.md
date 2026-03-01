# Dynamic Lists & Conditional Rendering

This guide covers rendering lists from data with efficient keyed
reconciliation, and conditionally showing or hiding UI sections using
`Show` and `Switch`.

---

## Dynamic Children

Use `.children_from()` to render a list of elements from a reactive data
source.  When the data changes, the framework efficiently adds, removes, and
reorders DOM nodes using keyed reconciliation.

```python
from Pytonium.components import Component, State, Ul, Li

class FruitList(Component):
    fruits = State(["Apple", "Banana", "Cherry"])

    def render(self):
        return (
            Ul().children_from(
                source=lambda: self.fruits,
                key=lambda fruit: fruit,
                render_item=lambda fruit, index: Li().text(fruit),
            )
        )
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | `Callable` | Lambda returning the current list of items. |
| `key` | `Callable` | Function extracting a stable identity from each item. |
| `render_item` | `Callable` | `(item, index) → Element` for each item. |

### How Keyed Reconciliation Works

When the source list changes, the framework:

1. Computes new keys from the updated list.
2. **Removes** items whose keys are no longer present (DOM nodes removed).
3. **Adds** items with new keys (HTML generated and inserted).
4. **Reorders** surviving items if their positions changed.

Each step produces minimal DOM mutation commands.  Existing items that did not
move are left untouched.

!!! tip "Stable keys"
    Keys must be unique and stable across renders.  Use database IDs, UUIDs,
    or other persistent identifiers -- not list indices, which change when
    items are inserted or removed.

### Todo List Example

A more complete example with add, delete, and toggle:

```python
class TodoList(Component):
    todos = State([])
    new_text = State("")
    next_id = State(1)

    def add_todo(self):
        text = self.new_text.strip()
        if not text:
            return
        self.todos = [
            *self.todos,
            {"id": self.next_id, "text": text, "done": False},
        ]
        self.next_id += 1
        self.new_text = ""

    def toggle(self, todo_id):
        self.todos = [
            {**t, "done": not t["done"]} if t["id"] == todo_id else t
            for t in self.todos
        ]

    def delete(self, todo_id):
        self.todos = [t for t in self.todos if t["id"] != todo_id]

    def render(self):
        return (
            Div()
                .child(
                    Div()
                        .child(
                            Input(type="text", placeholder="New todo...")
                                .bind_value(self, "new_text")
                        )
                        .child(Button().text("Add").on_click(self.add_todo))
                )
                .child(
                    Ul().children_from(
                        source=lambda: self.todos,
                        key=lambda t: t["id"],
                        render_item=lambda t, i: (
                            Li()
                                .class_toggle("done", lambda t=t: t["done"])
                                .child(
                                    Span().text(lambda t=t: t["text"])
                                )
                                .child(
                                    Button()
                                        .text("Delete")
                                        .on_click(lambda t=t: self.delete(t["id"]))
                                )
                                .on_click(lambda t=t: self.toggle(t["id"]))
                        ),
                    )
                )
        )
```

!!! warning "Lambda closure capture"
    In `render_item`, use `lambda t=t: ...` to capture the current item.
    Without the default parameter, all lambdas would reference the same loop
    variable and point to the last item.

---

## Conditional Rendering with Show

`Show` renders one of two branches based on a boolean condition.

```python
from Pytonium.components import Show

class LoginStatus(Component):
    logged_in = State(False)
    username = State("Alice")

    def toggle_login(self):
        self.logged_in = not self.logged_in

    def render(self):
        return (
            Div()
                .child(
                    Show(
                        when=lambda: self.logged_in,
                        then=lambda: (
                            Div()
                                .child(P().text(lambda: f"Welcome, {self.username}!"))
                                .child(Button().text("Log out").on_click(self.toggle_login))
                        ),
                        fallback=lambda: (
                            Div()
                                .child(P().text("Please log in."))
                                .child(Button().text("Log in").on_click(self.toggle_login))
                        ),
                    )
                )
        )
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `when` | `Callable` | *(required)* | Lambda returning a boolean. |
| `then` | `Callable` | *(required)* | Lambda returning an Element for `True`. |
| `fallback` | `Callable` | `None` | Optional lambda returning an Element for `False`. |

When the condition changes:

1. The old branch is unmounted (event handlers removed, bindings cleaned up).
2. The new branch is rendered, analyzed for dependencies, and injected.
3. Event handlers for the new branch are registered.

If `fallback` is `None` and the condition is `False`, the placeholder renders
as an empty `<div>`.

---

## Multi-Branch Rendering with Switch

`Switch` renders one of several branches based on a value selector.

```python
from Pytonium.components import Switch

class TabView(Component):
    current_tab = State("home")

    def set_tab(self, tab):
        self.current_tab = tab

    def render(self):
        return (
            Div()
                .child(
                    Div(class_name="tabs")
                        .child(
                            Button()
                                .text("Home")
                                .class_toggle("active", lambda: self.current_tab == "home")
                                .on_click(lambda: self.set_tab("home"))
                        )
                        .child(
                            Button()
                                .text("Settings")
                                .class_toggle("active", lambda: self.current_tab == "settings")
                                .on_click(lambda: self.set_tab("settings"))
                        )
                )
                .child(
                    Switch(lambda: self.current_tab)
                        .case("home", lambda: (
                            Div()
                                .child(H1().text("Home Page"))
                                .child(P().text("Welcome to the home page."))
                        ))
                        .case("settings", lambda: (
                            Div()
                                .child(H1().text("Settings"))
                                .child(P().text("Configure your preferences."))
                        ))
                        .default(lambda: P().text("Page not found."))
                )
        )
```

### Switch API

| Method | Description |
|--------|-------------|
| `Switch(selector)` | Constructor.  `selector` is a lambda returning the value to match. |
| `.case(value, element_fn)` | Register a branch for a specific value.  Returns `self` for chaining. |
| `.default(element_fn)` | Register the fallback branch (when no case matches).  Returns `self`. |

When the selector value changes, `Switch` unmounts the old branch and mounts
the matching new branch, just like `Show`.

---

## Combining Dynamic Content

You can combine `children_from`, `Show`, and `Switch` freely:

```python
class FilterableTodos(Component):
    todos = State([])
    filter_mode = State("all")

    @Computed
    def visible_todos(self):
        if self.filter_mode == "all":
            return self.todos
        elif self.filter_mode == "active":
            return [t for t in self.todos if not t["done"]]
        else:
            return [t for t in self.todos if t["done"]]

    @Computed
    def has_todos(self):
        return len(self.visible_todos) > 0

    def render(self):
        return (
            Div()
                .child(
                    Show(
                        when=lambda: self.has_todos,
                        then=lambda: (
                            Ul().children_from(
                                source=lambda: self.visible_todos,
                                key=lambda t: t["id"],
                                render_item=lambda t, i: Li().text(lambda t=t: t["text"]),
                            )
                        ),
                        fallback=lambda: P().text("No items to show."),
                    )
                )
        )
```

---

## Next Steps

- **[Components API Reference](../api/components.md)** -- Full reference for
  all classes and methods.
- **[Reactive App Example](../examples/reactive-app.md)** -- A complete
  application using all reactive component features.
