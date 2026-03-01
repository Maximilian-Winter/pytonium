# Reactive Elements

Elements are the building blocks of reactive component UIs.  The `Element`
class provides a fluent builder API for constructing HTML trees with reactive
bindings, and convenience constructors like `Div()`, `Button()`, and `Input()`
make the code readable and concise.

---

## The Builder Pattern

Every element method returns `self`, so you can chain calls:

```python
from Pytonium.components import Div, H1, P, Button

tree = (
    Div(class_name="card")
        .child(H1().text("Hello"))
        .child(P().text("This is a paragraph."))
        .child(Button().text("Click me"))
)
```

Indentation is optional but recommended for readability.  The parentheses
around the expression allow multi-line chaining without backslash continuations.

---

## Available Elements

Convenience constructors are plain functions that return `Element(tag)`.  All
accept `**attrs` for static HTML attributes.

### Text & Container

| Constructor | HTML Tag | Notes |
|-------------|----------|-------|
| `Div()` | `<div>` | Generic container |
| `Span()` | `<span>` | Inline container |
| `P()` | `<p>` | Paragraph |
| `Pre()` | `<pre>` | Preformatted text |
| `Code()` | `<code>` | Inline code |
| `Strong()` | `<strong>` | Bold text |
| `Em()` | `<em>` | Italic text |

### Headings

| Constructor | HTML Tag |
|-------------|----------|
| `H1()` | `<h1>` |
| `H2()` | `<h2>` |
| `H3()` | `<h3>` |
| `H4()` | `<h4>` |
| `H5()` | `<h5>` |
| `H6()` | `<h6>` |

### Form Elements

| Constructor | HTML Tag | Notes |
|-------------|----------|-------|
| `Button()` | `<button>` | Clickable button |
| `Input()` | `<input>` | Void element (no children) |
| `Textarea()` | `<textarea>` | Multi-line text input |
| `Select()` | `<select>` | Dropdown |
| `Option()` | `<option>` | Dropdown option |
| `Label()` | `<label>` | Form label |
| `Form()` | `<form>` | Form container |

### Lists

| Constructor | HTML Tag |
|-------------|----------|
| `Ul()` | `<ul>` |
| `Ol()` | `<ol>` |
| `Li()` | `<li>` |

### Tables

| Constructor | HTML Tag |
|-------------|----------|
| `Table()` | `<table>` |
| `Thead()` | `<thead>` |
| `Tbody()` | `<tbody>` |
| `Tr()` | `<tr>` |
| `Th()` | `<th>` |
| `Td()` | `<td>` |

### Semantic

| Constructor | HTML Tag |
|-------------|----------|
| `Header()` | `<header>` |
| `Footer()` | `<footer>` |
| `Nav()` | `<nav>` |
| `Section()` | `<section>` |
| `Article()` | `<article>` |
| `Main()` | `<main>` |

### Misc

| Constructor | HTML Tag | Notes |
|-------------|----------|-------|
| `A()` | `<a>` | Hyperlink |
| `Img()` | `<img>` | Void element |
| `Hr()` | `<hr>` | Void element |
| `Br()` | `<br>` | Void element |

!!! tip "Custom elements"
    For any tag not listed above, use `Element("my-tag")` directly.

---

## Text Content

Use `.text()` to set an element's text content.

### Static Text

```python
H1().text("Welcome to Pytonium")
```

### Reactive Text

Pass a lambda to make it reactive.  The framework tracks which `State` fields
the lambda reads and updates the DOM when they change.

```python
class Greeter(Component):
    name = State("World")

    def render(self):
        return H1().text(lambda: f"Hello, {self.name}!")
```

When `self.name` changes, only the `<h1>` text content is updated -- nothing
else in the DOM is touched.

---

## Attributes

### Static Attributes

Pass attributes as keyword arguments to the constructor or use `.attr()`:

```python
# Via constructor kwargs
Input(type="text", placeholder="Enter your name")

# Via .attr()
A().attr("href", "https://example.com").text("Visit")
```

### Reactive Attributes

Pass a lambda to `.attr()` for reactive attributes:

```python
Img().attr("src", lambda: self.avatar_url)
```

### HTML ID

Use `.id()` as a shorthand for setting the HTML `id` attribute:

```python
Div().id("main-content")
```

### Attribute Name Conversion

Python keyword arguments are automatically converted to HTML attribute names:

| Python | HTML | Rule |
|--------|------|------|
| `class_name` | `class` | Reserved word |
| `html_for` or `for_` | `for` | Reserved word |
| `data_value` | `data-value` | `data_*` → `data-*` |
| `aria_label` | `aria-label` | `aria_*` → `aria-*` |

---

## CSS Classes

### Static Classes

Use `.class_name()` to add one or more CSS classes (space-separated):

```python
Div(class_name="card primary")
# or
Div().class_name("card primary")
```

### Reactive Class Toggling

Use `.class_toggle()` to conditionally add or remove a class based on a
reactive condition:

```python
class TabBar(Component):
    active_tab = State("home")

    def render(self):
        return (
            Div()
                .child(
                    Button()
                        .text("Home")
                        .class_toggle("active", lambda: self.active_tab == "home")
                )
                .child(
                    Button()
                        .text("Settings")
                        .class_toggle("active", lambda: self.active_tab == "settings")
                )
        )
```

When `active_tab` changes, only the `classList.toggle()` call is executed in
the browser -- the element is not recreated.

---

## Inline Styles

### Static Styles

```python
Div().style("padding", "20px").style("background", "#1a1a2e")
```

### Reactive Styles

```python
class ColorPicker(Component):
    color = State("#ff0000")

    def render(self):
        return Div().style("background-color", lambda: self.color)
```

---

## Children

### Single Child

```python
Div().child(H1().text("Title"))
```

### Multiple Children

```python
Div().children(
    H1().text("Title"),
    P().text("First paragraph"),
    P().text("Second paragraph"),
)
```

### Nesting

```python
Div(class_name="layout")
    .child(
        Header()
            .child(H1().text("My App"))
            .child(Nav().child(Button().text("Menu")))
    )
    .child(
        Main()
            .child(P().text("Content goes here"))
    )
    .child(
        Footer()
            .child(P().text("2026"))
    )
```

---

## Reactive Bindings Explained

Every method that accepts a lambda creates a **reactive binding**.  During
`mount()`, the framework:

1. Executes the lambda once to get the initial value.
2. Records which `State` fields were accessed (dependency tracking).
3. Stores a `Binding` that maps `(state_field) → (DOM mutation)`.

When a `State` field changes later, the framework:

1. Looks up all bindings for that field.
2. Re-evaluates each lambda.
3. Generates a minimal JavaScript string (e.g., `el.textContent="new value"`).
4. Sends it to the browser in a single `execute_javascript()` call.

!!! note "Lambda vs function reference"
    Always use lambdas (or functions) for reactive values, not bare expressions.
    `lambda: self.count` is reactive; `self.count` is evaluated once and never
    updates.

---

## Complete Example

A styled user card with reactive bindings for every feature:

```python
class UserCard(Component):
    name = State("Alice")
    role = State("Developer")
    active = State(True)
    theme = State("dark")

    def toggle_active(self):
        self.active = not self.active

    def render(self):
        return (
            Div(class_name="user-card")
                .class_toggle("active", lambda: self.active)
                .class_toggle("dark-theme", lambda: self.theme == "dark")
                .style("opacity", lambda: "1" if self.active else "0.5")
                .child(
                    H2()
                        .text(lambda: self.name)
                        .style("color", lambda: "#7aa2f7" if self.active else "#666")
                )
                .child(
                    P()
                        .text(lambda: f"Role: {self.role}")
                        .attr("title", lambda: f"{self.name} - {self.role}")
                )
                .child(
                    Button()
                        .text(lambda: "Deactivate" if self.active else "Activate")
                        .on_click(self.toggle_active)
                )
        )
```

This component uses:

- `.class_toggle()` for conditional CSS classes
- `.style()` with a lambda for reactive inline styles
- `.text()` with lambdas for reactive text content
- `.attr()` with a lambda for a reactive tooltip
- `.on_click()` for event handling

---

## Next Steps

- **[Events & Computed](reactive-interactivity.md)** -- Add interactivity
  with event handlers, input binding, and computed properties.
- **[Dynamic Lists & Conditions](reactive-lists-conditions.md)** -- Render
  lists from data and conditionally show/hide UI sections.
