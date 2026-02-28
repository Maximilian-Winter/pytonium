# Pytonium Reactive Components: Surgical DOM Updates Without a Virtual DOM

## The Core Idea

Pytonium's unique architecture — a Python layer communicating through Cython to a C++ library wrapping CEF — enables something that neither Electron nor Tauri can achieve: a reactive Python component model that bypasses the virtual DOM entirely.

Instead of React's approach (re-render everything, diff the trees, patch the DOM), Pytonium can track dependencies between Python state and specific DOM nodes at initialization time, then surgically update only the affected nodes when state changes. No diffing. No virtual DOM. No JavaScript framework runtime in the browser. Pre-computed, minimal mutation commands sent as a single batch.

This is the approach pioneered by Svelte and SolidJS in the JavaScript world, but applied from the Python side — the developer writes pure Python components with no build step or compiler, and the framework generates minimal DOM mutations at the C++ layer. The browser never runs a reconciler, a differ, or any framework JavaScript. It just receives and executes trivial property assignments.

---

## Architecture Overview

The system has four layers:

```
┌─────────────────────────────────────┐
│  Python Component Layer             │
│  (Developer-facing API)             │
│  - Component classes with State     │
│  - Builder pattern for HTML trees   │
│  - Event handler registration       │
├─────────────────────────────────────┤
│  Dependency Tracker                 │
│  (Python)                           │
│  - Maps State fields → DOM node IDs │
│  - Detects state changes via        │
│    descriptors                      │
│  - Emits minimal update commands    │
├─────────────────────────────────────┤
│  C++ Mutation Compiler              │
│  (Via Cython bridge)                │
│  - Receives update commands         │
│  - Compiles into minimal JS batch   │
│  - Single IPC round-trip to CEF     │
│  - Handles batching and scheduling  │
├─────────────────────────────────────┤
│  CEF / Chromium DOM                 │
│  - Actual rendered page             │
│  - Events bubble back up through    │
│    C++ → Cython → Python            │
└─────────────────────────────────────┘
```

---

## The Python Component Model

### Defining a Component

```python
from pytonium.components import Component, State, Computed
from pytonium.elements import Div, H1, Button, Ul, Li, Input

class TodoApp(Component):
    # Reactive state — changes trigger surgical DOM updates
    todos = State([])
    new_todo_text = State("")
    filter_mode = State("all")  # "all", "active", "completed"

    # Computed values — derived from state, cached, auto-updating
    @Computed
    def visible_todos(self):
        if self.filter_mode == "all":
            return self.todos
        elif self.filter_mode == "active":
            return [t for t in self.todos if not t["done"]]
        else:
            return [t for t in self.todos if t["done"]]

    @Computed
    def remaining_count(self):
        return sum(1 for t in self.todos if not t["done"])

    # Event handlers
    def add_todo(self):
        if self.new_todo_text.strip():
            self.todos = [*self.todos, {"text": self.new_todo_text, "done": False}]
            self.new_todo_text = ""

    def toggle_todo(self, index):
        updated = list(self.todos)
        updated[index] = {**updated[index], "done": not updated[index]["done"]}
        self.todos = updated

    def set_filter(self, mode):
        self.filter_mode = mode

    # The render method — called once to establish the dependency graph
    def render(self):
        return (
            Div(class_name="todo-app")
                .child(
                    H1().text(lambda: f"{self.remaining_count} items remaining")
                )
                .child(
                    Div(class_name="input-row")
                        .child(
                            Input()
                                .bind_value(self, "new_todo_text")
                                .on_keydown(lambda e: self.add_todo() if e.key == "Enter" else None)
                        )
                        .child(
                            Button()
                                .text("Add")
                                .on_click(self.add_todo)
                        )
                )
                .child(
                    Ul().children_from(
                        lambda: self.visible_todos,
                        key=lambda t: t["text"],
                        render_item=lambda t, i: (
                            Li()
                                .text(lambda t=t: t["text"])
                                .class_toggle("done", lambda t=t: t["done"])
                                .on_click(lambda i=i: self.toggle_todo(i))
                        )
                    )
                )
                .child(
                    Div(class_name="filters")
                        .child(Button().text("All").on_click(lambda: self.set_filter("all")))
                        .child(Button().text("Active").on_click(lambda: self.set_filter("active")))
                        .child(Button().text("Done").on_click(lambda: self.set_filter("completed")))
                )
        )
```

### Key Design Decisions

**Lambdas as reactive bindings.** When a builder method receives a lambda instead of a static value, the dependency tracker knows this node needs updating when the referenced state changes. Static values are rendered once and never touched again. This is the mechanism that makes surgical updates possible — the framework knows at initialization time exactly which DOM nodes depend on which state.

**`State` as a Python descriptor.** The `State` class uses `__set_name__`, `__get__`, and `__set__` to intercept attribute access. When a state field is written to, the descriptor notifies the dependency tracker, which looks up which DOM nodes are affected and emits update commands.

**`Computed` for derived values.** Computed properties track which `State` fields they access during evaluation (similar to MobX or Vue's reactivity). They cache their result and only recompute when a dependency changes. DOM nodes bound to computed values update transitively.

**`children_from` for dynamic lists.** This is the equivalent of React's `.map()` pattern. The `key` function provides stable identity for list items, allowing the framework to add, remove, and reorder DOM nodes without re-rendering the entire list.

**Lambda closure capture.** Python closures capture variables by reference, not by value. Inside `render_item=lambda t, i: ...`, any nested lambdas that reference `t` or `i` must use default argument binding to capture the current value: `lambda t=t: t["text"]` instead of `lambda: t["text"]`. Without this, all items would reference the last value of `t` from the iteration. The framework could enforce this automatically in a future version, but for now, developers should use the `x=x` pattern in nested lambdas.

---

## The State Descriptor

```python
class State:
    def __set_name__(self, owner, name):
        self.name = name
        self.private_name = f"_state_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        # Register access with dependency tracker if currently tracking
        DependencyTracker.record_access(obj, self.name)
        return getattr(obj, self.private_name, self.default)

    def __set__(self, obj, value):
        old_value = getattr(obj, self.private_name, self.default)
        setattr(obj, self.private_name, value)
        if old_value is not value:
            # Notify the dependency tracker of the change
            DependencyTracker.notify_change(obj, self.name, old_value, value)

    def __init__(self, default=None):
        self.default = default
```

When `self.filter_mode = "active"` is called inside a component, the descriptor intercepts the write, compares old and new values, and if they differ, triggers the dependency tracker to process the change.

---

## The Dependency Tracker

The dependency tracker is the brain of the system. It maintains a mapping from `(component_instance, state_field)` pairs to sets of DOM node IDs and the specific attribute or content that needs updating.

**Important: Memory management.** The dependency tracker uses weak references (`weakref.ref`) to component instances rather than strong references or `id(component)`. Python can reuse `id()` values for new objects after garbage collection of old ones, which would cause stale mappings. Weak references allow the tracker to detect when a component has been garbage collected and automatically clean up its dependency entries. Component `on_unmount()` also explicitly removes all mappings for the unmounting component.

### How Dependencies Are Discovered

During the initial `render()` call, the tracker operates in recording mode:

```python
import weakref

class DependencyTracker:
    _current_tracking = None  # Set during render to capture dependencies
    _dependency_map = {}      # (weakref, field_name) → [bindings]

    @classmethod
    def record_access(cls, component, field_name):
        """Called by State.__get__ during render."""
        if cls._current_tracking is not None:
            # Use weakref to avoid preventing garbage collection
            cls._current_tracking.add((weakref.ref(component), field_name))

    @classmethod
    def track(cls, callback):
        """Execute callback while recording which State fields are accessed."""
        deps = set()
        cls._current_tracking = deps
        result = callback()
        cls._current_tracking = None
        return result, deps
```

When the framework encounters a lambda binding during render, it calls `DependencyTracker.track(lambda_fn)`. This executes the lambda, captures which `State` fields were read during execution, and associates those fields with the DOM node ID being constructed.

The result is a dependency map like:

```
(todo_app, "remaining_count") → [
    {node_id: "n_007", update: "text_content", transform: lambda: f"{self.remaining_count} items remaining"}
]

(todo_app, "filter_mode") → [
    {node_id: "n_012", update: "children", source: lambda: self.visible_todos, ...}
]

(todo_app, "todos") → [
    {node_id: "n_012", update: "children", source: lambda: self.visible_todos, ...},
    {node_id: "n_007", update: "text_content", transform: lambda: f"{self.remaining_count} items remaining"}
]
```

### How Updates Propagate

When state changes:

1. `State.__set__` calls `DependencyTracker.notify_change(component, field_name, old, new)`
2. The tracker looks up all DOM nodes mapped to `(component, field_name)`
3. For each affected node, it re-evaluates the associated lambda to get the new value
4. It emits a batch of minimal update commands to the C++ layer

```python
class DependencyTracker:
    @classmethod
    def notify_change(cls, component, field_name, old_value, new_value):
        key = (id(component), field_name)
        affected = cls._dependency_map.get(key, [])

        commands = []
        for binding in affected:
            new_val = binding["transform"]()
            commands.append(UpdateCommand(
                node_id=binding["node_id"],
                update_type=binding["update"],
                value=new_val
            ))

        # Also recompute affected Computed properties
        for computed_key in cls._computed_deps.get(key, []):
            computed_key.invalidate()
            # This may trigger further DOM updates

        # Batch and send to C++
        MutationCompiler.apply_batch(commands)
```

---

## The C++ Mutation Compiler

The update commands cross the Cython bridge into C++, where they are compiled into a single, minimal JavaScript string and sent to CEF's renderer process via one IPC round-trip. CEF does not expose direct DOM APIs from the browser process — `CefDOMVisitor` only works in the renderer — so the C++ layer acts as a mutation compiler: it receives structured update commands from Python and produces the most minimal JS possible to execute them.

The key insight is that the browser never runs framework code. No React reconciler, no virtual DOM differ, no Svelte runtime. The JS that arrives in the renderer is pure DOM mutation — `querySelector` and property assignments — executed in a single batch for a single reflow.

### Update Command Types

```cpp
enum class UpdateType {
    SetTextContent,    // Change text inside a node
    SetAttribute,      // Change a single attribute
    AddClass,          // Add a CSS class
    RemoveClass,       // Remove a CSS class
    ToggleClass,       // Toggle a CSS class
    SetStyle,          // Change an inline style property
    InsertChild,       // Insert a child node at index
    RemoveChild,       // Remove a child node
    MoveChild,         // Reorder a child node
    ReplaceNode,       // Replace entire node (rare, for type changes)
    SetValue,          // Set input/textarea value
    BatchUpdate        // Group of updates to apply atomically
};

struct UpdateCommand {
    std::string node_id;
    UpdateType type;
    std::string key;      // attribute name, class name, style property, etc.
    std::string value;    // new value
    int index;            // for child operations
};
```

### Execution Path

The full update path for a state change:

```
Python State.__set__
    → DependencyTracker.notify_change()  (Python)
    → Emit UpdateCommand structs         (Python → Cython)
    → MutationCompiler.apply_batch()     (C++)
    → build_batch_mutation_js()          (C++, generates minimal JS string)
    → CefFrame::ExecuteJavaScript()      (C++ → IPC to renderer process)
    → Renderer executes JS               (trivial DOM mutations, single reflow)
```

```cpp
class MutationCompiler {
public:
    void apply_batch(const std::vector<UpdateCommand>& commands) {
        auto frame = browser_->GetMainFrame();

        // Compile update commands into a single JavaScript call
        // This is ONE IPC round-trip to the renderer process
        std::string js = build_batch_mutation_js(commands);
        frame->ExecuteJavaScript(js, frame->GetURL(), 0);
    }

private:
    std::string build_batch_mutation_js(const std::vector<UpdateCommand>& cmds) {
        // Generates something like:
        // (function() {
        //   var n7 = document.querySelector('[data-pyt-id="n_007"]');
        //   n7.textContent = "3 items remaining";
        //   var n12 = document.querySelector('[data-pyt-id="n_012"]');
        //   n12.classList.add("done");
        // })();
        //
        // All mutations in a single JS execution = single reflow
    }
};
```

### Why This Is Fast

1. **No diffing cost.** The dependency graph was built once at render time. State changes map directly to DOM mutations without comparing trees.
2. **Zero framework runtime in the browser.** The renderer never runs React, Svelte, or any framework code. It receives and executes trivial DOM mutations — `querySelector` and property assignments. This is the real performance advantage over JS-based frameworks.
3. **Single reflow.** All mutations from a single state change are batched into one JavaScript execution, so the browser only reflows once.
4. **C++ batching.** The C++ layer coalesces rapid state changes (e.g., multiple state writes in a single event handler) into one IPC round-trip and one JS execution.

### What This Is Not

To be clear about the architecture: CEF does not expose direct DOM APIs from the browser process. Updates go through IPC to the renderer process and execute as JavaScript. The path is Python → C++ → IPC → JS → DOM, which is more hops than a pure JS framework. The advantage is not fewer hops — it's that the JS at the end of the chain is pre-computed, minimal, and contains zero framework logic. The "smart" work happens in Python and C++ before the IPC boundary.

---

## The Element Builder

The builder pattern constructs an intermediate representation that the framework uses both for initial rendering and for establishing the dependency graph.

```python
class Element:
    _id_counter = 0

    def __init__(self, tag, **attrs):
        Element._id_counter += 1
        self.node_id = f"n_{Element._id_counter:04d}"
        self.tag = tag
        self.attrs = attrs
        self._children = []
        self._events = {}
        self._bindings = []  # Reactive bindings to track

    def child(self, element):
        self._children.append(element)
        return self

    def text(self, content):
        """Static string or lambda for reactive text."""
        if callable(content):
            self._bindings.append(("text_content", content))
        else:
            self._static_text = content
        return self

    def class_toggle(self, class_name, condition):
        """Toggle a CSS class based on a reactive condition."""
        self._bindings.append(("class_toggle", class_name, condition))
        return self

    def bind_value(self, component, field_name, debounce_ms=0):
        """Two-way binding for input elements.

        For high-frequency input events (typing), the JS-side event listener
        buffers keystrokes and sends them as a single IPC message on the next
        animation frame, rather than one IPC round-trip per keystroke. The
        optional debounce_ms parameter adds additional debouncing.
        """
        self._bindings.append(("value", lambda: getattr(component, field_name)))
        self._events["input"] = {
            "handler": lambda e: setattr(component, field_name, e.value),
            "buffered": True,
            "debounce_ms": debounce_ms,
        }
        return self

    def on_click(self, handler):
        self._events["click"] = handler
        return self

    def on_keydown(self, handler):
        self._events["keydown"] = handler
        return self

    def children_from(self, source, key, render_item):
        """Dynamic child list with keyed reconciliation."""
        self._dynamic_children = {
            "source": source,
            "key": key,
            "render_item": render_item
        }
        return self

    def to_html(self):
        """Generate initial HTML with data-pyt-id markers."""
        attrs = " ".join(f'{k}="{v}"' for k, v in self.attrs.items())
        pyt_attr = f'data-pyt-id="{self.node_id}"'
        children_html = "".join(c.to_html() for c in self._children)
        text = getattr(self, "_static_text", "")

        # For reactive text, evaluate the lambda for initial value
        for binding_type, *args in self._bindings:
            if binding_type == "text_content":
                text = args[0]()  # Evaluate lambda for initial render

        return f"<{self.tag} {pyt_attr} {attrs}>{text}{children_html}</{self.tag}>"


# Convenience constructors
def Div(**attrs): return Element("div", **attrs)
def H1(**attrs): return Element("h1", **attrs)
def Button(**attrs): return Element("button", **attrs)
def Input(**attrs): return Element("input", **attrs)
def Ul(**attrs): return Element("ul", **attrs)
def Li(**attrs): return Element("li", **attrs)
def Span(**attrs): return Element("span", **attrs)
```

---

## The Initialization Sequence

When a component is mounted, the following happens in order:

```
1. Component.__init__()
   └─ State descriptors initialize default values

2. Component.render()
   └─ Builder methods construct Element tree
   └─ Lambdas are NOT yet evaluated (just stored)

3. DependencyTracker.analyze(element_tree)
   └─ For each Element with reactive bindings:
       └─ Track(lambda) → execute lambda, record State accesses
       └─ Map: (component, state_field) → (node_id, update_type, lambda)
   └─ For each Element with events:
       └─ Register event route: node_id → Python callback

4. Element.to_html() → generate full HTML string
   └─ Each element gets a data-pyt-id attribute
   └─ Reactive lambdas evaluated for initial values

5. C++ layer injects HTML into CEF
   └─ Registers JavaScript event listeners that route back through C++

6. Component is now live
   └─ State changes trigger surgical updates via dependency map
```

---

## Handling Dynamic Lists

Dynamic lists (the `children_from` pattern) require special handling since the number and identity of child nodes changes over time. This is where the `key` function becomes critical.

```python
class DynamicChildrenManager:
    def __init__(self, parent_node_id, source_fn, key_fn, render_item_fn):
        self.parent_id = parent_node_id
        self.source = source_fn
        self.key = key_fn
        self.render_item = render_item_fn
        self.current_keys = []       # Ordered list of current keys
        self.key_to_node = {}        # key → Element mapping

    def update(self):
        new_items = self.source()
        new_keys = [self.key(item) for item in new_items]

        commands = []

        # Detect removals
        removed = set(self.current_keys) - set(new_keys)
        for key in removed:
            node = self.key_to_node.pop(key)
            commands.append(RemoveChild(self.parent_id, node.node_id))

        # Detect additions
        added = set(new_keys) - set(self.current_keys)
        for i, (key, item) in enumerate(zip(new_keys, new_items)):
            if key in added:
                element = self.render_item(item, i)
                DependencyTracker.analyze(element)
                self.key_to_node[key] = element
                commands.append(InsertChild(self.parent_id, element.to_html(), i))

        # Detect moves (reordering)
        # Compare position of surviving keys in old vs new order
        # Emit MoveChild commands for minimal reordering

        self.current_keys = new_keys
        MutationCompiler.apply_batch(commands)
```

This gives you efficient list operations without re-rendering the entire list — items that didn't change are never touched.

---

## Conditional Rendering

Since `render()` is called once to establish the dependency graph, the component *structure* cannot change based on if/else logic inside `render()`. Instead, conditional rendering is handled by special control-flow elements that manage mounting and unmounting sub-trees when conditions change.

```python
from pytonium.elements import Show, Switch, Case

class App(Component):
    logged_in = State(False)
    current_tab = State("home")

    def render(self):
        return (
            Div()
                # Show/hide based on a reactive condition
                .child(
                    Show(
                        when=lambda: self.logged_in,
                        then=lambda: Dashboard(user=self.user),
                        fallback=lambda: LoginForm(on_login=self.handle_login)
                    )
                )
                # Switch between multiple branches
                .child(
                    Switch(lambda: self.current_tab)
                        .case("home", lambda: HomePage())
                        .case("settings", lambda: SettingsPage())
                        .case("profile", lambda: ProfilePage())
                        .default(lambda: NotFoundPage())
                )
        )
```

### How `Show` Works Internally

`Show` is not a regular element — it's a control-flow node that the dependency tracker handles specially:

1. The `when` lambda is tracked like any other reactive binding
2. When the condition changes from `False` to `True`, the `then` lambda is evaluated, its element tree is analyzed for dependencies, rendered to HTML, and injected into the DOM
3. When the condition changes from `True` to `False`, the `then` sub-tree is unmounted (DOM nodes removed, dependency mappings cleaned up, `on_unmount` called on any child components), and the `fallback` sub-tree is mounted in its place
4. The `Switch` element works similarly but supports multiple branches with a value-based selector

This is the same pattern used by SolidJS (`<Show>`, `<Switch>`, `<Match>`) — the structure of the DOM tree changes reactively without re-running the entire `render()` method.

---

## Event Routing

Events flow from the browser DOM back to Python through the existing Pytonium bridge, extended with node ID routing:

```
Browser DOM event (click on node n_042)
    ↓
JavaScript event listener (registered during mount)
    ↓ calls registered Pytonium JS binding
C++ event router
    ↓ looks up n_042 → component.toggle_todo(3)
Cython bridge
    ↓
Python event handler executes
    ↓ handler modifies State
State descriptor triggers DependencyTracker
    ↓
DependencyTracker emits UpdateCommands
    ↓
C++ UpdateEngine applies batch to DOM
```

The full round-trip for a click handler: DOM event → JS listener → IPC → C++ → Python handler → state change → dependency tracker → C++ mutation compiler → IPC → JS DOM mutations. This is more hops than a pure JS framework, but the critical difference is that no framework logic runs in the renderer — only trivial event forwarding on the way up and trivial DOM assignments on the way back down.

### High-Frequency Event Buffering

For low-frequency events like clicks, the IPC round-trip is imperceptible. But for high-frequency events — typing in an input field, mousemove for drag operations, scroll events — a round-trip per event would feel laggy.

The solution is JS-side event buffering. The event listener injected during mount collects rapid events and sends them as a single batched IPC message on the next `requestAnimationFrame`:

```javascript
// Injected by the framework during mount (simplified)
(function() {
    var buffer = {};
    var scheduled = false;

    document.querySelector('[data-pyt-id="n_042"]').addEventListener('input', function(e) {
        buffer['n_042'] = e.target.value;  // Overwrite — only latest value matters
        if (!scheduled) {
            scheduled = true;
            requestAnimationFrame(function() {
                // Send all buffered values in ONE IPC call
                Pytonium._internal.flush_event_buffer(buffer);
                buffer = {};
                scheduled = false;
            });
        }
    });
})();
```

This means rapid typing sends at most one IPC message per frame (~16ms at 60fps) instead of one per keystroke. The same pattern applies to mousemove events during drag operations.

Elements can opt into buffering via `bind_value(component, field, debounce_ms=0)` or event-specific options like `on_mousemove(handler, buffered=True)`.

---

## Component Lifecycle

```python
class Component:
    def on_mount(self):
        """Called after initial HTML is injected into CEF DOM."""
        pass

    def on_update(self, changed_fields: set):
        """Called after state changes have been applied to DOM."""
        pass

    def on_unmount(self):
        """Called before component is removed from DOM."""
        pass

    def render(self) -> Element:
        """Return element tree. Called once during initialization."""
        raise NotImplementedError
```

Lifecycle hooks allow components to perform side effects (fetching data, starting timers, cleaning up resources) at appropriate times, similar to React's `useEffect` but expressed as class methods.

---

## Component Composition

Components can nest naturally:

```python
class TodoItem(Component):
    text = State("")
    done = State(False)

    def toggle(self):
        self.done = not self.done

    def render(self):
        return (
            Li()
                .class_toggle("completed", lambda: self.done)
                .child(
                    Span().text(lambda: self.text)
                )
                .child(
                    Button()
                        .text("Toggle")
                        .on_click(self.toggle)
                )
        )


class TodoApp(Component):
    items = State([])

    def render(self):
        return (
            Div()
                .child(H1().text("Todos"))
                .child(
                    Ul().children_from(
                        lambda: self.items,
                        key=lambda item: item["id"],
                        render_item=lambda item, i: TodoItem(text=item["text"])
                    )
                )
        )
```

Each `TodoItem` instance maintains its own dependency graph. State changes in one item only update that item's DOM nodes — siblings are untouched.

---

## Comparison With Existing Approaches

| Aspect | React (Electron) | Svelte (Tauri) | Pytonium Reactive |
|---|---|---|---|
| Update strategy | Virtual DOM diff | Compiled surgical updates | Runtime surgical updates |
| Diffing cost | O(n) per render | None | None |
| Language | JavaScript | JavaScript (compiled) | Python |
| Backend language | JavaScript (Node) | Rust | Python |
| Framework JS in browser | React runtime (~40KB) | Svelte runtime (~2KB) | None (only raw DOM mutations) |
| Update path | JS reconciler → DOM | JS compiled updaters → DOM | Python → C++ → IPC → minimal JS → DOM |
| Build step required | JSX transpiler | Svelte compiler | None (pure Python) |
| Developer ergonomics | JSX (requires toolchain) | Svelte syntax (requires compiler) | Pure Python (no build step) |

The unique advantage: Pytonium is the only framework where the browser runs zero framework code during updates. The reconciliation, dependency tracking, and mutation planning all happen in Python and C++ — the renderer only receives and executes pre-computed DOM assignments. Combined with no build step and pure Python syntax, this gives Pytonium a distinct position in the desktop framework landscape.

---

## Implementation Roadmap

### Phase 1: Foundation
- Implement `State` descriptor with change notification and weakref-based tracking
- Implement `Element` builder with `to_html()` generation
- Basic `DependencyTracker` with lambda-based dependency discovery
- Wire update commands through existing Cython bridge to C++ `MutationCompiler`
- Single component rendering with text and attribute updates
- Lambda closure safety (enforce `x=x` capture pattern or auto-wrap)

### Phase 2: Interactivity
- Event routing from CEF → C++ → Python with node ID mapping
- Two-way binding for input elements with JS-side event buffering
- High-frequency event buffering (`requestAnimationFrame` batching)
- Class toggling and style bindings
- Component lifecycle hooks (`on_mount`, `on_update`, `on_unmount`)
- Weakref cleanup on unmount

### Phase 3: Dynamic Content
- `children_from` with keyed list reconciliation (LIS algorithm for minimal moves)
- `Computed` properties with transitive dependency tracking
- Component composition and nesting
- Conditional rendering: `Show`, `Switch`, `Case` control-flow elements
- Sub-tree mount/unmount with dependency cleanup

### Phase 4: Performance
- Update batching in C++ (coalesce rapid state changes before IPC)
- Async state updates with scheduling
- Input debouncing at the binding level
- Benchmark suite comparing against React/Electron and Svelte/Tauri
- Profile IPC round-trip overhead and optimize hot paths

### Phase 5: Developer Experience
- Error messages with component and state field context
- Closure capture warnings (detect common `lambda: x` mistakes in loops)
- DevTools integration showing dependency graph
- Hot reload support for component changes during development
- Auto-generated TypeScript definitions for the JS event layer
