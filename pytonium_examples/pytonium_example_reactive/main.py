"""Pytonium Reactive Components — Comprehensive Example

Demonstrates every major feature of the reactive component system:

  - State descriptors with automatic DOM updates
  - Computed properties (cached, auto-invalidating)
  - Element builder with fluent API
  - Event handling (click, keydown, input)
  - Two-way input binding (bind_value)
  - Dynamic lists with keyed reconciliation (children_from)
  - Conditional rendering (Show / Switch)
  - CSS class toggling
  - Component lifecycle hooks
  - Update batching (multiple state changes in one handler → single DOM update)

Run after building:
    pip install dist/pytonium-*.whl --force-reinstall
    python pytonium_examples/pytonium_example_reactive/main.py
"""

import os
import time
from datetime import datetime

from Pytonium import Pytonium
from Pytonium.components import (
    Component, State, Computed,
    Div, H1, H2, H3, Span, P, Button, Input, Ul, Li, Hr,
    Header, Footer, Section, Nav, Strong, Em,
    Show, Switch,
)


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

APP_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #0f0f1a;
    color: #e0e0f0;
    min-height: 100vh;
}

.app {
    max-width: 900px;
    margin: 0 auto;
    padding: 24px;
}

.app-header {
    text-align: center;
    padding: 32px 0 24px;
    border-bottom: 1px solid #2a2a4a;
    margin-bottom: 24px;
}
.app-header h1 { color: #bb9af7; font-size: 28px; }
.app-header p { color: #7a7aaa; margin-top: 8px; font-size: 14px; }

.clock { color: #7aa2f7; font-size: 13px; margin-top: 4px; }

/* Navigation tabs */
.nav { display: flex; gap: 8px; margin-bottom: 24px; }
.nav button {
    padding: 8px 20px;
    border: 1px solid #3a3a5a;
    border-radius: 6px;
    background: #1a1a2e;
    color: #a0a0c0;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.15s;
}
.nav button:hover { background: #2a2a4a; color: #e0e0f0; }
.nav button.active {
    background: #7b5ea7;
    color: #fff;
    border-color: #9b7ec7;
}

/* Cards */
.card {
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 16px;
}
.card h2, .card h3 { color: #bb9af7; margin-bottom: 12px; font-size: 18px; }

/* Counter */
.counter-row { display: flex; align-items: center; gap: 16px; }
.counter-value {
    font-size: 48px;
    font-weight: 700;
    color: #7aa2f7;
    min-width: 100px;
    text-align: center;
}
.counter-btns { display: flex; flex-direction: column; gap: 6px; }
.counter-btns button {
    padding: 6px 18px;
    border: 1px solid #3a3a5a;
    border-radius: 6px;
    background: #1a1a2e;
    color: #e0e0f0;
    cursor: pointer;
    font-size: 16px;
    transition: background 0.15s;
}
.counter-btns button:hover { background: #3a3a5a; }
.counter-info { color: #7a7aaa; font-size: 13px; margin-top: 8px; }
.even { color: #9ece6a; }
.odd { color: #ff9e64; }

/* Todo */
.todo-input-row { display: flex; gap: 8px; margin-bottom: 16px; }
.todo-input-row input {
    flex: 1;
    padding: 10px 14px;
    border: 1px solid #3a3a5a;
    border-radius: 6px;
    background: #12121e;
    color: #e0e0f0;
    font-size: 14px;
    outline: none;
}
.todo-input-row input:focus { border-color: #7b5ea7; }
.todo-input-row button {
    padding: 10px 20px;
    background: #7b5ea7;
    border: none;
    border-radius: 6px;
    color: #fff;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
}
.todo-input-row button:hover { background: #9b7ec7; }

.todo-filters { display: flex; gap: 6px; margin-bottom: 12px; }
.todo-filters button {
    padding: 4px 12px;
    border: 1px solid #3a3a5a;
    border-radius: 4px;
    background: transparent;
    color: #a0a0c0;
    cursor: pointer;
    font-size: 12px;
}
.todo-filters button.active { background: #7b5ea7; color: #fff; border-color: #9b7ec7; }

.todo-list { list-style: none; }
.todo-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-bottom: 1px solid #1f1f3a;
    cursor: pointer;
    transition: background 0.1s;
}
.todo-item:hover { background: #1f1f3a; }
.todo-item.done { opacity: 0.5; }
.todo-item.done .todo-text { text-decoration: line-through; }
.todo-check { font-size: 18px; }
.todo-text { flex: 1; }
.todo-delete {
    background: none;
    border: none;
    color: #f7768e;
    cursor: pointer;
    font-size: 14px;
    opacity: 0;
    transition: opacity 0.15s;
}
.todo-item:hover .todo-delete { opacity: 1; }

.todo-summary { color: #7a7aaa; font-size: 13px; margin-top: 8px; }

/* Color picker */
.color-section { margin-top: 12px; }
.color-preview {
    width: 60px; height: 60px;
    border-radius: 8px;
    border: 2px solid #3a3a5a;
    display: inline-block;
    vertical-align: middle;
    margin-right: 12px;
}
.color-sliders { margin-top: 12px; }
.color-sliders label {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
    font-size: 13px;
    color: #a0a0c0;
}
.color-sliders input[type="range"] { flex: 1; }
.color-value {
    font-family: 'Consolas', monospace;
    color: #7aa2f7;
    font-size: 14px;
    margin-top: 8px;
}

/* Footer */
.app-footer {
    text-align: center;
    color: #4a4a6a;
    font-size: 12px;
    padding: 24px 0;
    border-top: 1px solid #2a2a4a;
    margin-top: 24px;
}
"""


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------


class CounterSection(Component):
    """Demonstrates: State, Computed, click events, class toggling."""

    count = State(0)

    @Computed
    def parity(self):
        return "even" if self.count % 2 == 0 else "odd"

    @Computed
    def doubled(self):
        return self.count * 2

    def increment(self):
        self.count += 1

    def decrement(self):
        self.count -= 1

    def reset(self):
        self.count = 0

    def render(self):
        return (
            Div(class_name="card")
                .child(H2().text("Counter"))
                .child(
                    Div(class_name="counter-row")
                        .child(
                            Div(class_name="counter-btns")
                                .child(Button().text("+").on_click(self.increment))
                                .child(Button().text("-").on_click(self.decrement))
                                .child(Button().text("Reset").on_click(self.reset))
                        )
                        .child(
                            Span(class_name="counter-value")
                                .text(lambda: str(self.count))
                        )
                )
                .child(
                    P(class_name="counter-info")
                        .child(
                            Span()
                                .text(lambda: f"The number {self.count} is ")
                        )
                        .child(
                            Strong()
                                .text(lambda: self.parity)
                                .class_toggle("even", lambda: self.parity == "even")
                                .class_toggle("odd", lambda: self.parity == "odd")
                        )
                        .child(
                            Span()
                                .text(lambda: f". Doubled: {self.doubled}")
                        )
                )
        )


class TodoSection(Component):
    """Demonstrates: bind_value, children_from, keyed reconciliation,
    Computed properties, conditional rendering, keydown events."""

    todos = State([])
    new_text = State("")
    filter_mode = State("all")
    next_id = State(1)

    @Computed
    def visible_todos(self):
        if self.filter_mode == "all":
            return self.todos
        elif self.filter_mode == "active":
            return [t for t in self.todos if not t["done"]]
        else:
            return [t for t in self.todos if t["done"]]

    @Computed
    def remaining(self):
        return sum(1 for t in self.todos if not t["done"])

    @Computed
    def total(self):
        return len(self.todos)

    def add_todo(self):
        text = self.new_text.strip() if isinstance(self.new_text, str) else ""
        if not text:
            return
        new_todo = {"id": self.next_id, "text": text, "done": False}
        self.todos = [*self.todos, new_todo]
        self.next_id = self.next_id + 1
        self.new_text = ""

    def on_keydown(self, e):
        if e.key == "Enter":
            self.add_todo()

    def toggle_todo(self, todo_id):
        updated = []
        for t in self.todos:
            if t["id"] == todo_id:
                updated.append({**t, "done": not t["done"]})
            else:
                updated.append(t)
        self.todos = updated

    def delete_todo(self, todo_id):
        self.todos = [t for t in self.todos if t["id"] != todo_id]

    def set_filter(self, mode):
        self.filter_mode = mode

    def clear_completed(self):
        self.todos = [t for t in self.todos if not t["done"]]

    def render(self):
        return (
            Div(class_name="card")
                .child(H2().text("Todo List"))
                # Input row
                .child(
                    Div(class_name="todo-input-row")
                        .child(
                            Input(type="text", placeholder="What needs to be done?")
                                .bind_value(self, "new_text")
                                .on_keydown(self.on_keydown)
                        )
                        .child(
                            Button().text("Add").on_click(self.add_todo)
                        )
                )
                # Filter buttons
                .child(
                    Div(class_name="todo-filters")
                        .child(
                            Button()
                                .text("All")
                                .class_toggle("active", lambda: self.filter_mode == "all")
                                .on_click(lambda: self.set_filter("all"))
                        )
                        .child(
                            Button()
                                .text("Active")
                                .class_toggle("active", lambda: self.filter_mode == "active")
                                .on_click(lambda: self.set_filter("active"))
                        )
                        .child(
                            Button()
                                .text("Completed")
                                .class_toggle("active", lambda: self.filter_mode == "completed")
                                .on_click(lambda: self.set_filter("completed"))
                        )
                        .child(
                            Button()
                                .text("Clear completed")
                                .on_click(self.clear_completed)
                        )
                )
                # Todo list — dynamic children with keyed reconciliation
                .child(
                    Ul(class_name="todo-list")
                        .children_from(
                            source=lambda: self.visible_todos,
                            key=lambda t: t["id"],
                            render_item=lambda t, i: (
                                Li(class_name="todo-item")
                                    .class_toggle("done", lambda t=t: t["done"])
                                    .child(
                                        Span(class_name="todo-check")
                                            .text(lambda t=t: "x" if t["done"] else "o")
                                    )
                                    .child(
                                        Span(class_name="todo-text")
                                            .text(lambda t=t: t["text"])
                                    )
                                    .child(
                                        Button(class_name="todo-delete")
                                            .text("delete")
                                            .on_click(lambda t=t: self.delete_todo(t["id"]))
                                    )
                                    .on_click(lambda t=t: self.toggle_todo(t["id"]))
                            ),
                        )
                )
                # Summary
                .child(
                    P(class_name="todo-summary")
                        .text(lambda: (
                            f"{self.remaining} of {self.total} items remaining"
                            if self.total > 0
                            else "No todos yet -- add one above!"
                        ))
                )
        )


class ColorPickerSection(Component):
    """Demonstrates: reactive styles, multiple bind_value inputs,
    Computed properties, real-time visual feedback."""

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
            Div(class_name="card")
                .child(H2().text("Color Picker"))
                .child(
                    Div(class_name="color-section")
                        .child(
                            Div(class_name="color-preview")
                                .style("background-color", lambda: self.rgb_string)
                                .text(" ")
                        )
                        .child(
                            Span(class_name="color-value")
                                .text(lambda: self.hex_color)
                        )
                )
                .child(
                    Div(class_name="color-sliders")
                        .child(self._slider("R", "red"))
                        .child(self._slider("G", "green"))
                        .child(self._slider("B", "blue"))
                )
        )

    def _slider(self, label_text, field_name):
        return (
            Div()
                .child(
                    Span()
                        .text(f"{label_text}: ")
                        .style("color", "#a0a0c0")
                        .style("font-size", "13px")
                        .style("min-width", "30px")
                        .style("display", "inline-block")
                )
                .child(
                    Span()
                        .text(lambda field_name=field_name: str(getattr(self, field_name)))
                        .style("color", "#7aa2f7")
                        .style("font-size", "13px")
                        .style("min-width", "40px")
                        .style("display", "inline-block")
                )
        )


class TabDemoSection(Component):
    """Demonstrates: Switch conditional rendering, dynamic tab navigation."""

    current_tab = State("welcome")

    def set_tab(self, tab):
        self.current_tab = tab

    def render(self):
        return (
            Div(class_name="card")
                .child(H2().text("Tab Navigation (Switch)"))
                .child(
                    Div(class_name="nav")
                        .child(
                            Button()
                                .text("Welcome")
                                .class_toggle("active", lambda: self.current_tab == "welcome")
                                .on_click(lambda: self.set_tab("welcome"))
                        )
                        .child(
                            Button()
                                .text("Features")
                                .class_toggle("active", lambda: self.current_tab == "features")
                                .on_click(lambda: self.set_tab("features"))
                        )
                        .child(
                            Button()
                                .text("Architecture")
                                .class_toggle("active", lambda: self.current_tab == "architecture")
                                .on_click(lambda: self.set_tab("architecture"))
                        )
                )
                .child(
                    Switch(lambda: self.current_tab)
                        .case("welcome", lambda: (
                            Div()
                                .child(H3().text("Welcome to Reactive Pytonium"))
                                .child(P().text(
                                    "This demo showcases reactive components with "
                                    "surgical DOM updates. No virtual DOM, no JS "
                                    "framework -- just pure Python state descriptors "
                                    "driving minimal DOM mutations."
                                ))
                        ))
                        .case("features", lambda: (
                            Div()
                                .child(H3().text("Features Demonstrated"))
                                .child(Ul()
                                    .child(Li().text("State descriptors with change notification"))
                                    .child(Li().text("Computed properties with caching"))
                                    .child(Li().text("Element builder (fluent API)"))
                                    .child(Li().text("Event handling (click, keydown)"))
                                    .child(Li().text("Two-way input binding"))
                                    .child(Li().text("Dynamic lists (children_from)"))
                                    .child(Li().text("Conditional rendering (Show/Switch)"))
                                    .child(Li().text("CSS class toggling"))
                                    .child(Li().text("Update batching"))
                                )
                        ))
                        .case("architecture", lambda: (
                            Div()
                                .child(H3().text("How It Works"))
                                .child(P().text(
                                    "State changes in Python -> DependencyTracker looks up "
                                    "affected DOM nodes -> MutationCompiler generates minimal "
                                    "JavaScript -> single IPC round-trip to CEF -> browser "
                                    "executes trivial DOM mutations. Zero framework JS in "
                                    "the renderer."
                                ))
                        ))
                        .default(lambda: P().text("Unknown tab"))
                )
        )


class ShowDemoSection(Component):
    """Demonstrates: Show conditional rendering with then/fallback."""

    logged_in = State(False)
    username = State("Practitioner")

    def toggle_login(self):
        self.logged_in = not self.logged_in

    def render(self):
        return (
            Div(class_name="card")
                .child(H2().text("Conditional Rendering (Show)"))
                .child(
                    Show(
                        when=lambda: self.logged_in,
                        then=lambda: (
                            Div()
                                .child(
                                    P()
                                        .child(Span().text("Welcome, "))
                                        .child(Strong().text(lambda: self.username))
                                        .child(Span().text("! You are logged in."))
                                )
                                .child(
                                    Button()
                                        .text("Log out")
                                        .on_click(self.toggle_login)
                                )
                        ),
                        fallback=lambda: (
                            Div()
                                .child(P().text("You are not logged in."))
                                .child(
                                    Button()
                                        .text("Log in")
                                        .on_click(self.toggle_login)
                                )
                        ),
                    )
                )
        )


class ReactiveApp(Component):
    """Root component composing all demo sections.

    Demonstrates: component composition, clock driven by Python main loop.
    """

    clock_text = State("")

    def render(self):
        return (
            Div(class_name="app")
                .child(
                    Div(class_name="app-header")
                        .child(H1().text("Pytonium Reactive Components"))
                        .child(P().text(
                            "Surgical DOM updates from pure Python -- "
                            "no virtual DOM, no JS framework"
                        ))
                        .child(
                            Span(class_name="clock")
                                .text(lambda: self.clock_text)
                        )
                )
                .child(Div().id("sections"))
                .child(
                    Div(class_name="app-footer")
                        .child(P().text(
                            "Pytonium Reactive Components v0.1 -- "
                            "Built with Python, Cython, CEF, and love"
                        ))
                )
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("=" * 60)
    print("  Pytonium Reactive Components -- Comprehensive Demo")
    print("=" * 60)
    print()

    p = Pytonium()

    # ---------------------------------------------------------------
    # Step 1: Register event bindings BEFORE initialize()
    # CEF binds JavaScript functions during page load (OnContextCreated).
    # Bindings added AFTER that point are invisible to JavaScript.
    # ---------------------------------------------------------------
    Component.setup(p)

    # ---------------------------------------------------------------
    # Step 2: Write the HTML page to a file and load via file:// URL.
    # (Avoids data: URL size / encoding issues with large CSS.)
    # ---------------------------------------------------------------
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(script_dir, "_reactive_demo.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '<meta charset="UTF-8">\n'
            "<title>Pytonium Reactive Demo</title>\n"
            f"<style>{APP_CSS}</style>\n"
            "</head>\n"
            "<body>\n"
            '<div id="app"></div>\n'
            "</body>\n"
            "</html>\n"
        )

    p.initialize(f"file:///{html_path}", 960, 900)

    # ---------------------------------------------------------------
    # Step 3: Mount components.
    # mount() automatically waits for the page to be ready (polls
    # the _ready sentinel until execute_javascript() actually works).
    # ---------------------------------------------------------------
    app = ReactiveApp()
    app.mount(p, container_id="app")

    # Create sub-components
    counter = CounterSection()
    todo = TodoSection()
    tab_demo = TabDemoSection()
    show_demo = ShowDemoSection()
    color_picker = ColorPickerSection()

    # Append section containers into the "sections" div, then mount
    sections = [
        ("section-counter", counter),
        ("section-tabs", tab_demo),
        ("section-show", show_demo),
        ("section-todo", todo),
        ("section-color", color_picker),
    ]

    for section_id, _ in sections:
        p.execute_javascript(
            f'(function(){{'
            f'var s=document.getElementById("sections");'
            f'if(s){{var d=document.createElement("div");'
            f'd.id="{section_id}";s.appendChild(d);}}'
            f'}})()'
        )

    # Pump a few frames so the section containers are in the DOM
    for _ in range(5):
        p.update_message_loop()
        time.sleep(0.016)

    for section_id, component in sections:
        component.mount(p, container_id=section_id)

    print("  All components mounted!")
    print()
    print("  Try:")
    print("    - Click +/- on the counter")
    print("    - Type a todo and press Enter or click Add")
    print("    - Click a todo to toggle done")
    print("    - Switch between filter tabs (All/Active/Completed)")
    print("    - Navigate the tabs (Welcome/Features/Architecture)")
    print("    - Toggle the login state")
    print()

    # Seed some initial todos for demonstration
    todo.todos = [
        {"id": 1, "text": "Try clicking this todo item", "done": False},
        {"id": 2, "text": "Add a new todo above", "done": False},
        {"id": 3, "text": "This one is already done", "done": True},
    ]
    todo.next_id = 4

    # Main loop — update the clock from Python
    frame = 0
    while p.is_running():
        p.update_message_loop()
        time.sleep(0.016)

        # Update the clock every ~30 frames (~0.5s)
        frame += 1
        if frame % 30 == 0:
            now = datetime.now().strftime("%H:%M:%S")
            app.clock_text = now


if __name__ == "__main__":
    main()
