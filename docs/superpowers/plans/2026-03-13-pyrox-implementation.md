# Pyrox Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Pyrox, a standalone Python library for server-side reactive web components over WebSocket.

**Architecture:** Four-layer design — Transport Protocol (JSON messages + JS client), Reactive Core (State/Elements/DependencyTracker/MutationCompiler), Session Management (lifecycle, reconnection, locking), and ASGI Integration (middleware, routing, static serving). Clean-room reimplementation inspired by Pytonium's reactive components (~3k LOC), redesigned for multi-user async web.

**Tech Stack:** Python 3.10+, asyncio, ASGI protocol, vanilla JavaScript (no build step). No required dependencies beyond stdlib.

**Spec:** `docs/superpowers/specs/2026-03-13-pyrox-web-framework-design.md`

**Reference (Pytonium reactive components):** `src/pytonium_python_framework/Pytonium/components/`

---

## File Structure

```
pyrox/                          # Package root (NEW — standalone project)
├── __init__.py                 # Public API exports
├── core/
│   ├── __init__.py
│   ├── types.py                # UpdateType enum, UpdateCommand, Binding dataclasses
│   ├── state.py                # State descriptor + Computed decorator
│   ├── tracker.py              # DependencyTracker (instance-scoped)
│   ├── elements.py             # Element builder + HTML constructors
│   ├── conditionals.py         # Show, Switch conditional elements
│   └── dynamic_children.py     # DynamicChildrenManager for keyed lists
├── compiler/
│   ├── __init__.py
│   ├── mutation_compiler.py    # UpdateCommand → JSON mutation dicts
│   └── codec.py                # WebSocket message encode/decode
├── session/
│   ├── __init__.py
│   ├── session.py              # Session dataclass + lock
│   ├── manager.py              # SessionManager (create, reconnect, expire)
│   └── store.py                # SessionStore protocol + InMemoryStore
├── events/
│   ├── __init__.py
│   └── dispatcher.py           # EventDispatcher (async, replaces EventRouter)
├── component.py                # Component base class (mount, lifecycle, flush)
├── asgi/
│   ├── __init__.py
│   ├── app.py                  # Pyrox app class + ASGI application
│   ├── websocket.py            # WebSocket handler (message loop)
│   ├── routes.py               # HTTP routes (page shell, static files)
│   └── page_shell.py           # Auto-generated HTML page template
├── client/
│   └── pyrox.js                # Client JS library (~3-5KB)
├── testing/
│   ├── __init__.py
│   └── mock_session.py         # MockSession for unit testing
└── py.typed                    # PEP 561 marker
tests/
├── test_types.py
├── test_state.py
├── test_tracker.py
├── test_elements.py
├── test_conditionals.py
├── test_dynamic_children.py
├── test_mutation_compiler.py
├── test_codec.py
├── test_dispatcher.py
├── test_component.py
├── test_session.py
├── test_session_manager.py
├── test_mock_session.py
├── test_asgi_app.py
└── test_integration.py
pyproject.toml                  # Package metadata + dependencies
```

**Key structural differences from Pytonium:**
- `DependencyTracker` moves from `state.py` to its own `tracker.py` (it's a large class)
- `MutationCompiler` outputs JSON dicts instead of JS strings — simpler, no JS escaping
- `EventRouter` becomes `EventDispatcher` — async, no CEF bindings, no JS injection
- New `session/` package — the web-specific layer
- New `asgi/` package — ASGI middleware and routing
- New `client/pyrox.js` — the thin JS client
- New `testing/` package — MockSession for fast tests

---

## Chunk 1: Foundation (Types + State + Tracker)

### Task 1: Project Setup + Types

**Files:**
- Create: `pyrox/__init__.py`
- Create: `pyrox/core/__init__.py`
- Create: `pyrox/core/types.py`
- Create: `tests/test_types.py`
- Create: `pyproject.toml`

- [ ] **Step 1: Create project skeleton and pyproject.toml**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "pyrox"
version = "0.1.0"
description = "Reactive Python web framework — server-side components over WebSocket"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
classifiers = [
    "Development Status :: 3 - Alpha",
    "Framework :: AsyncIO",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Internet :: WWW/HTTP",
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "pytest-asyncio>=0.21"]
uvicorn = ["uvicorn[standard]>=0.20"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

```python
# pyrox/__init__.py
"""Pyrox — Reactive Python web framework."""
__version__ = "0.1.0"
```

```python
# pyrox/core/__init__.py
"""Pyrox reactive core."""
```

- [ ] **Step 2: Write failing tests for types**

```python
# tests/test_types.py
"""Tests for core type definitions."""
import pytest
from pyrox.core.types import UpdateType, UpdateCommand, Binding


class TestUpdateType:
    def test_all_mutation_ops_defined(self):
        """All 12 mutation operations from the spec must exist."""
        ops = [
            "SET_TEXT_CONTENT", "SET_ATTRIBUTE", "REMOVE_ATTRIBUTE",
            "ADD_CLASS", "REMOVE_CLASS", "TOGGLE_CLASS",
            "SET_STYLE", "SET_VALUE",
            "INSERT_CHILD", "REMOVE_CHILD", "MOVE_CHILD",
            "REPLACE_INNER_HTML",
        ]
        for op in ops:
            assert hasattr(UpdateType, op), f"Missing UpdateType.{op}"

    def test_values_are_json_friendly_strings(self):
        assert UpdateType.SET_TEXT_CONTENT.value == "text"
        assert UpdateType.SET_ATTRIBUTE.value == "attr"
        assert UpdateType.INSERT_CHILD.value == "insert"
        assert UpdateType.REMOVE_CHILD.value == "remove"
        assert UpdateType.MOVE_CHILD.value == "move"


class TestUpdateCommand:
    def test_create_with_defaults(self):
        cmd = UpdateCommand(node_id="c0-n1", update_type=UpdateType.SET_TEXT_CONTENT)
        assert cmd.node_id == "c0-n1"
        assert cmd.key == ""
        assert cmd.value == ""
        assert cmd.index == -1
        assert cmd.html == ""

    def test_create_with_all_fields(self):
        cmd = UpdateCommand(
            node_id="c0-n2",
            update_type=UpdateType.INSERT_CHILD,
            key="item-key",
            value="child-id",
            index=3,
            html="<li>hello</li>",
        )
        assert cmd.index == 3
        assert cmd.html == "<li>hello</li>"


class TestBinding:
    def test_create_with_transform(self):
        fn = lambda: "hello"
        b = Binding(
            node_id="c0-n1",
            update_type=UpdateType.SET_TEXT_CONTENT,
            transform=fn,
        )
        assert b.transform is fn
        assert b._dynamic_manager_element is None
        assert b._conditional_element is None

    def test_create_with_dynamic_manager(self):
        sentinel = object()
        b = Binding(
            node_id="c0-n1",
            update_type=UpdateType.REPLACE_INNER_HTML,
            _dynamic_manager_element=sentinel,
        )
        assert b._dynamic_manager_element is sentinel
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd pyrox_project && python -m pytest tests/test_types.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pyrox.core.types'`

- [ ] **Step 4: Implement types**

```python
# pyrox/core/types.py
"""Core data types for Pyrox reactive components.

Defines the UpdateType enum, UpdateCommand dataclass, and Binding dataclass.
These mirror Pytonium's types.py but with JSON-friendly enum values matching
the WebSocket message protocol ops.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional


class UpdateType(Enum):
    """Types of DOM mutations. Values match the JSON message protocol op names."""
    SET_TEXT_CONTENT = "text"
    SET_ATTRIBUTE = "attr"
    REMOVE_ATTRIBUTE = "remove_attr"
    ADD_CLASS = "class_add"
    REMOVE_CLASS = "class_remove"
    TOGGLE_CLASS = "class_toggle"
    SET_STYLE = "style"
    SET_VALUE = "value"
    INSERT_CHILD = "insert"
    REMOVE_CHILD = "remove"
    MOVE_CHILD = "move"
    REPLACE_INNER_HTML = "inner_html"


@dataclass
class UpdateCommand:
    """A single DOM mutation to be compiled into a JSON message.

    Attributes:
        node_id: Target element's data-pyrox-id value (e.g., "c0-n3").
        update_type: What kind of mutation to perform.
        key: Attribute name, class name, or style property (context-dependent).
        value: New value to set, or child node_id for remove/move.
        index: Position index for child insert/move operations.
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

    Created during dependency analysis of render(). When the bound State
    field changes, the transform lambda is re-evaluated and an UpdateCommand
    is emitted.

    Attributes:
        node_id: Target element's data-pyrox-id.
        update_type: What kind of mutation this binding produces.
        key: Attribute/class/style key (for non-text bindings).
        transform: Lambda that produces the current value when called.
        _dynamic_manager_element: Element with DynamicChildrenManager.
        _conditional_element: Element with conditional logic (Show/Switch).
    """
    node_id: str
    update_type: UpdateType
    key: str = ""
    transform: Optional[Callable] = None
    _dynamic_manager_element: Any = None
    _conditional_element: Any = None
    _is_class_toggle: bool = False
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd pyrox_project && python -m pytest tests/test_types.py -v`
Expected: All 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add pyrox/ tests/test_types.py pyproject.toml
git commit -m "feat(pyrox): project setup + core types (UpdateType, UpdateCommand, Binding)"
```

---

### Task 2: State Descriptor

**Files:**
- Create: `pyrox/core/state.py`
- Create: `tests/test_state.py`

**Reference:** `src/pytonium_python_framework/Pytonium/components/state.py` (lines 1-100 — the State class)

- [ ] **Step 1: Write failing tests for State**

```python
# tests/test_state.py
"""Tests for the State descriptor."""
import pytest
from pyrox.core.state import State, Computed


class TestState:
    def test_default_value(self):
        class MyComp:
            count = State(0)
        obj = MyComp()
        assert obj.count == 0

    def test_set_and_get(self):
        class MyComp:
            name = State("hello")
        obj = MyComp()
        obj.name = "world"
        assert obj.name == "world"

    def test_independent_instances(self):
        class MyComp:
            count = State(0)
        a = MyComp()
        b = MyComp()
        a.count = 5
        assert b.count == 0

    def test_change_callback_fires(self):
        changes = []
        class MyComp:
            count = State(0)
            def _on_state_change(self, field_name, old_value, new_value):
                changes.append((field_name, old_value, new_value))
        obj = MyComp()
        obj.count = 42
        assert changes == [("count", 0, 42)]

    def test_no_callback_on_same_value(self):
        changes = []
        class MyComp:
            count = State(0)
            def _on_state_change(self, field_name, old_value, new_value):
                changes.append((field_name, old_value, new_value))
        obj = MyComp()
        obj.count = 0  # Same as default
        assert changes == []

    def test_none_default(self):
        class MyComp:
            data = State(None)
        obj = MyComp()
        assert obj.data is None
        obj.data = {"key": "value"}
        assert obj.data == {"key": "value"}

    def test_multiple_fields(self):
        class MyComp:
            x = State(0)
            y = State(0)
            name = State("")
        obj = MyComp()
        obj.x = 10
        obj.y = 20
        obj.name = "test"
        assert obj.x == 10
        assert obj.y == 20
        assert obj.name == "test"


class TestComputed:
    def test_basic_computed(self):
        class MyComp:
            first = State("John")
            last = State("Doe")

            @Computed
            def full_name(self):
                return f"{self.first} {self.last}"

        obj = MyComp()
        assert obj.full_name == "John Doe"

    def test_computed_caches(self):
        call_count = 0
        class MyComp:
            x = State(1)

            @Computed
            def doubled(self):
                nonlocal call_count
                call_count += 1
                return self.x * 2

        obj = MyComp()
        assert obj.doubled == 2
        assert obj.doubled == 2  # Should use cache
        assert call_count == 1

    def test_computed_invalidates_on_dep_change(self):
        class MyComp:
            x = State(1)

            @Computed
            def doubled(self):
                return self.x * 2

        obj = MyComp()
        assert obj.doubled == 2
        obj.x = 5
        assert obj.doubled == 10
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd pyrox_project && python -m pytest tests/test_state.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement State descriptor**

```python
# pyrox/core/state.py
"""State descriptor and Computed decorator for Pyrox reactive components.

State is a Python descriptor that stores per-instance values and fires
a change notification callback when the value changes. Unlike Pytonium's
State which notifies a global DependencyTracker, Pyrox's State calls
the component's _on_state_change() method (if defined), which the
DependencyTracker hooks into during registration.

Computed is a descriptor for cached derived properties. It tracks which
State fields were accessed during computation and invalidates when any
dependency changes.
"""

from typing import Any, Callable, Optional

# Sentinel for "no value set yet"
_UNSET = object()


class State:
    """Descriptor for reactive state fields on Component subclasses.

    Usage::

        class Counter(Component):
            count = State(0)

            async def increment(self):
                self.count += 1  # Triggers _on_state_change
    """

    def __init__(self, default: Any = None):
        self._default = default
        self._name: str = ""
        self._storage_key: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name
        self._storage_key = f"_state_{name}"

    def __get__(self, obj: Any, objtype: type = None) -> Any:
        if obj is None:
            return self  # Class-level access returns the descriptor
        value = getattr(obj, self._storage_key, _UNSET)
        if value is _UNSET:
            value = self._default
            # Store so subsequent gets don't hit _UNSET path
            object.__setattr__(obj, self._storage_key, value)
        # Record access for dependency tracking
        tracker = getattr(obj, "_tracker", None)
        if tracker is not None:
            tracker.record_access(self._name)
        return value

    def __set__(self, obj: Any, value: Any) -> None:
        old = getattr(obj, self._storage_key, _UNSET)
        if old is _UNSET:
            old = self._default
        if old == value:
            return  # No change, skip notification
        object.__setattr__(obj, self._storage_key, value)
        # Invalidate any Computed properties that depend on this field
        _invalidate_computed_deps(obj, self._name)
        # Notify the component (DependencyTracker hooks into this)
        callback = getattr(obj, "_on_state_change", None)
        if callback is not None:
            callback(self._name, old, value)


def _invalidate_computed_deps(obj: Any, field_name: str) -> None:
    """Invalidate Computed properties that depend on the changed field."""
    computed_deps = getattr(obj, "_computed_reverse_deps", None)
    if computed_deps is None:
        return
    dependents = computed_deps.get(field_name, set())
    for computed_name in dependents:
        cache_key = f"_computed_cache_{computed_name}"
        if hasattr(obj, cache_key):
            delattr(obj, cache_key)


class Computed:
    """Descriptor for cached derived properties.

    Caches the result until a dependency State field changes.

    Usage::

        class MyComp(Component):
            first = State("John")
            last = State("Doe")

            @Computed
            def full_name(self):
                return f"{self.first} {self.last}"
    """

    def __init__(self, func: Callable):
        self._func = func
        self._name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name

    def __get__(self, obj: Any, objtype: type = None) -> Any:
        if obj is None:
            return self

        cache_key = f"_computed_cache_{self._name}"
        cached = getattr(obj, cache_key, _UNSET)
        if cached is not _UNSET:
            return cached

        # Track dependencies AND compute value in a single call
        tracker = getattr(obj, "_tracker", None)
        if tracker is not None:
            value, deps = tracker.track_dependencies_with_result(self._func, obj)
        else:
            deps = set()
            value = self._func(obj)

        # Cache the result
        object.__setattr__(obj, cache_key, value)

        # Register reverse deps so State.__set__ can invalidate
        if deps:
            reverse = getattr(obj, "_computed_reverse_deps", None)
            if reverse is None:
                reverse = {}
                object.__setattr__(obj, "_computed_reverse_deps", reverse)
            for dep_field in deps:
                if dep_field not in reverse:
                    reverse[dep_field] = set()
                reverse[dep_field].add(self._name)

        return value
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd pyrox_project && python -m pytest tests/test_state.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pyrox/core/state.py tests/test_state.py
git commit -m "feat(pyrox): State descriptor + Computed decorator"
```

---

### Task 3: DependencyTracker

**Files:**
- Create: `pyrox/core/tracker.py`
- Create: `tests/test_tracker.py`

**Reference:** `src/pytonium_python_framework/Pytonium/components/state.py` (DependencyTracker class, lines 100-542)

Key difference: Pyrox's tracker is **instance-scoped** (each component gets one), not class-level.

- [ ] **Step 1: Write failing tests for DependencyTracker**

```python
# tests/test_tracker.py
"""Tests for the instance-scoped DependencyTracker."""
import pytest
from pyrox.core.types import UpdateType, UpdateCommand, Binding
from pyrox.core.tracker import DependencyTracker
from pyrox.core.state import State


class StubComponent:
    """Minimal component-like object for testing."""
    x = State(0)
    y = State(0)

    def __init__(self):
        self._tracker = DependencyTracker()
        self._tracker.register(self)
        self._batch: list[dict] = []

    def _on_state_change(self, field_name, old_value, new_value):
        self._tracker.notify_change(field_name, old_value, new_value)


class TestDependencyTracker:
    def test_record_and_track(self):
        tracker = DependencyTracker()
        tracker.record_access("x")
        tracker.record_access("y")
        assert tracker.current_deps == {"x", "y"}
        tracker.clear_tracking()
        assert tracker.current_deps == set()

    def test_track_dependencies_of_lambda(self):
        comp = StubComponent()
        fn = lambda: comp.x + comp.y
        deps = comp._tracker.track_dependencies(fn, comp)
        assert deps == {"x", "y"}

    def test_add_binding(self):
        tracker = DependencyTracker()
        binding = Binding(
            node_id="c0-n1",
            update_type=UpdateType.SET_TEXT_CONTENT,
            transform=lambda: "hello",
        )
        tracker.add_binding("x", binding)
        assert tracker.get_bindings("x") == [binding]

    def test_notify_change_produces_commands(self):
        comp = StubComponent()
        binding = Binding(
            node_id="c0-n1",
            update_type=UpdateType.SET_TEXT_CONTENT,
            transform=lambda: f"x={comp.x}",
        )
        comp._tracker.add_binding("x", binding)
        comp.x = 42  # Triggers notify_change
        # Check that a command was produced
        commands = comp._tracker.pending_commands
        assert len(commands) == 1
        assert commands[0].node_id == "c0-n1"
        assert commands[0].value == "x=42"

    def test_no_commands_for_unbound_field(self):
        comp = StubComponent()
        comp.x = 10  # No bindings for x
        assert comp._tracker.pending_commands == []

    def test_remove_bindings_for_element(self):
        tracker = DependencyTracker()
        b1 = Binding(node_id="c0-n1", update_type=UpdateType.SET_TEXT_CONTENT)
        b2 = Binding(node_id="c0-n2", update_type=UpdateType.SET_TEXT_CONTENT)
        tracker.add_binding("x", b1)
        tracker.add_binding("x", b2)
        tracker.remove_bindings_for_node("c0-n1")
        assert tracker.get_bindings("x") == [b2]

    def test_clear_pending_commands(self):
        comp = StubComponent()
        binding = Binding(
            node_id="c0-n1",
            update_type=UpdateType.SET_TEXT_CONTENT,
            transform=lambda: f"x={comp.x}",
        )
        comp._tracker.add_binding("x", binding)
        comp.x = 5
        assert len(comp._tracker.pending_commands) == 1
        comp._tracker.clear_pending()
        assert comp._tracker.pending_commands == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd pyrox_project && python -m pytest tests/test_tracker.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement DependencyTracker**

```python
# pyrox/core/tracker.py
"""Instance-scoped DependencyTracker for Pyrox reactive components.

Unlike Pytonium's class-level DependencyTracker, each Pyrox component
instance gets its own tracker. This eliminates id() reuse bugs, simplifies
cleanup (GC handles it), and enables multi-session safety.

The tracker:
- Records State field accesses during lambda evaluation (for dependency discovery)
- Stores bindings (field_name → list[Binding])
- On state change, evaluates bindings and queues UpdateCommands
"""

from typing import Any, Callable

from .types import Binding, UpdateCommand, UpdateType


class DependencyTracker:
    """Per-component dependency tracker.

    Manages the mapping from State field names to their reactive Bindings,
    and produces UpdateCommands when state changes.
    """

    def __init__(self):
        self._bindings: dict[str, list[Binding]] = {}
        self._tracking: bool = False
        self._current_deps: set[str] = set()
        self._pending_commands: list[UpdateCommand] = []
        self._component: Any = None

    def register(self, component: Any) -> None:
        """Bind this tracker to its owning component."""
        self._component = component

    def record_access(self, field_name: str) -> None:
        """Record that a State field was accessed (called by State.__get__)."""
        if self._tracking:
            self._current_deps.add(field_name)

    @property
    def current_deps(self) -> set[str]:
        """Currently tracked dependencies (during a tracking session)."""
        return set(self._current_deps)

    def clear_tracking(self) -> None:
        """Reset the current tracking session."""
        self._current_deps.clear()
        self._tracking = False

    def track_dependencies(self, fn: Callable, component: Any) -> set[str]:
        """Execute fn and return the set of State fields it accessed.

        Args:
            fn: A lambda or function to evaluate.
            component: The component instance (passed to fn if it takes args).

        Returns:
            Set of State field names accessed during fn's execution.
        """
        _, deps = self.track_dependencies_with_result(fn, component)
        return deps

    def track_dependencies_with_result(self, fn: Callable, component: Any) -> tuple[Any, set[str]]:
        """Execute fn and return both its result and the set of State fields accessed.

        Used by Computed to avoid double-invocation.

        Args:
            fn: A lambda or function to evaluate.
            component: The component instance (passed to fn if it takes args).

        Returns:
            Tuple of (return value, set of dependency field names).
        """
        self._tracking = True
        self._current_deps.clear()
        result = None
        try:
            # Try calling with no args (lambda: ...) first
            try:
                result = fn()
            except TypeError:
                result = fn(component)
        finally:
            self._tracking = False
        deps = set(self._current_deps)
        self._current_deps.clear()
        return result, deps

    def add_binding(self, field_name: str, binding: Binding) -> None:
        """Register a reactive binding for a State field."""
        if field_name not in self._bindings:
            self._bindings[field_name] = []
        self._bindings[field_name].append(binding)

    def get_bindings(self, field_name: str) -> list[Binding]:
        """Get all bindings for a State field."""
        return list(self._bindings.get(field_name, []))

    def remove_bindings_for_node(self, node_id: str) -> None:
        """Remove all bindings targeting a specific node."""
        for field_name in self._bindings:
            self._bindings[field_name] = [
                b for b in self._bindings[field_name] if b.node_id != node_id
            ]

    def notify_change(self, field_name: str, old_value: Any, new_value: Any) -> None:
        """Called when a State field changes. Evaluates bindings and queues commands.

        Args:
            field_name: Name of the changed State field.
            old_value: Previous value.
            new_value: New value.
        """
        bindings = self._bindings.get(field_name, [])
        for binding in bindings:
            # Handle dynamic children (children_from)
            if binding._dynamic_manager_element is not None:
                element = binding._dynamic_manager_element
                manager = getattr(element, "_dynamic_manager", None)
                if manager is not None:
                    manager.update()
                continue

            # Handle conditional elements (Show/Switch)
            if binding._conditional_element is not None:
                element = binding._conditional_element
                if hasattr(element, "_evaluate_condition"):
                    element._evaluate_condition()
                continue

            # Standard binding — evaluate transform and queue command
            if binding.transform is not None:
                try:
                    result = binding.transform()
                except Exception:
                    continue  # Skip broken bindings

                # Handle class_toggle: emit ADD_CLASS or REMOVE_CLASS based on bool
                if binding._is_class_toggle:
                    cmd = UpdateCommand(
                        node_id=binding.node_id,
                        update_type=UpdateType.ADD_CLASS if result else UpdateType.REMOVE_CLASS,
                        key=binding.key,
                        value=binding.key,
                    )
                else:
                    cmd = UpdateCommand(
                        node_id=binding.node_id,
                        update_type=binding.update_type,
                        key=binding.key,
                        value=str(result),
                    )
                self._pending_commands.append(cmd)

    @property
    def pending_commands(self) -> list[UpdateCommand]:
        """Commands queued since the last clear."""
        return list(self._pending_commands)

    def clear_pending(self) -> None:
        """Clear all pending commands (after flushing)."""
        self._pending_commands.clear()

    def analyze_element(self, element: Any) -> None:
        """Analyze an element tree for reactive bindings.

        Walks the element tree, evaluates each reactive lambda in tracking
        mode, and registers bindings for discovered dependencies.

        Args:
            element: Root Element to analyze.
        """
        # Analyze this element's bindings
        for binding_info in getattr(element, "_reactive_bindings", []):
            fn = binding_info["fn"]
            update_type = binding_info["update_type"]
            key = binding_info.get("key", "")

            # Track dependencies
            self._tracking = True
            self._current_deps.clear()
            try:
                fn()
            except Exception:
                pass
            finally:
                self._tracking = False

            deps = set(self._current_deps)
            self._current_deps.clear()

            # Create binding and register for each dependency
            is_toggle = binding_info.get("_is_class_toggle", False)
            binding = Binding(
                node_id=element.node_id,
                update_type=update_type,
                key=key,
                transform=fn,
                _is_class_toggle=is_toggle,
            )
            for dep in deps:
                self.add_binding(dep, binding)

        # Handle children_from
        if hasattr(element, "_dynamic_children") and element._dynamic_children:
            source_fn = element._dynamic_children["source"]
            self._tracking = True
            self._current_deps.clear()
            try:
                source_fn()
            except Exception:
                pass
            finally:
                self._tracking = False
            deps = set(self._current_deps)
            self._current_deps.clear()

            binding = Binding(
                node_id=element.node_id,
                update_type=UpdateType.REPLACE_INNER_HTML,
                key="_dynamic_children",
                transform=None,
                _dynamic_manager_element=element,
            )
            for dep in deps:
                self.add_binding(dep, binding)

        # Handle conditional elements (Show/Switch)
        if hasattr(element, "_condition_fn") and element._condition_fn:
            condition_fn = element._condition_fn
            self._tracking = True
            self._current_deps.clear()
            try:
                condition_fn()
            except Exception:
                pass
            finally:
                self._tracking = False
            deps = set(self._current_deps)
            self._current_deps.clear()

            binding = Binding(
                node_id=element.node_id,
                update_type=UpdateType.REPLACE_INNER_HTML,
                key="_conditional",
                transform=None,
                _conditional_element=element,
            )
            for dep in deps:
                self.add_binding(dep, binding)

        # Recurse into children
        for child in getattr(element, "_children", []):
            self.analyze_element(child)

        # Recurse into active conditional branch
        current = getattr(element, "_current_element", None)
        if current is not None:
            self.analyze_element(current)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd pyrox_project && python -m pytest tests/test_tracker.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pyrox/core/tracker.py tests/test_tracker.py
git commit -m "feat(pyrox): instance-scoped DependencyTracker"
```

---

## Chunk 2: Elements + MutationCompiler

### Task 4: Element Builder

**Files:**
- Create: `pyrox/core/elements.py`
- Create: `tests/test_elements.py`

**Reference:** `src/pytonium_python_framework/Pytonium/components/elements.py` (667 lines)

- [ ] **Step 1: Write failing tests for Elements**

```python
# tests/test_elements.py
"""Tests for the Element builder and HTML constructors."""
import pytest
from pyrox.core.elements import (
    Element, Div, Span, H1, Button, Input, Ul, Li, P, Form,
    reset_id_counter,
)


class TestElement:
    def setup_method(self):
        reset_id_counter()

    def test_basic_div(self):
        el = Div()
        html = el.to_html()
        assert '<div data-pyrox-id="n0">' in html
        assert '</div>' in html

    def test_text_static(self):
        el = H1().text("Hello")
        html = el.to_html()
        assert ">Hello</h1>" in html

    def test_text_reactive(self):
        el = H1().text(lambda: "Dynamic")
        html = el.to_html()
        assert ">Dynamic</h1>" in html
        assert el._reactive_bindings  # Should have a binding

    def test_child(self):
        el = Div().child(Span().text("inner"))
        html = el.to_html()
        assert "<span" in html
        assert "inner" in html

    def test_children_varargs(self):
        el = Div().child(Span(), P(), H1())
        assert len(el._children) == 3

    def test_attr_static(self):
        el = Div().attr("role", "button")
        html = el.to_html()
        assert 'role="button"' in html

    def test_attr_reactive(self):
        el = Div().attr("title", lambda: "dynamic")
        html = el.to_html()
        assert 'title="dynamic"' in html
        assert el._reactive_bindings

    def test_id(self):
        el = Div().id("myid")
        html = el.to_html()
        assert 'id="myid"' in html

    def test_cls(self):
        el = Div().cls("foo bar")
        html = el.to_html()
        assert 'class="foo bar"' in html

    def test_class_toggle(self):
        el = Div().class_toggle("active", lambda: True)
        html = el.to_html()
        assert "active" in html

    def test_style_static(self):
        el = Div().style("color", "red")
        html = el.to_html()
        assert 'style="color:red"' in html

    def test_style_reactive(self):
        el = Div().style("opacity", lambda: "0.5")
        html = el.to_html()
        assert 'style="opacity:0.5"' in html

    def test_on_click(self):
        handler = lambda: None
        el = Button().on_click(handler)
        assert "click" in el._events

    def test_on_input(self):
        handler = lambda e: None
        el = Input().on_input(handler)
        assert "input" in el._events

    def test_bind_value(self):
        el = Input().bind_value(lambda: "hello")
        html = el.to_html()
        assert 'value="hello"' in html

    def test_children_from(self):
        items = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        el = Ul().children_from(
            source=lambda: items,
            key=lambda item: item["id"],
            render_item=lambda item, i: Li().text(item["name"]),
        )
        html = el.to_html()
        assert "A" in html
        assert "B" in html
        assert el._dynamic_children is not None

    def test_raw_html(self):
        el = Div().raw_html(lambda: "<b>bold</b>")
        html = el.to_html()
        assert "<b>bold</b>" in html

    def test_node_ids_increment(self):
        reset_id_counter()
        a = Div()
        b = Div()
        c = Div()
        assert a.node_id == "n0"
        assert b.node_id == "n1"
        assert c.node_id == "n2"

    def test_node_ids_with_prefix(self):
        reset_id_counter("c1-")
        a = Div()
        b = Div()
        assert a.node_id == "c1-n0"
        assert b.node_id == "c1-n1"

    def test_to_html_escapes_text(self):
        el = Span().text("<script>alert('xss')</script>")
        html = el.to_html()
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_nested_structure(self):
        el = (
            Div()
                .child(H1().text("Title"))
                .child(
                    Ul()
                        .child(Li().text("Item 1"))
                        .child(Li().text("Item 2"))
                )
        )
        html = el.to_html()
        assert "Title" in html
        assert "Item 1" in html
        assert "Item 2" in html

    def test_find_by_tag(self):
        el = Div().child(Button().text("Click"))
        found = el.find("button")
        assert found is not None
        assert found._tag == "button"

    def test_find_returns_none(self):
        el = Div()
        assert el.find("input") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd pyrox_project && python -m pytest tests/test_elements.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement Element builder**

```python
# pyrox/core/elements.py
"""Element builder and HTML element constructors for Pyrox.

Provides a fluent builder API for constructing HTML element trees with
reactive bindings. Mirrors Pytonium's elements.py API but uses
data-pyrox-id attributes and stores reactive binding metadata for
the DependencyTracker to analyze.

Usage::

    tree = (
        Div().id("app")
            .child(H1().text(lambda: f"Count: {self.count}"))
            .child(Button().text("+").on_click(self.increment))
    )
    html = tree.to_html()
"""

from html import escape as html_escape
from typing import Any, Callable, Optional, Union

from .types import UpdateType

# Module-level ID counter and component prefix
_id_counter: int = 0
_id_prefix: str = ""


def reset_id_counter(prefix: str = "") -> None:
    """Reset the global node ID counter with an optional component prefix.

    Args:
        prefix: Component-scoped prefix (e.g., "c0-"). Set by Component._prepare().
    """
    global _id_counter, _id_prefix
    _id_counter = 0
    _id_prefix = prefix


def _next_id() -> str:
    """Generate the next node ID (e.g., "c0-n3")."""
    global _id_counter
    nid = f"{_id_prefix}n{_id_counter}"
    _id_counter += 1
    return nid


class Element:
    """HTML element builder with reactive binding support.

    Each element gets a unique data-pyrox-id for targeted DOM mutations.
    The builder pattern allows chaining: Div().cls("x").child(Span().text("hi"))
    """

    def __init__(self, tag: str, **attrs: str):
        self._tag = tag
        self.node_id = _next_id()
        self._children: list["Element"] = []
        self._static_attrs: dict[str, str] = dict(attrs)
        self._classes: list[str] = []
        self._static_text: Optional[str] = None
        self._reactive_text: Optional[Callable] = None
        self._raw_html_fn: Optional[Callable] = None
        self._static_styles: dict[str, str] = {}
        self._reactive_bindings: list[dict] = []
        self._events: dict[str, dict] = {}
        self._dynamic_children: Optional[dict] = None
        self._dynamic_initial_elements: Optional[list] = None
        self._dynamic_manager: Any = None
        self._condition_fn: Optional[Callable] = None
        self._current_element: Optional["Element"] = None
        self._bind_value_fn: Optional[Callable] = None

    # --- Builder methods (all return self for chaining) ---

    def child(self, *elements: "Element") -> "Element":
        """Add one or more child elements."""
        self._children.extend(elements)
        return self

    def children(self, *elements: "Element") -> "Element":
        """Alias for child() with multiple elements."""
        return self.child(*elements)

    def text(self, content: Union[str, Callable]) -> "Element":
        """Set text content (static string or reactive lambda)."""
        if callable(content):
            self._reactive_text = content
            self._reactive_bindings.append({
                "fn": content,
                "update_type": UpdateType.SET_TEXT_CONTENT,
            })
        else:
            self._static_text = content
        return self

    def raw_html(self, content: Union[str, Callable]) -> "Element":
        """Set innerHTML without escaping. Use only with trusted content."""
        if callable(content):
            self._raw_html_fn = content
            self._reactive_bindings.append({
                "fn": content,
                "update_type": UpdateType.REPLACE_INNER_HTML,
            })
        else:
            self._raw_html_fn = lambda _c=content: _c
        return self

    def attr(self, name: str, value: Union[str, Callable]) -> "Element":
        """Set an HTML attribute (static or reactive)."""
        if callable(value):
            self._reactive_bindings.append({
                "fn": value,
                "update_type": UpdateType.SET_ATTRIBUTE,
                "key": name,
            })
            # Evaluate for initial render
            try:
                self._static_attrs[name] = str(value())
            except Exception:
                pass
        else:
            self._static_attrs[name] = value
        return self

    def id(self, html_id: str) -> "Element":
        """Set the HTML id attribute."""
        self._static_attrs["id"] = html_id
        return self

    def cls(self, class_names: str) -> "Element":
        """Set CSS class names (space-separated string)."""
        self._classes.extend(class_names.split())
        return self

    def class_name(self, name: str) -> "Element":
        """Add a single CSS class."""
        self._classes.append(name)
        return self

    def class_toggle(self, name: str, condition: Callable) -> "Element":
        """Toggle a CSS class based on a reactive condition.

        Uses ADD_CLASS/REMOVE_CLASS internally (not TOGGLE_CLASS) to avoid
        toggle-semantics bugs where repeated True would flip the class off.
        The DependencyTracker evaluates the condition and emits the correct op.
        """
        # Store both the condition and class name for the tracker to resolve
        self._reactive_bindings.append({
            "fn": condition,
            "update_type": UpdateType.ADD_CLASS,  # Tracker will emit ADD or REMOVE
            "key": name,
            "_is_class_toggle": True,  # Marker for tracker to handle specially
        })
        # Evaluate for initial render
        try:
            if condition():
                self._classes.append(name)
        except Exception:
            pass
        return self

    def style(self, prop: str, value: Union[str, Callable]) -> "Element":
        """Set a CSS style property (static or reactive)."""
        if callable(value):
            self._reactive_bindings.append({
                "fn": value,
                "update_type": UpdateType.SET_STYLE,
                "key": prop,
            })
            try:
                self._static_styles[prop] = str(value())
            except Exception:
                pass
        else:
            self._static_styles[prop] = value
        return self

    def bind_value(self, value_fn: Callable) -> "Element":
        """Bind the input value to a reactive source."""
        self._bind_value_fn = value_fn
        self._reactive_bindings.append({
            "fn": value_fn,
            "update_type": UpdateType.SET_VALUE,
        })
        return self

    # --- Event handlers ---

    def _on(self, event_type: str, handler: Callable, **opts) -> "Element":
        """Register an event handler."""
        self._events[event_type] = {"handler": handler, **opts}
        return self

    def on_click(self, handler: Callable) -> "Element":
        return self._on("click", handler)

    def on_dblclick(self, handler: Callable) -> "Element":
        return self._on("dblclick", handler)

    def on_input(self, handler: Callable) -> "Element":
        return self._on("input", handler)

    def on_change(self, handler: Callable) -> "Element":
        return self._on("change", handler)

    def on_submit(self, handler: Callable) -> "Element":
        return self._on("submit", handler)

    def on_keydown(self, handler: Callable) -> "Element":
        return self._on("keydown", handler)

    def on_keyup(self, handler: Callable) -> "Element":
        return self._on("keyup", handler)

    def on_mouseenter(self, handler: Callable) -> "Element":
        return self._on("mouseenter", handler)

    def on_mouseleave(self, handler: Callable) -> "Element":
        return self._on("mouseleave", handler)

    def on_focus(self, handler: Callable) -> "Element":
        return self._on("focus", handler)

    def on_blur(self, handler: Callable) -> "Element":
        return self._on("blur", handler)

    # --- Dynamic children ---

    def children_from(
        self,
        source: Callable,
        key: Callable,
        render_item: Callable,
    ) -> "Element":
        """Configure dynamic children from a reactive list source.

        Args:
            source: Lambda returning the list of items.
            key: Function extracting a stable key from each item.
            render_item: Function(item, index) → Element for each item.
        """
        self._dynamic_children = {
            "source": source,
            "key": key,
            "render_item": render_item,
        }
        return self

    # --- Query ---

    def find(self, tag: str) -> Optional["Element"]:
        """Find the first descendant element with the given tag name."""
        if self._tag == tag:
            return self
        for child in self._children:
            found = child.find(tag)
            if found is not None:
                return found
        return None

    # --- HTML generation ---

    def to_html(self) -> str:
        """Generate the HTML string for this element and its children."""
        parts = [f"<{self._tag}"]

        # data-pyrox-id
        parts.append(f' data-pyrox-id="{self.node_id}"')

        # Static attributes
        for name, value in self._static_attrs.items():
            parts.append(f' {name}="{html_escape(value, quote=True)}"')

        # Classes
        if self._classes:
            parts.append(f' class="{html_escape(" ".join(self._classes), quote=True)}"')

        # Styles
        if self._static_styles:
            style_str = ";".join(f"{k}:{v}" for k, v in self._static_styles.items())
            parts.append(f' style="{html_escape(style_str, quote=True)}"')

        # Input value
        if self._bind_value_fn is not None:
            try:
                val = str(self._bind_value_fn())
                parts.append(f' value="{html_escape(val, quote=True)}"')
            except Exception:
                pass

        parts.append(">")

        # Content
        if self._raw_html_fn is not None:
            try:
                parts.append(str(self._raw_html_fn()))
            except Exception:
                pass
        elif self._reactive_text is not None:
            try:
                parts.append(html_escape(str(self._reactive_text())))
            except Exception:
                pass
        elif self._static_text is not None:
            parts.append(html_escape(str(self._static_text)))

        # Dynamic children (children_from)
        if self._dynamic_children:
            source_fn = self._dynamic_children["source"]
            key_fn = self._dynamic_children["key"]
            render_item_fn = self._dynamic_children["render_item"]
            self._dynamic_initial_elements = []
            try:
                items = source_fn()
                for i, item in enumerate(items):
                    child_element = render_item_fn(item, i)
                    item_key = str(key_fn(item))
                    self._dynamic_initial_elements.append((item_key, child_element))
                    parts.append(child_element.to_html())
            except Exception:
                pass
        else:
            # Static children
            for child in self._children:
                parts.append(child.to_html())

        # Closing tag (void elements don't get closing tags)
        if self._tag not in _VOID_TAGS:
            parts.append(f"</{self._tag}>")

        return "".join(parts)


# --- HTML element constructors ---
# Each is a plain function returning an Element instance.


# Module-level constant for void elements (no closing tag)
_VOID_TAGS = frozenset({"br", "hr", "img", "input", "meta", "link"})


def Div(**attrs) -> Element: return Element("div", **attrs)
def Span(**attrs) -> Element: return Element("span", **attrs)
def P(**attrs) -> Element: return Element("p", **attrs)
def H1(**attrs) -> Element: return Element("h1", **attrs)
def H2(**attrs) -> Element: return Element("h2", **attrs)
def H3(**attrs) -> Element: return Element("h3", **attrs)
def H4(**attrs) -> Element: return Element("h4", **attrs)
def H5(**attrs) -> Element: return Element("h5", **attrs)
def H6(**attrs) -> Element: return Element("h6", **attrs)
def Button(**attrs) -> Element: return Element("button", **attrs)
def Input(**attrs) -> Element: return Element("input", **attrs)
def Textarea(**attrs) -> Element: return Element("textarea", **attrs)
def Select(**attrs) -> Element: return Element("select", **attrs)
def Option(**attrs) -> Element: return Element("option", **attrs)
def Label(**attrs) -> Element: return Element("label", **attrs)
def Form(**attrs) -> Element: return Element("form", **attrs)
def A(**attrs) -> Element: return Element("a", **attrs)
def Img(**attrs) -> Element: return Element("img", **attrs)
def Ul(**attrs) -> Element: return Element("ul", **attrs)
def Ol(**attrs) -> Element: return Element("ol", **attrs)
def Li(**attrs) -> Element: return Element("li", **attrs)
def Table(**attrs) -> Element: return Element("table", **attrs)
def Tr(**attrs) -> Element: return Element("tr", **attrs)
def Td(**attrs) -> Element: return Element("td", **attrs)
def Th(**attrs) -> Element: return Element("th", **attrs)
def Thead(**attrs) -> Element: return Element("thead", **attrs)
def Tbody(**attrs) -> Element: return Element("tbody", **attrs)
def Header(**attrs) -> Element: return Element("header", **attrs)
def Footer(**attrs) -> Element: return Element("footer", **attrs)
def Nav(**attrs) -> Element: return Element("nav", **attrs)
def Section(**attrs) -> Element: return Element("section", **attrs)
def Article(**attrs) -> Element: return Element("article", **attrs)
def Main(**attrs) -> Element: return Element("main", **attrs)
def Pre(**attrs) -> Element: return Element("pre", **attrs)
def Code(**attrs) -> Element: return Element("code", **attrs)
def Hr() -> Element: return Element("hr")
def Br() -> Element: return Element("br")
def Strong(**attrs) -> Element: return Element("strong", **attrs)
def Em(**attrs) -> Element: return Element("em", **attrs)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd pyrox_project && python -m pytest tests/test_elements.py -v`
Expected: All 22 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pyrox/core/elements.py tests/test_elements.py
git commit -m "feat(pyrox): Element builder + 35 HTML constructors"
```

---

### Task 5: MutationCompiler (JSON output)

**Files:**
- Create: `pyrox/compiler/__init__.py`
- Create: `pyrox/compiler/mutation_compiler.py`
- Create: `pyrox/compiler/codec.py`
- Create: `tests/test_mutation_compiler.py`
- Create: `tests/test_codec.py`

**Reference:** `src/pytonium_python_framework/Pytonium/components/mutation_compiler.py` (190 lines)

Key difference: Pyrox outputs JSON dicts, not JS strings.

- [ ] **Step 1: Write failing tests for MutationCompiler**

```python
# tests/test_mutation_compiler.py
"""Tests for MutationCompiler (JSON output)."""
import pytest
from pyrox.core.types import UpdateType, UpdateCommand
from pyrox.compiler.mutation_compiler import MutationCompiler


class TestMutationCompiler:
    def test_compile_text_content(self):
        compiler = MutationCompiler()
        cmds = [UpdateCommand(
            node_id="c0-n1",
            update_type=UpdateType.SET_TEXT_CONTENT,
            value="Hello",
        )]
        result = compiler.compile_batch(cmds)
        assert result == [{"op": "text", "id": "c0-n1", "value": "Hello"}]

    def test_compile_set_attribute(self):
        compiler = MutationCompiler()
        cmds = [UpdateCommand(
            node_id="c0-n2",
            update_type=UpdateType.SET_ATTRIBUTE,
            key="title",
            value="My Title",
        )]
        result = compiler.compile_batch(cmds)
        assert result == [{"op": "attr", "id": "c0-n2", "key": "title", "value": "My Title"}]

    def test_compile_insert_child(self):
        compiler = MutationCompiler()
        cmds = [UpdateCommand(
            node_id="c0-n0",
            update_type=UpdateType.INSERT_CHILD,
            value="child-key",
            index=2,
            html="<li>new</li>",
        )]
        result = compiler.compile_batch(cmds)
        assert result == [{
            "op": "insert", "id": "c0-n0",
            "html": "<li>new</li>", "index": 2,
        }]

    def test_compile_remove_child(self):
        compiler = MutationCompiler()
        cmds = [UpdateCommand(
            node_id="c0-n0",
            update_type=UpdateType.REMOVE_CHILD,
            value="c0-n5",
        )]
        result = compiler.compile_batch(cmds)
        assert result == [{"op": "remove", "id": "c0-n0", "child": "c0-n5"}]

    def test_compile_batch_multiple(self):
        compiler = MutationCompiler()
        cmds = [
            UpdateCommand(node_id="c0-n1", update_type=UpdateType.SET_TEXT_CONTENT, value="A"),
            UpdateCommand(node_id="c0-n2", update_type=UpdateType.ADD_CLASS, value="active"),
            UpdateCommand(node_id="c0-n3", update_type=UpdateType.SET_STYLE, key="color", value="red"),
        ]
        result = compiler.compile_batch(cmds)
        assert len(result) == 3
        assert result[0]["op"] == "text"
        assert result[1]["op"] == "class_add"
        assert result[2]["op"] == "style"

    def test_compile_empty_batch(self):
        compiler = MutationCompiler()
        assert compiler.compile_batch([]) == []

    def test_html_escapes_text_values(self):
        compiler = MutationCompiler()
        cmds = [UpdateCommand(
            node_id="c0-n1",
            update_type=UpdateType.SET_TEXT_CONTENT,
            value="<script>alert('xss')</script>",
        )]
        result = compiler.compile_batch(cmds)
        assert "<script>" not in result[0]["value"]
        assert "&lt;script&gt;" in result[0]["value"]

    def test_does_not_escape_inner_html(self):
        compiler = MutationCompiler()
        cmds = [UpdateCommand(
            node_id="c0-n1",
            update_type=UpdateType.REPLACE_INNER_HTML,
            html="<b>bold</b>",
        )]
        result = compiler.compile_batch(cmds)
        assert result[0]["html"] == "<b>bold</b>"
```

```python
# tests/test_codec.py
"""Tests for WebSocket message codec."""
import json
import pytest
from pyrox.compiler.codec import encode_message, decode_message


class TestCodec:
    def test_encode_mutations(self):
        msg = {"type": "mutations", "batch": [{"op": "text", "id": "n1", "value": "hi"}]}
        encoded = encode_message(msg)
        assert isinstance(encoded, str)
        decoded = json.loads(encoded)
        assert decoded == msg

    def test_decode_event(self):
        raw = '{"type": "event", "node_id": "n3", "event": "click", "data": {}}'
        msg = decode_message(raw)
        assert msg["type"] == "event"
        assert msg["node_id"] == "n3"

    def test_decode_input(self):
        raw = '{"type": "input", "node_id": "n7", "value": "hello"}'
        msg = decode_message(raw)
        assert msg["type"] == "input"
        assert msg["value"] == "hello"

    def test_decode_invalid_json(self):
        with pytest.raises(ValueError):
            decode_message("not json")

    def test_decode_missing_type(self):
        with pytest.raises(ValueError):
            decode_message('{"node_id": "n1"}')

    def test_decode_unknown_type(self):
        with pytest.raises(ValueError, match="Unknown client message type"):
            decode_message('{"type": "hack"}')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd pyrox_project && python -m pytest tests/test_mutation_compiler.py tests/test_codec.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement MutationCompiler and codec**

```python
# pyrox/compiler/__init__.py
"""Pyrox mutation compiler and message codec."""

# pyrox/compiler/mutation_compiler.py
"""MutationCompiler — converts UpdateCommands to JSON mutation dicts.

Unlike Pytonium's MutationCompiler which outputs JavaScript strings,
Pyrox outputs JSON-serializable dicts matching the WebSocket protocol.
The client JS library interprets these dicts and applies DOM mutations.
"""

from html import escape as html_escape
from typing import Any

from ..core.types import UpdateCommand, UpdateType


class MutationCompiler:
    """Compiles UpdateCommand lists into JSON mutation batches.

    Each UpdateCommand becomes a dict like:
        {"op": "text", "id": "c0-n1", "value": "Hello"}

    Text content values are HTML-escaped by default to prevent XSS.
    REPLACE_INNER_HTML is NOT escaped (opt-in raw HTML).
    """

    def __init__(self):
        self._pending: list[dict[str, Any]] = []

    def compile_batch(self, commands: list[UpdateCommand]) -> list[dict[str, Any]]:
        """Compile a list of UpdateCommands into JSON mutation dicts.

        Args:
            commands: List of UpdateCommands to compile.

        Returns:
            List of JSON-serializable mutation dicts.
        """
        return [self._compile_single(cmd) for cmd in commands]

    def apply_batch(self, commands: list[UpdateCommand]) -> None:
        """Compile commands and add them to the pending queue.

        Used by DynamicChildrenManager and conditionals to queue mutations
        that will be collected during the next flush.
        """
        self._pending.extend(self.compile_batch(commands))

    def apply_single(self, cmd: UpdateCommand) -> None:
        """Compile a single command and add to the pending queue."""
        self._pending.append(self._compile_single(cmd))

    def collect_pending(self) -> list[dict[str, Any]]:
        """Collect and clear all pending mutations."""
        result = list(self._pending)
        self._pending.clear()
        return result

    def _compile_single(self, cmd: UpdateCommand) -> dict[str, Any]:
        """Compile a single UpdateCommand to a JSON mutation dict."""
        op = cmd.update_type.value  # e.g., "text", "attr", "insert"
        result: dict[str, Any] = {"op": op, "id": cmd.node_id}

        match cmd.update_type:
            case UpdateType.SET_TEXT_CONTENT:
                result["value"] = html_escape(cmd.value)

            case UpdateType.SET_ATTRIBUTE:
                result["key"] = cmd.key
                result["value"] = cmd.value

            case UpdateType.REMOVE_ATTRIBUTE:
                result["key"] = cmd.key

            case UpdateType.ADD_CLASS | UpdateType.REMOVE_CLASS | UpdateType.TOGGLE_CLASS:
                result["value"] = cmd.value

            case UpdateType.SET_STYLE:
                result["key"] = cmd.key
                result["value"] = cmd.value

            case UpdateType.SET_VALUE:
                result["value"] = cmd.value

            case UpdateType.INSERT_CHILD:
                result["html"] = cmd.html
                result["index"] = cmd.index

            case UpdateType.REMOVE_CHILD:
                result["child"] = cmd.value

            case UpdateType.MOVE_CHILD:
                result["child"] = cmd.value
                result["index"] = cmd.index

            case UpdateType.REPLACE_INNER_HTML:
                result["html"] = cmd.html  # NOT escaped — developer opted in

        return result
```

```python
# pyrox/compiler/codec.py
"""WebSocket message encode/decode for the Pyrox protocol.

All messages are JSON strings. The codec validates the 'type' field
and provides a clean interface for message handling.
"""

import json
from typing import Any


_VALID_CLIENT_TYPES = {"event", "input", "reconnect", "init"}


def encode_message(msg: dict[str, Any]) -> str:
    """Encode a message dict to a JSON string for WebSocket transmission.

    Args:
        msg: Message dict with at least a 'type' field.

    Returns:
        JSON string.
    """
    return json.dumps(msg, separators=(",", ":"))


def decode_message(raw: str) -> dict[str, Any]:
    """Decode a JSON string from WebSocket into a message dict.

    Args:
        raw: JSON string received from client.

    Returns:
        Parsed message dict.

    Raises:
        ValueError: If JSON is invalid or 'type' field is missing.
    """
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON message: {e}") from e

    if not isinstance(msg, dict) or "type" not in msg:
        raise ValueError("Message must be a JSON object with a 'type' field")

    if msg["type"] not in _VALID_CLIENT_TYPES:
        raise ValueError(f"Unknown client message type: {msg['type']}")

    return msg
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd pyrox_project && python -m pytest tests/test_mutation_compiler.py tests/test_codec.py -v`
Expected: All 13 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pyrox/compiler/ tests/test_mutation_compiler.py tests/test_codec.py
git commit -m "feat(pyrox): MutationCompiler (JSON output) + message codec"
```

---

## Chunk 3: Conditionals + DynamicChildren + EventDispatcher

### Task 6: Conditional Elements (Show/Switch)

**Files:**
- Create: `pyrox/core/conditionals.py`
- Create: `tests/test_conditionals.py`

**Reference:** `src/pytonium_python_framework/Pytonium/components/conditional.py` (286 lines)

- [ ] **Step 1: Write failing tests for Show and Switch**

```python
# tests/test_conditionals.py
"""Tests for Show and Switch conditional elements."""
import pytest
from pyrox.core.elements import Div, Span, P, reset_id_counter
from pyrox.core.conditionals import Show, Switch


class TestShow:
    def setup_method(self):
        reset_id_counter()

    def test_show_when_true(self):
        el = Show(when=lambda: True, then=lambda: Span().text("visible"))
        html = el.to_html()
        assert "visible" in html

    def test_show_when_false(self):
        el = Show(when=lambda: False, then=lambda: Span().text("visible"))
        html = el.to_html()
        assert "visible" not in html

    def test_show_with_fallback(self):
        el = Show(
            when=lambda: False,
            then=lambda: Span().text("yes"),
            fallback=lambda: Span().text("no"),
        )
        html = el.to_html()
        assert "no" in html
        assert "yes" not in html

    def test_show_renders_as_div_wrapper(self):
        el = Show(when=lambda: True, then=lambda: Span().text("hi"))
        html = el.to_html()
        assert html.startswith("<div")

    def test_show_has_condition_fn(self):
        fn = lambda: True
        el = Show(when=fn, then=lambda: Span())
        assert el._condition_fn is fn

    def test_show_current_element(self):
        el = Show(when=lambda: True, then=lambda: Span().text("active"))
        el.to_html()  # Triggers initial evaluation
        assert el._current_element is not None


class TestSwitch:
    def setup_method(self):
        reset_id_counter()

    def test_switch_selects_matching_case(self):
        el = (
            Switch(selector=lambda: "b")
                .case("a", lambda: Span().text("A"))
                .case("b", lambda: Span().text("B"))
                .case("c", lambda: Span().text("C"))
        )
        html = el.to_html()
        assert "B" in html
        assert "A" not in html
        assert "C" not in html

    def test_switch_default(self):
        el = (
            Switch(selector=lambda: "unknown")
                .case("a", lambda: Span().text("A"))
                .default(lambda: Span().text("default"))
        )
        html = el.to_html()
        assert "default" in html
        assert "A" not in html

    def test_switch_no_match_no_default(self):
        el = (
            Switch(selector=lambda: "x")
                .case("a", lambda: Span().text("A"))
        )
        html = el.to_html()
        # Wrapper div exists but no content
        assert "<div" in html
        assert "A" not in html

    def test_switch_has_condition_fn(self):
        fn = lambda: "a"
        el = Switch(selector=fn)
        assert el._condition_fn is fn
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd pyrox_project && python -m pytest tests/test_conditionals.py -v`
Expected: FAIL

- [ ] **Step 3: Implement Show and Switch**

```python
# pyrox/core/conditionals.py
"""Conditional rendering elements: Show and Switch.

Show renders content based on a boolean condition.
Switch renders one of several branches based on a selector value.

Both render as <div> wrappers. When the condition changes, the inner
content is swapped via REPLACE_INNER_HTML mutations.

Reference: Pytonium's conditional.py (286 lines)
"""

from typing import Any, Callable, Optional

from .elements import Element, _next_id
from .types import UpdateType


class Show(Element):
    """Conditional element — renders content when condition is True.

    Usage::

        Show(
            when=lambda: self.logged_in,
            then=lambda: Div().text("Welcome!"),
            fallback=lambda: Div().text("Please log in"),
        )
    """

    def __init__(
        self,
        when: Callable,
        then: Callable,
        fallback: Optional[Callable] = None,
    ):
        super().__init__("div")
        self._condition_fn = when
        self._then_fn = then
        self._fallback_fn = fallback
        self._current_element: Optional[Element] = None
        self._current_branch: Optional[bool] = None
        self._mutation_compiler = None
        self._component = None
        self._event_router = None

    def _evaluate_condition(self) -> None:
        """Evaluate the condition and update the rendered branch if needed."""
        try:
            result = bool(self._condition_fn())
        except Exception:
            result = False

        if result == self._current_branch and self._current_element is not None:
            return  # No change

        old_element = self._current_element
        self._current_branch = result

        if result:
            self._current_element = self._then_fn()
        elif self._fallback_fn is not None:
            self._current_element = self._fallback_fn()
        else:
            self._current_element = None

        # Emit mutation if we have a compiler and the branch actually changed
        if self._mutation_compiler is not None:
            from .types import UpdateCommand
            html = self._current_element.to_html() if self._current_element else ""
            cmd = UpdateCommand(
                node_id=self.node_id,
                update_type=UpdateType.REPLACE_INNER_HTML,
                html=html,
            )
            self._mutation_compiler.apply_single(cmd)

            # Re-analyze dependencies for new element
            if self._current_element and self._component:
                tracker = getattr(self._component, "_tracker", None)
                if tracker:
                    tracker.analyze_element(self._current_element)

    def _setup_reactive(self, mutation_compiler, component, event_router) -> None:
        """Initialize reactive behavior (called during component mount)."""
        self._mutation_compiler = mutation_compiler
        self._component = component
        self._event_router = event_router

    def to_html(self) -> str:
        """Generate HTML with the currently active branch.
        Note: During to_html(), _mutation_compiler is None so no mutation is emitted.
        """
        self._evaluate_condition()

        parts = [f'<div data-pyrox-id="{self.node_id}">']
        if self._current_element is not None:
            parts.append(self._current_element.to_html())
        parts.append("</div>")
        return "".join(parts)


class Switch(Element):
    """Multi-branch conditional element.

    Usage::

        Switch(selector=lambda: self.tab)
            .case("home", lambda: HomePanel())
            .case("settings", lambda: SettingsPanel())
            .default(lambda: Div().text("Unknown tab"))
    """

    def __init__(self, selector: Callable):
        super().__init__("div")
        self._condition_fn = selector
        self._cases: list[tuple[Any, Callable]] = []
        self._default_fn: Optional[Callable] = None
        self._current_element: Optional[Element] = None
        self._current_value: Any = object()  # Sentinel for "no value yet"
        self._mutation_compiler = None
        self._component = None
        self._event_router = None

    def case(self, value: Any, element_fn: Callable) -> "Switch":
        """Add a case branch."""
        self._cases.append((value, element_fn))
        return self

    def default(self, element_fn: Callable) -> "Switch":
        """Add a default branch (used when no case matches)."""
        self._default_fn = element_fn
        return self

    def _evaluate_condition(self) -> None:
        """Evaluate the selector and update the rendered branch if needed."""
        try:
            value = self._condition_fn()
        except Exception:
            value = None

        if value == self._current_value and self._current_element is not None:
            return

        old_element = self._current_element
        self._current_value = value
        self._current_element = None

        for case_value, case_fn in self._cases:
            if case_value == value:
                self._current_element = case_fn()
                break

        if self._current_element is None and self._default_fn is not None:
            self._current_element = self._default_fn()

        # Emit mutation if we have a compiler and the branch changed
        if self._mutation_compiler is not None:
            from .types import UpdateCommand
            html = self._current_element.to_html() if self._current_element else ""
            cmd = UpdateCommand(
                node_id=self.node_id,
                update_type=UpdateType.REPLACE_INNER_HTML,
                html=html,
            )
            self._mutation_compiler.apply_single(cmd)

            if self._current_element and self._component:
                tracker = getattr(self._component, "_tracker", None)
                if tracker:
                    tracker.analyze_element(self._current_element)

    def _setup_reactive(self, mutation_compiler, component, event_router) -> None:
        self._mutation_compiler = mutation_compiler
        self._component = component
        self._event_router = event_router

    def to_html(self) -> str:
        self._evaluate_condition()
        parts = [f'<div data-pyrox-id="{self.node_id}">']
        if self._current_element is not None:
            parts.append(self._current_element.to_html())
        parts.append("</div>")
        return "".join(parts)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd pyrox_project && python -m pytest tests/test_conditionals.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pyrox/core/conditionals.py tests/test_conditionals.py
git commit -m "feat(pyrox): Show/Switch conditional elements"
```

---

### Task 7: DynamicChildrenManager

**Files:**
- Create: `pyrox/core/dynamic_children.py`
- Create: `tests/test_dynamic_children.py`

**Reference:** `src/pytonium_python_framework/Pytonium/components/dynamic_children.py` (205 lines)

- [ ] **Step 1: Write failing tests for DynamicChildrenManager**

```python
# tests/test_dynamic_children.py
"""Tests for DynamicChildrenManager (keyed list reconciliation)."""
import pytest
from pyrox.core.elements import Ul, Li, reset_id_counter
from pyrox.core.types import UpdateType
from pyrox.core.dynamic_children import DynamicChildrenManager
from pyrox.compiler.mutation_compiler import MutationCompiler


class MockCompiler:
    """Captures commands instead of sending them."""
    def __init__(self):
        self.applied: list = []

    def apply_batch(self, commands):
        self.applied.extend(commands)


class TestDynamicChildrenManager:
    def setup_method(self):
        reset_id_counter()

    def test_initialize_from_parent(self):
        items = [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}]
        parent = Ul().children_from(
            source=lambda: items,
            key=lambda x: x["id"],
            render_item=lambda x, i: Li().text(x["name"]),
        )
        parent.to_html()  # Generates _dynamic_initial_elements

        mgr = DynamicChildrenManager(
            parent_node_id=parent.node_id,
            source_fn=lambda: items,
            key_fn=lambda x: x["id"],
            render_item_fn=lambda x, i: Li().text(x["name"]),
            mutation_compiler=MockCompiler(),
            component=None,
        )
        mgr.initialize(parent_element=parent)
        assert mgr.current_keys == ["a", "b"]

    def test_add_item(self):
        items = [{"id": "a", "name": "A"}]
        compiler = MockCompiler()
        mgr = DynamicChildrenManager(
            parent_node_id="n0",
            source_fn=lambda: items,
            key_fn=lambda x: x["id"],
            render_item_fn=lambda x, i: Li().text(x["name"]),
            mutation_compiler=compiler,
            component=None,
        )
        mgr.initialize()
        items.append({"id": "b", "name": "B"})
        mgr.update()
        assert "b" in mgr.current_keys
        insert_cmds = [c for c in compiler.applied if c.update_type == UpdateType.INSERT_CHILD]
        assert len(insert_cmds) == 1

    def test_remove_item(self):
        items = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        compiler = MockCompiler()
        mgr = DynamicChildrenManager(
            parent_node_id="n0",
            source_fn=lambda: items,
            key_fn=lambda x: x["id"],
            render_item_fn=lambda x, i: Li().text(str(x["id"])),
            mutation_compiler=compiler,
            component=None,
        )
        mgr.initialize()
        items.pop(1)  # Remove "b"
        mgr.update()
        assert "b" not in mgr.current_keys
        remove_cmds = [c for c in compiler.applied if c.update_type == UpdateType.REMOVE_CHILD]
        assert len(remove_cmds) == 1

    def test_reorder_items(self):
        items = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        compiler = MockCompiler()
        mgr = DynamicChildrenManager(
            parent_node_id="n0",
            source_fn=lambda: items,
            key_fn=lambda x: x["id"],
            render_item_fn=lambda x, i: Li().text(str(x["id"])),
            mutation_compiler=compiler,
            component=None,
        )
        mgr.initialize()
        items.reverse()  # c, b, a
        mgr.update()
        assert mgr.current_keys == ["c", "b", "a"]

    def test_cleanup(self):
        items = [{"id": "a"}, {"id": "b"}]
        mgr = DynamicChildrenManager(
            parent_node_id="n0",
            source_fn=lambda: items,
            key_fn=lambda x: x["id"],
            render_item_fn=lambda x, i: Li().text(str(x["id"])),
            mutation_compiler=MockCompiler(),
            component=None,
        )
        mgr.initialize()
        mgr.cleanup()
        assert mgr.current_keys == []
        assert mgr.key_to_element == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd pyrox_project && python -m pytest tests/test_dynamic_children.py -v`
Expected: FAIL

- [ ] **Step 3: Implement DynamicChildrenManager**

```python
# pyrox/core/dynamic_children.py
"""Dynamic children management for reactive lists.

Handles the children_from() pattern — rendering a list of items from a
reactive source with keyed reconciliation. When the source list changes,
the manager detects additions, removals, and reorders, emitting minimal
DOM mutation commands.

Reference: Pytonium's dynamic_children.py (205 lines)
"""

from typing import Any, Callable, Optional

from .elements import Element
from .types import UpdateCommand, UpdateType


class DynamicChildrenManager:
    """Manages a dynamic list of child elements with keyed reconciliation."""

    def __init__(
        self,
        parent_node_id: str,
        source_fn: Callable,
        key_fn: Callable,
        render_item_fn: Callable,
        mutation_compiler: Any,
        component: Any,
        event_router: Any = None,
    ):
        self.parent_id = parent_node_id
        self.source = source_fn
        self.key = key_fn
        self.render_item = render_item_fn
        self.mutation_compiler = mutation_compiler
        self.component = component
        self.event_router = event_router

        self.current_keys: list[str] = []
        self.key_to_element: dict[str, Element] = {}

    def initialize(self, parent_element: Optional[Element] = None) -> None:
        """Initialize with the current source items.

        Reuses elements created during to_html() if available.
        """
        self.current_keys = []
        self.key_to_element = {}

        initial = getattr(parent_element, "_dynamic_initial_elements", None)
        if initial is not None:
            for item_key, element in initial:
                self.current_keys.append(item_key)
                self.key_to_element[item_key] = element
            parent_element._dynamic_initial_elements = None
            return

        # Fallback: render fresh
        try:
            items = self.source()
        except Exception:
            items = []

        for i, item in enumerate(items):
            item_key = str(self.key(item))
            element = self.render_item(item, i)
            self.current_keys.append(item_key)
            self.key_to_element[item_key] = element

    def update(self) -> None:
        """Reconcile the current DOM with the new source list."""
        try:
            new_items = self.source()
        except Exception:
            return

        new_keys = [str(self.key(item)) for item in new_items]
        old_set = set(self.current_keys)
        new_set = set(new_keys)

        commands: list[UpdateCommand] = []

        # 1. Remove items no longer present
        for key in self.current_keys:
            if key not in new_set:
                element = self.key_to_element.pop(key, None)
                if element:
                    commands.append(UpdateCommand(
                        node_id=self.parent_id,
                        update_type=UpdateType.REMOVE_CHILD,
                        value=element.node_id,
                    ))
                    # Clean up tracker bindings
                    if self.component:
                        tracker = getattr(self.component, "_tracker", None)
                        if tracker:
                            tracker.remove_bindings_for_node(element.node_id)

        # 2. Add new items at correct positions
        for i, (key, item) in enumerate(zip(new_keys, new_items)):
            if key not in old_set:
                element = self.render_item(item, i)
                # Analyze dependencies for new element
                if self.component:
                    tracker = getattr(self.component, "_tracker", None)
                    if tracker:
                        tracker.analyze_element(element)
                self.key_to_element[key] = element
                html = element.to_html()
                commands.append(UpdateCommand(
                    node_id=self.parent_id,
                    update_type=UpdateType.INSERT_CHILD,
                    value=key,
                    index=i,
                    html=html,
                ))

        # 3. Detect reordering
        surviving_old = [k for k in self.current_keys if k in new_set]
        surviving_new = [k for k in new_keys if k in old_set]

        if surviving_old != surviving_new and len(surviving_new) > 1:
            for i, key in enumerate(new_keys):
                if key in old_set and key in self.key_to_element:
                    element = self.key_to_element[key]
                    commands.append(UpdateCommand(
                        node_id=self.parent_id,
                        update_type=UpdateType.MOVE_CHILD,
                        value=element.node_id,
                        index=i,
                    ))

        self.current_keys = list(new_keys)

        if commands:
            self.mutation_compiler.apply_batch(commands)

    def cleanup(self) -> None:
        """Remove all tracked elements."""
        if self.component:
            tracker = getattr(self.component, "_tracker", None)
            if tracker:
                for element in self.key_to_element.values():
                    tracker.remove_bindings_for_node(element.node_id)
        self.current_keys.clear()
        self.key_to_element.clear()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd pyrox_project && python -m pytest tests/test_dynamic_children.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pyrox/core/dynamic_children.py tests/test_dynamic_children.py
git commit -m "feat(pyrox): DynamicChildrenManager for keyed list reconciliation"
```

---

### Task 8: EventDispatcher (async)

**Files:**
- Create: `pyrox/events/__init__.py`
- Create: `pyrox/events/dispatcher.py`
- Create: `tests/test_dispatcher.py`

**Reference:** `src/pytonium_python_framework/Pytonium/components/event_router.py` (468 lines)

Key difference: async handlers, no CEF bindings, no JS injection.

- [ ] **Step 1: Write failing tests for EventDispatcher**

```python
# tests/test_dispatcher.py
"""Tests for the async EventDispatcher."""
import asyncio
import pytest
from pyrox.events.dispatcher import EventDispatcher, EventData


class TestEventData:
    def test_from_dict(self):
        data = EventData.from_dict({
            "value": "hello",
            "key": "Enter",
            "shiftKey": True,
        })
        assert data.value == "hello"
        assert data.key == "Enter"
        assert data.shift_key is True

    def test_empty_dict(self):
        data = EventData.from_dict({})
        assert data.value == ""
        assert data.key == ""
        assert data.shift_key is False


class TestEventDispatcher:
    def test_register_handler(self):
        dispatcher = EventDispatcher()
        handler = lambda: None
        dispatcher.register("n1", "click", handler)
        assert dispatcher.has_handler("n1", "click")

    def test_no_handler(self):
        dispatcher = EventDispatcher()
        assert not dispatcher.has_handler("n1", "click")

    @pytest.mark.asyncio
    async def test_dispatch_async_handler(self):
        dispatcher = EventDispatcher()
        result = []

        async def handler(event):
            result.append(event.value)

        dispatcher.register("n1", "click", handler)
        await dispatcher.dispatch("n1", "click", {"value": "clicked"})
        assert result == ["clicked"]

    @pytest.mark.asyncio
    async def test_dispatch_sync_handler(self):
        """Sync handlers should be auto-wrapped."""
        dispatcher = EventDispatcher()
        result = []

        def handler(event):
            result.append("sync")

        dispatcher.register("n1", "click", handler)
        await dispatcher.dispatch("n1", "click", {})
        assert result == ["sync"]

    @pytest.mark.asyncio
    async def test_dispatch_handler_no_args(self):
        """Handlers with no parameters should work."""
        dispatcher = EventDispatcher()
        result = []

        async def handler():
            result.append("no-args")

        dispatcher.register("n1", "click", handler)
        await dispatcher.dispatch("n1", "click", {})
        assert result == ["no-args"]

    @pytest.mark.asyncio
    async def test_dispatch_unknown_node(self):
        """Dispatching to unknown node should not raise."""
        dispatcher = EventDispatcher()
        await dispatcher.dispatch("unknown", "click", {})

    def test_remove_handler(self):
        dispatcher = EventDispatcher()
        dispatcher.register("n1", "click", lambda: None)
        dispatcher.remove("n1", "click")
        assert not dispatcher.has_handler("n1", "click")

    def test_remove_all_for_node(self):
        dispatcher = EventDispatcher()
        dispatcher.register("n1", "click", lambda: None)
        dispatcher.register("n1", "input", lambda: None)
        dispatcher.remove_all("n1")
        assert not dispatcher.has_handler("n1", "click")
        assert not dispatcher.has_handler("n1", "input")

    def test_register_from_element(self):
        from pyrox.core.elements import Button, reset_id_counter
        reset_id_counter()
        handler = lambda: None
        btn = Button().on_click(handler)
        dispatcher = EventDispatcher()
        dispatcher.register_from_element(btn)
        assert dispatcher.has_handler(btn.node_id, "click")

    def test_cleanup(self):
        dispatcher = EventDispatcher()
        dispatcher.register("n1", "click", lambda: None)
        dispatcher.register("n2", "input", lambda: None)
        dispatcher.cleanup()
        assert not dispatcher.has_handler("n1", "click")
        assert not dispatcher.has_handler("n2", "input")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd pyrox_project && python -m pytest tests/test_dispatcher.py -v`
Expected: FAIL

- [ ] **Step 3: Implement EventDispatcher**

```python
# pyrox/events/__init__.py
"""Pyrox event handling."""

# pyrox/events/dispatcher.py
"""Async EventDispatcher — routes client events to Python handlers.

Unlike Pytonium's EventRouter which binds JS functions and injects
event listeners via execute_javascript(), Pyrox's EventDispatcher
receives events as JSON messages over WebSocket and dispatches them
to registered async handlers.

Supports:
- async def handlers (native)
- sync def handlers (auto-wrapped)
- Handlers with 0 args (no event data) or 1 arg (EventData)
"""

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class EventData:
    """Deserialized event data from client.

    Provides typed access to common event properties.
    """
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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventData":
        """Create EventData from a raw event dict."""
        return cls(
            type=data.get("type", ""),
            value=data.get("value", ""),
            key=data.get("key", ""),
            key_code=data.get("keyCode", 0),
            client_x=data.get("clientX", 0.0),
            client_y=data.get("clientY", 0.0),
            shift_key=data.get("shiftKey", False),
            ctrl_key=data.get("ctrlKey", False),
            alt_key=data.get("altKey", False),
            meta_key=data.get("metaKey", False),
            checked=data.get("checked", False),
        )


class EventDispatcher:
    """Routes incoming events to registered handlers.

    Handlers are indexed by (node_id, event_type) and called with
    an EventData instance (or no args if the handler doesn't accept any).
    """

    def __init__(self):
        self._handlers: dict[tuple[str, str], Callable] = {}

    def register(self, node_id: str, event_type: str, handler: Callable) -> None:
        """Register a handler for a (node_id, event_type) pair."""
        self._handlers[(node_id, event_type)] = handler

    def has_handler(self, node_id: str, event_type: str) -> bool:
        """Check if a handler is registered."""
        return (node_id, event_type) in self._handlers

    def remove(self, node_id: str, event_type: str) -> None:
        """Remove a specific handler."""
        self._handlers.pop((node_id, event_type), None)

    def remove_all(self, node_id: str) -> None:
        """Remove all handlers for a node."""
        keys = [k for k in self._handlers if k[0] == node_id]
        for k in keys:
            del self._handlers[k]

    def cleanup(self) -> None:
        """Remove all handlers."""
        self._handlers.clear()

    def register_from_element(self, element: Any) -> None:
        """Register all event handlers from an element.

        Args:
            element: An Element with _events dict.
        """
        for event_type, event_info in getattr(element, "_events", {}).items():
            handler = event_info.get("handler")
            if handler:
                self.register(element.node_id, event_type, handler)

    def register_tree(self, element: Any) -> None:
        """Recursively register event handlers from an element tree."""
        self.register_from_element(element)
        for child in getattr(element, "_children", []):
            self.register_tree(child)
        # Also register from active conditional branch
        current = getattr(element, "_current_element", None)
        if current is not None:
            self.register_tree(current)

    async def dispatch(self, node_id: str, event_type: str, data: dict) -> None:
        """Dispatch an event to its registered handler.

        Handles:
        - async handlers (called directly)
        - sync handlers (called directly — not threaded for simplicity)
        - 0-arg handlers (called without event data)
        - 1-arg handlers (called with EventData)

        Args:
            node_id: The node that emitted the event.
            event_type: The event type (e.g., "click", "input").
            data: Raw event data dict from the client.
        """
        handler = self._handlers.get((node_id, event_type))
        if handler is None:
            return

        event = EventData.from_dict(data)

        # Inspect handler to determine arg count
        try:
            sig = inspect.signature(handler)
            # Filter out 'self' parameter for bound methods
            params = [
                p for p in sig.parameters.values()
                if p.name != "self"
            ]
            takes_arg = len(params) > 0
        except (ValueError, TypeError):
            takes_arg = False

        # Call handler
        if asyncio.iscoroutinefunction(handler):
            if takes_arg:
                await handler(event)
            else:
                await handler()
        else:
            if takes_arg:
                handler(event)
            else:
                handler()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd pyrox_project && python -m pytest tests/test_dispatcher.py -v`
Expected: All 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pyrox/events/ tests/test_dispatcher.py
git commit -m "feat(pyrox): async EventDispatcher"
```

---

## Chunk 4: Component + Session + ASGI

### Task 9: Component Base Class

**Files:**
- Create: `pyrox/component.py`
- Create: `tests/test_component.py`

**Reference:** `src/pytonium_python_framework/Pytonium/components/component.py` (392 lines)

- [ ] **Step 1: Write failing tests for Component**

```python
# tests/test_component.py
"""Tests for the Component base class."""
import pytest
from pyrox.component import Component
from pyrox.core.state import State
from pyrox.core.elements import Div, H1, Button, Input, reset_id_counter


class Counter(Component):
    count = State(0)

    async def increment(self):
        self.count += 1

    def render(self):
        return (
            Div()
                .child(H1().text(lambda: f"Count: {self.count}"))
                .child(Button().text("+").on_click(self.increment))
        )


class TestComponent:
    def setup_method(self):
        reset_id_counter()

    def test_render_returns_element(self):
        comp = Counter()
        tree = comp.render()
        assert tree._tag == "div"

    def test_state_default(self):
        comp = Counter()
        assert comp.count == 0

    def test_state_set_and_get(self):
        comp = Counter()
        comp.count = 5
        assert comp.count == 5

    def test_init_with_kwargs(self):
        comp = Counter(count=10)
        assert comp.count == 10

    def test_mount_creates_tracker(self):
        comp = Counter()
        comp._prepare()
        assert comp._tracker is not None

    def test_mount_creates_compiler(self):
        comp = Counter()
        comp._prepare()
        assert comp._compiler is not None

    def test_mount_creates_dispatcher(self):
        comp = Counter()
        comp._prepare()
        assert comp._dispatcher is not None

    def test_mount_html(self):
        comp = Counter()
        comp._prepare()
        html = comp._render_html()
        assert "Count: 0" in html
        assert "<button" in html

    def test_state_change_produces_commands(self):
        comp = Counter()
        comp._prepare()
        comp._render_html()  # Sets up bindings
        comp.count = 42
        cmds = comp._tracker.pending_commands
        assert len(cmds) > 0
        # The text should reflect the new value
        assert any("42" in c.value for c in cmds)

    def test_flush_clears_pending(self):
        comp = Counter()
        comp._prepare()
        comp._render_html()
        comp.count = 1
        batch = comp._collect_batch()
        assert len(batch) > 0
        assert comp._tracker.pending_commands == []

    def test_render_not_implemented(self):
        comp = Component()
        with pytest.raises(NotImplementedError):
            comp.render()

    def test_lifecycle_hooks_exist(self):
        comp = Counter()
        assert hasattr(comp, "on_mount")
        assert hasattr(comp, "on_update")
        assert hasattr(comp, "on_unmount")
        assert hasattr(comp, "on_error")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd pyrox_project && python -m pytest tests/test_component.py -v`
Expected: FAIL

- [ ] **Step 3: Implement Component base class**

```python
# pyrox/component.py
"""Component base class for Pyrox reactive web components.

The Component class is the foundation of the reactive UI system.
Subclasses define State fields as class attributes and implement render()
to return an Element tree.

Unlike Pytonium's Component which directly calls execute_javascript(),
Pyrox's Component produces JSON mutation batches that are sent over
WebSocket by the Session layer.
"""

import asyncio
from typing import Any, Optional

from .core.elements import Element, reset_id_counter
from .core.state import State
from .core.tracker import DependencyTracker
from .core.types import UpdateCommand
from .compiler.mutation_compiler import MutationCompiler
from .events.dispatcher import EventDispatcher


class Component:
    """Base class for reactive Pyrox components.

    Subclasses define reactive state with State descriptors and implement
    render() to return an Element tree. State changes produce mutation
    batches sent to the client via WebSocket.

    Usage::

        class Counter(Component):
            count = State(0)

            async def increment(self):
                self.count += 1

            def render(self):
                return (
                    Div()
                        .child(H1().text(lambda: f"Count: {self.count}"))
                        .child(Button().text("+").on_click(self.increment))
                )
    """

    def __init__(self, **kwargs):
        self._tracker = DependencyTracker()
        self._compiler = MutationCompiler()
        self._dispatcher = EventDispatcher()
        self._element_tree: Optional[Element] = None
        self._session: Any = None
        self._batch: list[dict] = []
        self._mounted: bool = False
        self._component_index: int = 0

        # Set initial state values from kwargs
        for key, value in kwargs.items():
            cls = type(self)
            if hasattr(cls, key) and isinstance(getattr(cls, key), State):
                setattr(self, key, value)

    def render(self) -> Element:
        """Return the element tree for this component. Must be overridden."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement render()"
        )

    # --- Lifecycle hooks (async) ---

    async def on_mount(self):
        """Called after initial HTML is sent to client."""
        pass

    async def on_update(self, changed_fields: set[str]):
        """Called after state changes are flushed."""
        pass

    async def on_unmount(self):
        """Called when session expires or component is removed."""
        pass

    async def on_error(self, error: Exception, context: str):
        """Called when an event handler raises."""
        pass

    # --- Internal mount/render ---

    def _prepare(self) -> None:
        """Initialize tracker and dispatcher (called before render)."""
        self._tracker.register(self)

    def _render_html(self) -> str:
        """Render the component and set up bindings. Returns initial HTML."""
        self._element_tree = self.render()
        self._tracker.analyze_element(self._element_tree)
        self._init_dynamic_children(self._element_tree)
        self._init_conditionals(self._element_tree)
        self._dispatcher.register_tree(self._element_tree)
        return self._element_tree.to_html()

    def _on_state_change(self, field_name: str, old_value: Any, new_value: Any) -> None:
        """Called by State.__set__ when a field changes."""
        self._tracker.notify_change(field_name, old_value, new_value)

    def _auto_flush(self) -> None:
        """Auto-flush pending commands (called by session after event dispatch)."""
        # Collect commands from the tracker (standard bindings)
        commands = self._tracker.pending_commands
        if commands:
            batch = self._compiler.compile_batch(commands)
            self._batch.extend(batch)
            self._tracker.clear_pending()
        # Collect commands from the compiler's pending queue
        # (DynamicChildrenManager and Show/Switch queue directly to compiler)
        compiler_pending = self._compiler.collect_pending()
        if compiler_pending:
            self._batch.extend(compiler_pending)

    async def flush(self) -> None:
        """Explicitly send queued mutations. Use in background tasks."""
        self._auto_flush()
        if self._batch and self._session is not None:
            await self._session.send({"type": "mutations", "batch": self._batch})
            self._batch = []

    def _collect_batch(self) -> list[dict]:
        """Collect and return the current batch, clearing it."""
        self._auto_flush()
        batch = list(self._batch)
        self._batch.clear()
        return batch

    # --- Dynamic children + conditionals ---

    def _init_dynamic_children(self, element: Element) -> None:
        """Initialize DynamicChildrenManagers for children_from elements."""
        if hasattr(element, "_dynamic_children") and element._dynamic_children:
            from .core.dynamic_children import DynamicChildrenManager
            dyn = element._dynamic_children
            manager = DynamicChildrenManager(
                parent_node_id=element.node_id,
                source_fn=dyn["source"],
                key_fn=dyn["key"],
                render_item_fn=dyn["render_item"],
                mutation_compiler=self._compiler,
                component=self,
                event_router=self._dispatcher,
            )
            element._dynamic_manager = manager
            manager.initialize(parent_element=element)

        for child in getattr(element, "_children", []):
            self._init_dynamic_children(child)

    def _init_conditionals(self, element: Element) -> None:
        """Initialize conditional elements (Show/Switch)."""
        for child in getattr(element, "_children", []):
            if hasattr(child, "_setup_reactive") and callable(child._setup_reactive):
                child._setup_reactive(
                    mutation_compiler=self._compiler,
                    component=self,
                    event_router=self._dispatcher,
                )
            self._init_conditionals(child)

        current = getattr(element, "_current_element", None)
        if current is not None:
            if hasattr(current, "_setup_reactive") and callable(current._setup_reactive):
                current._setup_reactive(
                    mutation_compiler=self._compiler,
                    component=self,
                    event_router=self._dispatcher,
                )
            self._init_conditionals(current)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd pyrox_project && python -m pytest tests/test_component.py -v`
Expected: All 12 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pyrox/component.py tests/test_component.py
git commit -m "feat(pyrox): Component base class with lifecycle hooks"
```

---

### Task 10: Session + SessionManager + SessionStore

**Files:**
- Create: `pyrox/session/__init__.py`
- Create: `pyrox/session/session.py`
- Create: `pyrox/session/manager.py`
- Create: `pyrox/session/store.py`
- Create: `tests/test_session.py`
- Create: `tests/test_session_manager.py`

- [ ] **Step 1: Write failing tests for Session and SessionStore**

```python
# tests/test_session.py
"""Tests for Session and SessionStore."""
import asyncio
import time
import pytest
from pyrox.session.session import Session
from pyrox.session.store import InMemoryStore, SessionStore


class TestSession:
    def test_create_session(self):
        s = Session(session_id="abc123", component=None)
        assert s.id == "abc123"
        assert s.websocket is None
        assert s.component is None
        assert s.grace_until is None

    def test_session_lock(self):
        s = Session(session_id="abc123", component=None)
        assert isinstance(s._lock, asyncio.Lock)

    def test_is_expired_no_grace(self):
        s = Session(session_id="abc123", component=None)
        assert not s.is_expired()

    def test_is_expired_past_grace(self):
        s = Session(session_id="abc123", component=None)
        s.grace_until = time.monotonic() - 1.0  # Already expired
        assert s.is_expired()

    def test_is_expired_within_grace(self):
        s = Session(session_id="abc123", component=None)
        s.grace_until = time.monotonic() + 100.0
        assert not s.is_expired()


class TestInMemoryStore:
    @pytest.mark.asyncio
    async def test_set_and_get(self):
        store = InMemoryStore()
        s = Session(session_id="abc", component=None)
        await store.set("abc", s)
        got = await store.get("abc")
        assert got is s

    @pytest.mark.asyncio
    async def test_get_missing(self):
        store = InMemoryStore()
        assert await store.get("missing") is None

    @pytest.mark.asyncio
    async def test_delete(self):
        store = InMemoryStore()
        s = Session(session_id="abc", component=None)
        await store.set("abc", s)
        await store.delete("abc")
        assert await store.get("abc") is None

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        store = InMemoryStore()
        s1 = Session(session_id="alive", component=None)
        s2 = Session(session_id="dead", component=None)
        s2.grace_until = time.monotonic() - 1.0  # Expired
        await store.set("alive", s1)
        await store.set("dead", s2)
        await store.cleanup_expired()
        assert await store.get("alive") is not None
        assert await store.get("dead") is None
```

```python
# tests/test_session_manager.py
"""Tests for SessionManager."""
import pytest
from pyrox.session.manager import SessionManager
from pyrox.session.store import InMemoryStore
from pyrox.component import Component
from pyrox.core.state import State
from pyrox.core.elements import Div, H1


class SimpleComp(Component):
    msg = State("hello")
    def render(self):
        return Div().child(H1().text(lambda: self.msg))


class TestSessionManager:
    @pytest.mark.asyncio
    async def test_create_session(self):
        mgr = SessionManager(store=InMemoryStore())
        session = await mgr.create_session("/", SimpleComp)
        assert session.id is not None
        assert session.component is not None
        assert isinstance(session.component, SimpleComp)

    @pytest.mark.asyncio
    async def test_get_session(self):
        mgr = SessionManager(store=InMemoryStore())
        session = await mgr.create_session("/", SimpleComp)
        got = await mgr.get_session(session.id)
        assert got is session

    @pytest.mark.asyncio
    async def test_reconnect(self):
        mgr = SessionManager(store=InMemoryStore())
        session = await mgr.create_session("/", SimpleComp)
        sid = session.id
        await mgr.disconnect_session(sid, grace_period=30.0)
        assert session.grace_until is not None
        reconnected = await mgr.get_session(sid)
        assert reconnected is session

    @pytest.mark.asyncio
    async def test_destroy_session(self):
        mgr = SessionManager(store=InMemoryStore())
        session = await mgr.create_session("/", SimpleComp)
        sid = session.id
        await mgr.destroy_session(sid)
        assert await mgr.get_session(sid) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd pyrox_project && python -m pytest tests/test_session.py tests/test_session_manager.py -v`
Expected: FAIL

- [ ] **Step 3: Implement Session, InMemoryStore, SessionManager**

```python
# pyrox/session/__init__.py
"""Pyrox session management."""

# pyrox/session/session.py
"""Session object — represents one connected client."""

import asyncio
import time
from typing import Any, Optional


class Session:
    """A single client session.

    Each session holds a component instance, a WebSocket connection
    (or None during disconnection grace period), and a lock for
    serializing state mutations.
    """

    def __init__(self, session_id: str, component: Any):
        self.id = session_id
        self.component = component
        self.websocket: Any = None
        self.created_at: float = time.monotonic()
        self.last_active: float = time.monotonic()
        self.grace_until: Optional[float] = None
        self._lock = asyncio.Lock()
        self._mount_html: Optional[str] = None
        self._container: str = "#app"
        self._path: str = "/"

    def is_expired(self) -> bool:
        """Check if the session has exceeded its grace period."""
        if self.grace_until is None:
            return False
        return time.monotonic() > self.grace_until

    def lock(self) -> asyncio.Lock:
        """Return the session's serialization lock."""
        return self._lock

    async def send(self, msg: dict) -> None:
        """Send a message to the client over WebSocket.

        Silently drops messages if WebSocket is disconnected.
        The websocket is stored as the raw ASGI send callable.
        """
        if self.websocket is not None:
            from ..compiler.codec import encode_message
            try:
                await self.websocket({
                    "type": "websocket.send",
                    "text": encode_message(msg),
                })
            except Exception:
                pass  # Connection lost — will be handled by disconnect
```

```python
# pyrox/session/store.py
"""SessionStore protocol and InMemoryStore implementation."""

import time
from typing import Optional, Protocol

from .session import Session


class SessionStore(Protocol):
    """Protocol for session storage backends."""

    async def get(self, session_id: str) -> Optional[Session]: ...
    async def set(self, session_id: str, session: Session) -> None: ...
    async def delete(self, session_id: str) -> None: ...
    async def cleanup_expired(self) -> None: ...


class InMemoryStore:
    """Default session store. Dict-based, single process."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    async def get(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    async def set(self, session_id: str, session: Session) -> None:
        self._sessions[session_id] = session

    async def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def cleanup_expired(self) -> None:
        expired = [
            sid for sid, s in self._sessions.items()
            if s.is_expired()
        ]
        for sid in expired:
            del self._sessions[sid]
```

```python
# pyrox/session/manager.py
"""SessionManager — creates, tracks, and cleans up sessions."""

import secrets
import time
from typing import Any, Optional, Type

from .session import Session
from .store import InMemoryStore


class SessionManager:
    """Manages the lifecycle of client sessions.

    Creates sessions with unique IDs, handles disconnection grace
    periods, and cleans up expired sessions.
    """

    def __init__(
        self,
        store: Any = None,
        grace_period: float = 30.0,
    ):
        self._store = store or InMemoryStore()
        self._grace_period = grace_period
        self._routes: dict[str, Type] = {}  # path → Component class

    def register_route(self, path: str, component_cls: Type) -> None:
        """Register a component class for a URL path."""
        self._routes[path] = component_cls

    async def create_session(
        self,
        path: str,
        component_cls: Type,
        **kwargs,
    ) -> Session:
        """Create a new session with a fresh component instance.

        Args:
            path: The URL path that triggered this session.
            component_cls: The Component class to instantiate.
            **kwargs: Initial state values for the component.

        Returns:
            A new Session with a mounted component.
        """
        session_id = secrets.token_urlsafe(32)
        component = component_cls(**kwargs)
        session = Session(session_id=session_id, component=component)
        session._path = path

        # Prepare the component (init tracker, render, set up bindings)
        component._prepare()
        component._session = session
        html = component._render_html()
        session._mount_html = html

        await self._store.set(session_id, session)
        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID (if not expired)."""
        session = await self._store.get(session_id)
        if session is not None and session.is_expired():
            await self._store.delete(session_id)
            return None
        return session

    async def disconnect_session(
        self,
        session_id: str,
        grace_period: Optional[float] = None,
    ) -> None:
        """Mark a session as disconnected with a grace period."""
        session = await self._store.get(session_id)
        if session is not None:
            period = grace_period if grace_period is not None else self._grace_period
            session.grace_until = time.monotonic() + period
            session.websocket = None

    async def destroy_session(self, session_id: str) -> None:
        """Destroy a session and call on_unmount."""
        session = await self._store.get(session_id)
        if session is not None:
            if session.component and hasattr(session.component, "on_unmount"):
                try:
                    await session.component.on_unmount()
                except Exception:
                    pass
            await self._store.delete(session_id)

    async def cleanup_expired(self) -> None:
        """Clean up all expired sessions."""
        await self._store.cleanup_expired()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd pyrox_project && python -m pytest tests/test_session.py tests/test_session_manager.py -v`
Expected: All 12 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pyrox/session/ tests/test_session.py tests/test_session_manager.py
git commit -m "feat(pyrox): Session + SessionManager + InMemoryStore"
```

---

### Task 11: ASGI App + WebSocket Handler + Page Shell

**Files:**
- Create: `pyrox/asgi/__init__.py`
- Create: `pyrox/asgi/app.py`
- Create: `pyrox/asgi/websocket.py`
- Create: `pyrox/asgi/routes.py`
- Create: `pyrox/asgi/page_shell.py`
- Create: `tests/test_asgi_app.py`

- [ ] **Step 1: Write failing tests for ASGI app**

```python
# tests/test_asgi_app.py
"""Tests for the ASGI application layer."""
import pytest
from pyrox.asgi.app import PyroxApp
from pyrox.asgi.page_shell import generate_page_shell
from pyrox.component import Component
from pyrox.core.state import State
from pyrox.core.elements import Div, H1


class HelloComp(Component):
    msg = State("Hello Pyrox")
    def render(self):
        return Div().child(H1().text(lambda: self.msg))


class TestPageShell:
    def test_generate_default(self):
        html = generate_page_shell(title="Test", path="/test")
        assert "<title>Test</title>" in html
        assert "pyrox.js" in html
        assert 'id="app"' in html
        assert "/test" in html

    def test_generate_custom_container(self):
        html = generate_page_shell(title="X", path="/x", container="#main")
        assert "#main" in html


class TestPyroxApp:
    def test_mount_component(self):
        app = PyroxApp()
        app.mount_component("/counter", HelloComp)
        assert "/counter" in app._routes

    def test_asgi_app_returns_callable(self):
        app = PyroxApp()
        asgi = app.asgi_app()
        assert callable(asgi)

    def test_mount_component_with_title(self):
        app = PyroxApp()
        app.mount_component("/hello", HelloComp, title="Hello Page")
        assert app._routes["/hello"]["title"] == "Hello Page"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd pyrox_project && python -m pytest tests/test_asgi_app.py -v`
Expected: FAIL

- [ ] **Step 3: Implement ASGI layer**

```python
# pyrox/asgi/__init__.py
"""Pyrox ASGI integration."""

# pyrox/asgi/page_shell.py
"""Auto-generated HTML page template for Pyrox components."""


def generate_page_shell(
    title: str = "Pyrox App",
    path: str = "/",
    container: str = "#app",
) -> str:
    """Generate a minimal HTML page that bootstraps a Pyrox component.

    Args:
        title: Page title.
        path: Component route path (for WebSocket connection).
        container: CSS selector for the mount container.

    Returns:
        Complete HTML string.
    """
    container_id = container.lstrip("#")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body>
    <div id="{container_id}"></div>
    <script src="/_pyrox/pyrox.js"></script>
    <script>Pyrox.connect("{container}", {{path: "{path}"}});</script>
</body>
</html>"""
```

```python
# pyrox/asgi/routes.py
"""HTTP route handlers for Pyrox."""

import os
from typing import Any


async def handle_page_request(scope: dict, receive: Any, send: Any, html: str) -> None:
    """Serve an HTML page shell."""
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [
            [b"content-type", b"text/html; charset=utf-8"],
            [b"content-length", str(len(html.encode())).encode()],
        ],
    })
    await send({
        "type": "http.response.body",
        "body": html.encode(),
    })


async def handle_static_request(scope: dict, receive: Any, send: Any) -> None:
    """Serve the pyrox.js client library."""
    path = scope.get("path", "")

    if path == "/_pyrox/pyrox.js":
        js_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "client", "pyrox.js")
        try:
            with open(js_path, "r") as f:
                content = f.read()
            body = content.encode()
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    [b"content-type", b"application/javascript; charset=utf-8"],
                    [b"content-length", str(len(body)).encode()],
                    [b"cache-control", b"public, max-age=3600"],
                ],
            })
            await send({"type": "http.response.body", "body": body})
        except FileNotFoundError:
            await send_404(send)
    else:
        await send_404(send)


async def send_404(send: Any) -> None:
    """Send a 404 response."""
    body = b"Not Found"
    await send({
        "type": "http.response.start",
        "status": 404,
        "headers": [[b"content-type", b"text/plain"], [b"content-length", b"9"]],
    })
    await send({"type": "http.response.body", "body": body})
```

```python
# pyrox/asgi/websocket.py
"""WebSocket handler for Pyrox sessions."""

import asyncio
from typing import Any, Type

from ..compiler.codec import decode_message, encode_message
from ..events.dispatcher import EventData
from ..session.manager import SessionManager
from ..session.session import Session


async def handle_websocket(
    scope: dict,
    receive: Any,
    send: Any,
    session_manager: SessionManager,
    component_cls: Type,
    path: str,
) -> None:
    """Handle a WebSocket connection for a Pyrox component.

    Lifecycle:
    1. Accept WebSocket connection
    2. Create or reconnect session
    3. Send mount message with initial HTML
    4. Loop: receive events, dispatch to handlers, send mutation batches
    5. On disconnect: enter grace period
    """
    # Accept the WebSocket
    await send({"type": "websocket.accept"})

    session = None

    try:
        # Wait for first message (could be reconnect)
        msg = await receive()
        if msg["type"] == "websocket.disconnect":
            return

        first_data = msg.get("text", "")
        reconnect_id = None

        if first_data:
            try:
                parsed = decode_message(first_data)
                if parsed.get("type") == "reconnect":
                    reconnect_id = parsed.get("session_id")
            except ValueError:
                pass

        # Reconnect or create new session
        if reconnect_id:
            session = await session_manager.get_session(reconnect_id)

        if session is None:
            session = await session_manager.create_session(path, component_cls)

        # Bind WebSocket and clear grace period
        session.websocket = send
        session.grace_until = None

        # Send mount message
        mount_msg = {
            "type": "mount",
            "html": session._mount_html,
            "container": session._container,
            "session_id": session.id,
        }
        await send({
            "type": "websocket.send",
            "text": encode_message(mount_msg),
        })

        # Call on_mount
        if session.component:
            await session.component.on_mount()

        # Message loop
        while True:
            msg = await receive()
            if msg["type"] == "websocket.disconnect":
                break

            text = msg.get("text", "")
            if not text:
                continue

            try:
                parsed = decode_message(text)
            except ValueError:
                continue

            msg_type = parsed.get("type")

            if msg_type == "event":
                await _handle_event(session, parsed)
            elif msg_type == "input":
                await _handle_input(session, parsed)

    except Exception:
        pass
    finally:
        # Disconnect — enter grace period
        if session:
            await session_manager.disconnect_session(session.id)


async def _handle_event(session: Session, msg: dict) -> None:
    """Dispatch an event and send resulting mutations."""
    component = session.component
    if component is None:
        return

    node_id = msg.get("node_id", "")
    event_type = msg.get("event", "")
    event_data = msg.get("data", {})

    async with session.lock():
        try:
            await component._dispatcher.dispatch(node_id, event_type, event_data)
            # Auto-flush and send mutations
            batch = component._collect_batch()
            if batch:
                await session.send({"type": "mutations", "batch": batch})
        except Exception as e:
            # Discard batch on error
            component._batch.clear()
            component._tracker.clear_pending()
            try:
                await component.on_error(e, f"event:{event_type}@{node_id}")
                # Flush any mutations from on_error
                batch = component._collect_batch()
                if batch:
                    await session.send({"type": "mutations", "batch": batch})
            except Exception:
                pass
            # Send error message to client
            await session.send({
                "type": "error",
                "message": str(e),
            })


async def _handle_input(session: Session, msg: dict) -> None:
    """Handle debounced input value sync.

    Sets the bound State field normally (triggering reactivity for other
    bindings like Computed and text displays), but filters out the SET_VALUE
    mutation for the originating node_id to prevent echo back to client.
    """
    component = session.component
    if component is None:
        return

    node_id = msg.get("node_id", "")
    value = msg.get("value", "")

    async with session.lock():
        # Look up the input binding in the element tree
        element = _find_element_by_id(component._element_tree, node_id)
        if element and element._bind_value_fn:
            # Find which State field this lambda reads
            tracker = component._tracker
            deps = tracker.track_dependencies(element._bind_value_fn, component)
            if deps:
                field_name = next(iter(deps))
                # Set via normal State descriptor (triggers reactivity)
                setattr(component, field_name, value)

                # Collect batch and filter out the echo mutation
                batch = component._collect_batch()
                filtered = [
                    m for m in batch
                    if not (m.get("op") == "value" and m.get("id") == node_id)
                ]
                if filtered:
                    await session.send({"type": "mutations", "batch": filtered})


def _find_element_by_id(element: Any, node_id: str) -> Any:
    """Recursively find an element by its node_id."""
    if element is None:
        return None
    if getattr(element, "node_id", None) == node_id:
        return element
    for child in getattr(element, "_children", []):
        found = _find_element_by_id(child, node_id)
        if found:
            return found
    return None
```

```python
# pyrox/asgi/app.py
"""Pyrox ASGI application — the main entry point."""

from typing import Any, Optional, Type

from ..session.manager import SessionManager
from ..session.store import InMemoryStore
from .page_shell import generate_page_shell
from .routes import handle_page_request, handle_static_request
from .websocket import handle_websocket


class PyroxApp:
    """Main Pyrox application.

    Manages component routes and serves as an ASGI application.

    Usage::

        from pyrox import Pyrox
        app = Pyrox()
        app.mount_component("/counter", Counter)

        # Standalone
        import uvicorn
        uvicorn.run(app.asgi_app(), port=8000)

        # With FastAPI
        fastapi_app.mount("/_pyrox", app.asgi_app())
    """

    def __init__(
        self,
        grace_period: float = 30.0,
        store: Any = None,
    ):
        self._store = store or InMemoryStore()
        self._session_manager = SessionManager(
            store=self._store,
            grace_period=grace_period,
        )
        self._routes: dict[str, dict] = {}

    def mount_component(
        self,
        path: str,
        component_cls: Type,
        title: Optional[str] = None,
        template: Optional[str] = None,
        container: str = "#app",
    ) -> None:
        """Mount a component class at a URL path.

        Args:
            path: URL path (e.g., "/counter").
            component_cls: Component subclass to instantiate per session.
            title: Page title (defaults to component class name).
            template: Optional custom HTML template file path.
            container: CSS selector for mount container.
        """
        self._routes[path] = {
            "component_cls": component_cls,
            "title": title or component_cls.__name__,
            "template": template,
            "container": container,
        }

    def asgi_app(self) -> Any:
        """Return an ASGI application callable."""
        async def app(scope: dict, receive: Any, send: Any) -> None:
            if scope["type"] == "http":
                await self._handle_http(scope, receive, send)
            elif scope["type"] == "websocket":
                await self._handle_ws(scope, receive, send)

        return app

    async def _handle_http(self, scope: dict, receive: Any, send: Any) -> None:
        """Route HTTP requests."""
        path = scope.get("path", "")

        # Static files (pyrox.js)
        if path.startswith("/_pyrox/"):
            await handle_static_request(scope, receive, send)
            return

        # Component page
        route = self._routes.get(path)
        if route:
            if route["template"]:
                try:
                    with open(route["template"], "r") as f:
                        html = f.read()
                except FileNotFoundError:
                    html = generate_page_shell(
                        title=route["title"],
                        path=path,
                        container=route["container"],
                    )
            else:
                html = generate_page_shell(
                    title=route["title"],
                    path=path,
                    container=route["container"],
                )
            await handle_page_request(scope, receive, send, html)
            return

        # 404
        from .routes import send_404
        await send_404(send)

    async def _handle_ws(self, scope: dict, receive: Any, send: Any) -> None:
        """Route WebSocket connections."""
        # Extract path from query string
        qs = scope.get("query_string", b"").decode()
        path = "/"
        for part in qs.split("&"):
            if part.startswith("path="):
                path = part[5:]
                break

        route = self._routes.get(path)
        if route is None:
            # Reject unknown paths
            await send({"type": "websocket.close", "code": 4004})
            return

        await handle_websocket(
            scope, receive, send,
            session_manager=self._session_manager,
            component_cls=route["component_cls"],
            path=path,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd pyrox_project && python -m pytest tests/test_asgi_app.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pyrox/asgi/ tests/test_asgi_app.py
git commit -m "feat(pyrox): ASGI app + WebSocket handler + page shell"
```

---

## Chunk 5: Client JS + MockSession + Public API + Integration

### Task 12: pyrox.js Client Library

**Files:**
- Create: `pyrox/client/pyrox.js`

No automated tests (JS in browser) — tested via integration test in Task 15.

- [ ] **Step 1: Implement pyrox.js**

```javascript
// pyrox/client/pyrox.js
// Pyrox — Client-side WebSocket relay + DOM mutation applier
// ~3-5KB gzipped. No dependencies.

(function(global) {
  "use strict";

  var Pyrox = {
    connected: false,
    _ws: null,
    _container: null,
    _path: "/",
    _sessionId: null,
    _reconnectAttempts: 0,
    _maxReconnectDelay: 30000,
    _inputTimers: {},
    _inputDebounceMs: 80,
    _disabledButtons: new Set(),
    onError: null, // User-configurable error callback

    connect: function(containerSelector, opts) {
      opts = opts || {};
      this._container = document.querySelector(containerSelector);
      this._path = opts.path || "/";
      this._connectWs();
    },

    _connectWs: function() {
      var self = this;
      var protocol = location.protocol === "https:" ? "wss:" : "ws:";
      var url = protocol + "//" + location.host + "/_pyrox/ws?path=" + encodeURIComponent(this._path);

      var ws = new WebSocket(url);
      this._ws = ws;

      ws.onopen = function() {
        self.connected = true;
        self._reconnectAttempts = 0;
        document.dispatchEvent(new CustomEvent("pyrox:connect"));

        // Send reconnect if we have a session ID
        if (self._sessionId) {
          ws.send(JSON.stringify({type: "reconnect", session_id: self._sessionId}));
        } else {
          // Send empty message to trigger new session
          ws.send(JSON.stringify({type: "init"}));
        }
      };

      ws.onmessage = function(event) {
        var msg;
        try { msg = JSON.parse(event.data); } catch(e) { return; }
        self._handleMessage(msg);
      };

      ws.onclose = function() {
        self.connected = false;
        document.dispatchEvent(new CustomEvent("pyrox:disconnect"));
        self._scheduleReconnect();
      };

      ws.onerror = function() {
        // onclose will fire after this
      };
    },

    _scheduleReconnect: function() {
      var self = this;
      var delay = Math.min(1000 * Math.pow(2, this._reconnectAttempts), this._maxReconnectDelay);
      this._reconnectAttempts++;
      setTimeout(function() { self._connectWs(); }, delay);
    },

    _handleMessage: function(msg) {
      switch(msg.type) {
        case "mount":
          this._sessionId = msg.session_id;
          if (this._container) {
            this._container.innerHTML = msg.html;
          }
          this._attachEventDelegation();
          break;

        case "mutations":
          this._applyBatch(msg.batch);
          break;

        case "error":
          if (this.onError) {
            this.onError(msg.message);
          } else {
            console.warn("[Pyrox] Error:", msg.message);
          }
          break;
      }
    },

    _applyBatch: function(batch) {
      for (var i = 0; i < batch.length; i++) {
        this._applyMutation(batch[i]);
      }
      // Re-enable any buttons that were auto-disabled
      this._disabledButtons.forEach(function(id) {
        var el = document.querySelector('[data-pyrox-id="' + id + '"]');
        if (el) el.disabled = false;
      });
      this._disabledButtons.clear();
    },

    _applyMutation: function(m) {
      var el = document.querySelector('[data-pyrox-id="' + m.id + '"]');
      if (!el) return;

      switch(m.op) {
        case "text":
          el.textContent = m.value;
          break;
        case "attr":
          el.setAttribute(m.key, m.value);
          break;
        case "remove_attr":
          el.removeAttribute(m.key);
          break;
        case "class_add":
          el.classList.add(m.value);
          break;
        case "class_remove":
          el.classList.remove(m.value);
          break;
        case "class_toggle":
          el.classList.toggle(m.value);
          break;
        case "style":
          el.style[m.key] = m.value;
          break;
        case "value":
          el.value = m.value;
          break;
        case "inner_html":
          el.innerHTML = m.html;
          break;
        case "insert":
          var temp = document.createElement("div");
          temp.innerHTML = m.html;
          var newChild = temp.firstChild;
          if (newChild) {
            if (m.index >= 0 && m.index < el.children.length) {
              el.insertBefore(newChild, el.children[m.index]);
            } else {
              el.appendChild(newChild);
            }
          }
          break;
        case "remove":
          var child = document.querySelector('[data-pyrox-id="' + m.child + '"]');
          if (child && child.parentNode === el) {
            el.removeChild(child);
          }
          break;
        case "move":
          var moveChild = document.querySelector('[data-pyrox-id="' + m.child + '"]');
          if (moveChild) {
            if (m.index >= 0 && m.index < el.children.length) {
              el.insertBefore(moveChild, el.children[m.index]);
            } else {
              el.appendChild(moveChild);
            }
          }
          break;
      }
    },

    _attachEventDelegation: function() {
      var self = this;
      // Single event delegation on document
      if (this._delegationAttached) return;
      this._delegationAttached = true;

      var events = ["click", "dblclick", "submit", "change",
                    "keydown", "keyup", "mouseenter", "mouseleave",
                    "focus", "blur"];

      events.forEach(function(eventType) {
        document.addEventListener(eventType, function(e) {
          var target = e.target.closest("[data-pyrox-id]");
          if (!target) return;
          var nodeId = target.getAttribute("data-pyrox-id");

          // Auto-disable buttons on click
          if (eventType === "click" && target.tagName === "BUTTON") {
            target.disabled = true;
            self._disabledButtons.add(nodeId);
          }

          // Prevent form submission
          if (eventType === "submit") {
            e.preventDefault();
          }

          var data = {
            value: target.value || "",
            key: e.key || "",
            keyCode: e.keyCode || 0,
            clientX: e.clientX || 0,
            clientY: e.clientY || 0,
            shiftKey: !!e.shiftKey,
            ctrlKey: !!e.ctrlKey,
            altKey: !!e.altKey,
            metaKey: !!e.metaKey,
            checked: !!target.checked,
          };

          self._sendEvent(nodeId, eventType, data);
        }, eventType === "focus" || eventType === "blur" || eventType === "mouseenter" || eventType === "mouseleave");
      });

      // Input debouncing (separate from event delegation)
      document.addEventListener("input", function(e) {
        var target = e.target.closest("[data-pyrox-id]");
        if (!target) return;
        var nodeId = target.getAttribute("data-pyrox-id");

        // Clear existing timer
        if (self._inputTimers[nodeId]) {
          clearTimeout(self._inputTimers[nodeId]);
        }

        // Debounced input sync
        self._inputTimers[nodeId] = setTimeout(function() {
          self._sendInput(nodeId, target.value);
          delete self._inputTimers[nodeId];
        }, self._inputDebounceMs);
      });
    },

    _sendEvent: function(nodeId, eventType, data) {
      if (!this._ws || this._ws.readyState !== WebSocket.OPEN) return;
      this._ws.send(JSON.stringify({
        type: "event",
        node_id: nodeId,
        event: eventType,
        data: data,
      }));
    },

    _sendInput: function(nodeId, value) {
      if (!this._ws || this._ws.readyState !== WebSocket.OPEN) return;
      this._ws.send(JSON.stringify({
        type: "input",
        node_id: nodeId,
        value: value,
      }));
    },
  };

  global.Pyrox = Pyrox;
})(typeof window !== "undefined" ? window : this);
```

- [ ] **Step 2: Commit**

```bash
git add pyrox/client/pyrox.js
git commit -m "feat(pyrox): pyrox.js client library (WebSocket relay + DOM mutation applier)"
```

---

### Task 13: MockSession for Testing

**Files:**
- Create: `pyrox/testing/__init__.py`
- Create: `pyrox/testing/mock_session.py`
- Create: `tests/test_mock_session.py`

- [ ] **Step 1: Write failing tests for MockSession**

```python
# tests/test_mock_session.py
"""Tests for MockSession testing utility."""
import pytest
from pyrox.testing.mock_session import MockSession
from pyrox.component import Component
from pyrox.core.state import State
from pyrox.core.elements import Div, H1, Button, reset_id_counter


class Counter(Component):
    count = State(0)

    async def increment(self):
        self.count += 1

    def render(self):
        return (
            Div()
                .child(H1().text(lambda: f"Count: {self.count}"))
                .child(Button().text("+").on_click(self.increment))
        )


class TestMockSession:
    def setup_method(self):
        reset_id_counter()

    @pytest.mark.asyncio
    async def test_mount(self):
        session = MockSession()
        counter = Counter()
        await session.mount(counter)
        assert "Count: 0" in session.last_mount_html

    @pytest.mark.asyncio
    async def test_fire_event(self):
        session = MockSession()
        counter = Counter()
        await session.mount(counter)
        btn = counter._element_tree.find("button")
        await session.fire("click", node_id=btn.node_id)
        assert counter.count == 1

    @pytest.mark.asyncio
    async def test_last_mutations(self):
        session = MockSession()
        counter = Counter()
        await session.mount(counter)
        btn = counter._element_tree.find("button")
        await session.fire("click", node_id=btn.node_id)
        assert len(session.last_mutations) > 0
        assert any("1" in m.get("value", "") for m in session.last_mutations)

    @pytest.mark.asyncio
    async def test_messages(self):
        session = MockSession()
        counter = Counter()
        await session.mount(counter)
        # Mount message should be recorded
        assert len(session.messages) >= 1
        assert session.messages[0]["type"] == "mount"

    @pytest.mark.asyncio
    async def test_multiple_clicks(self):
        session = MockSession()
        counter = Counter()
        await session.mount(counter)
        btn = counter._element_tree.find("button")
        await session.fire("click", node_id=btn.node_id)
        await session.fire("click", node_id=btn.node_id)
        await session.fire("click", node_id=btn.node_id)
        assert counter.count == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd pyrox_project && python -m pytest tests/test_mock_session.py -v`
Expected: FAIL

- [ ] **Step 3: Implement MockSession**

```python
# pyrox/testing/__init__.py
"""Pyrox testing utilities."""
from .mock_session import MockSession

__all__ = ["MockSession"]

# pyrox/testing/mock_session.py
"""MockSession — test harness that replaces WebSocket with in-memory buffer.

Usage::

    from pyrox.testing import MockSession

    async def test_counter():
        session = MockSession()
        counter = Counter()
        await session.mount(counter)
        assert "Count: 0" in session.last_mount_html
        btn = counter._element_tree.find("button")
        await session.fire("click", node_id=btn.node_id)
        assert session.last_mutations[0]["value"] == "Count: 1"
"""

from typing import Any, Optional

from ..component import Component
from ..core.elements import reset_id_counter


class MockSession:
    """Test harness for Pyrox components.

    Replaces the WebSocket transport with an in-memory message buffer.
    Provides convenience methods for mounting components and simulating
    user interactions.
    """

    def __init__(self):
        self.messages: list[dict] = []
        self.last_mount_html: str = ""
        self.last_mutations: list[dict] = []
        self._component: Optional[Component] = None

    async def mount(self, component: Component) -> None:
        """Mount a component into the mock session.

        Prepares the component, renders it, and records the mount message.
        """
        reset_id_counter()
        self._component = component
        component._prepare()
        component._session = self  # MockSession acts as the session
        html = component._render_html()
        self.last_mount_html = html

        mount_msg = {
            "type": "mount",
            "html": html,
            "container": "#app",
        }
        self.messages.append(mount_msg)

        await component.on_mount()

    async def fire(self, event_type: str, node_id: str, data: dict = None) -> None:
        """Simulate a user event.

        Dispatches the event through the component's EventDispatcher,
        collects resulting mutations, and records them.

        Args:
            event_type: Event type (e.g., "click", "input").
            node_id: Target element's data-pyrox-id.
            data: Optional event data dict.
        """
        if self._component is None:
            raise RuntimeError("No component mounted")

        await self._component._dispatcher.dispatch(
            node_id, event_type, data or {}
        )

        batch = self._component._collect_batch()
        if batch:
            self.last_mutations = batch
            self.messages.append({"type": "mutations", "batch": batch})

    async def send(self, msg: dict) -> None:
        """Mock send — records the message instead of sending over WebSocket."""
        self.messages.append(msg)
        if msg.get("type") == "mutations":
            self.last_mutations = msg.get("batch", [])

    @property
    def in_grace_period(self) -> bool:
        """Always False for mock sessions."""
        return False

    def lock(self):
        """Return a no-op async context manager."""
        import asyncio
        return asyncio.Lock()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd pyrox_project && python -m pytest tests/test_mock_session.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add pyrox/testing/ tests/test_mock_session.py
git commit -m "feat(pyrox): MockSession testing utility"
```

---

### Task 14: Public API Exports + py.typed

**Files:**
- Modify: `pyrox/__init__.py`
- Create: `pyrox/py.typed`

- [ ] **Step 1: Write public API exports**

```python
# pyrox/__init__.py
"""Pyrox — Reactive Python web framework.

Server-side reactive components over WebSocket. No JavaScript framework,
no build step, no virtual DOM.

Usage::

    from pyrox import Pyrox, Component, State, Div, H1, Button

    class Counter(Component):
        count = State(0)

        async def increment(self):
            self.count += 1

        def render(self):
            return (
                Div()
                    .child(H1().text(lambda: f"Count: {self.count}"))
                    .child(Button().text("+").on_click(self.increment))
            )

    app = Pyrox()
    app.mount_component("/", Counter)
"""

__version__ = "0.1.0"

# Core
from .component import Component
from .core.state import State, Computed
from .core.tracker import DependencyTracker

# Elements
from .core.elements import (
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

# Conditionals
from .core.conditionals import Show, Switch

# Events
from .events.dispatcher import EventDispatcher, EventData

# App
from .asgi.app import PyroxApp as Pyrox

# Testing (not auto-imported — use `from pyrox.testing import MockSession`)

__all__ = [
    # Core
    "Component", "State", "Computed", "DependencyTracker",
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
    # Conditionals
    "Show", "Switch",
    # Events
    "EventDispatcher", "EventData",
    # App
    "Pyrox",
]
```

```
# pyrox/py.typed
# PEP 561 marker — this package supports type checking
```

- [ ] **Step 2: Verify imports work**

Run: `cd pyrox_project && python -c "from pyrox import Pyrox, Component, State, Div, H1, Button, Show, Switch; print('All imports OK')"`.
Expected: `All imports OK`

- [ ] **Step 3: Commit**

```bash
git add pyrox/__init__.py pyrox/py.typed
git commit -m "feat(pyrox): public API exports + py.typed marker"
```

---

### Task 15: Integration Test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# tests/test_integration.py
"""Integration test — full round-trip from Component to mutations."""
import pytest
from pyrox import Component, State, Div, H1, H2, Button, Input, Ul, Li, Show
from pyrox.testing import MockSession
from pyrox.core.elements import reset_id_counter


class TodoApp(Component):
    """Non-trivial component for integration testing."""
    items = State([])
    new_item = State("")
    show_completed = State(True)

    async def add_item(self):
        if self.new_item.strip():
            self.items = [*self.items, {"id": len(self.items), "text": self.new_item, "done": False}]
            self.new_item = ""

    async def toggle_item(self, event):
        idx = int(event.value)
        new_items = list(self.items)
        new_items[idx] = {**new_items[idx], "done": not new_items[idx]["done"]}
        self.items = new_items

    def render(self):
        return (
            Div()
                .child(H1().text("Todo App"))
                .child(
                    Input()
                        .bind_value(lambda: self.new_item)
                        .on_input(lambda e: setattr(self, "new_item", e.value))
                )
                .child(Button().text("Add").on_click(self.add_item))
                .child(
                    H2().text(lambda: f"Items: {len(self.items)}")
                )
                .child(
                    Ul().children_from(
                        source=lambda: self.items,
                        key=lambda item: item["id"],
                        render_item=lambda item, i: Li().text(item["text"]),
                    )
                )
                .child(
                    Show(
                        when=lambda: len(self.items) == 0,
                        then=lambda: Div().text("No items yet!"),
                    )
                )
        )


class TestIntegration:
    def setup_method(self):
        reset_id_counter()

    @pytest.mark.asyncio
    async def test_full_todo_workflow(self):
        session = MockSession()
        app = TodoApp()
        await session.mount(app)

        # Initial render
        assert "Todo App" in session.last_mount_html
        assert "No items yet!" in session.last_mount_html
        assert "Items: 0" in session.last_mount_html

        # Set new_item text
        app.new_item = "Buy milk"

        # Click Add
        add_btn = app._element_tree.find("button")
        await session.fire("click", node_id=add_btn.node_id)

        # Verify item was added
        assert len(app.items) == 1
        assert app.items[0]["text"] == "Buy milk"
        assert app.new_item == ""  # Should be cleared

        # Add another item
        app.new_item = "Walk dog"
        await session.fire("click", node_id=add_btn.node_id)
        assert len(app.items) == 2

    @pytest.mark.asyncio
    async def test_mutations_are_json_serializable(self):
        """All mutations must be JSON-serializable (no Python objects)."""
        import json
        session = MockSession()
        app = TodoApp()
        await session.mount(app)

        app.new_item = "Test item"
        add_btn = app._element_tree.find("button")
        await session.fire("click", node_id=add_btn.node_id)

        for msg in session.messages:
            # Should not raise
            json.dumps(msg)

    @pytest.mark.asyncio
    async def test_multiple_components(self):
        """Two independent components should not interfere."""
        s1 = MockSession()
        s2 = MockSession()

        class SimpleCounter(Component):
            count = State(0)
            async def inc(self):
                self.count += 1
            def render(self):
                return Div().child(
                    H1().text(lambda: f"Count: {self.count}"),
                    Button().text("+").on_click(self.inc),
                )

        reset_id_counter()
        c1 = SimpleCounter()
        await s1.mount(c1)

        reset_id_counter()
        c2 = SimpleCounter()
        await s2.mount(c2)

        btn1 = c1._element_tree.find("button")
        await s1.fire("click", node_id=btn1.node_id)
        await s1.fire("click", node_id=btn1.node_id)

        assert c1.count == 2
        assert c2.count == 0  # Independent
```

- [ ] **Step 2: Run all tests**

Run: `cd pyrox_project && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test(pyrox): integration tests for full component lifecycle"
```

---

### Task 16: Example App

**Files:**
- Create: `examples/counter.py`

A minimal working example to verify the end-to-end stack.

- [ ] **Step 1: Write example**

```python
# examples/counter.py
"""Minimal Pyrox example — a reactive counter served over HTTP.

Run:
    pip install uvicorn
    python examples/counter.py

Then open http://localhost:8000 in your browser.
"""

from pyrox import Pyrox, Component, State, Div, H1, Button


class Counter(Component):
    count = State(0)

    async def increment(self):
        self.count += 1

    async def decrement(self):
        self.count -= 1

    def render(self):
        return (
            Div()
                .child(H1().text(lambda: f"Count: {self.count}"))
                .child(
                    Div()
                        .child(Button().text("-").on_click(self.decrement))
                        .child(Button().text("+").on_click(self.increment))
                )
        )


if __name__ == "__main__":
    import uvicorn

    app = Pyrox()
    app.mount_component("/", Counter, title="Pyrox Counter")
    uvicorn.run(app.asgi_app(), host="0.0.0.0", port=8000)
```

- [ ] **Step 2: Verify syntax**

Run: `cd pyrox_project && python -c "import ast; ast.parse(open('examples/counter.py').read()); print('Syntax OK')"`
Expected: `Syntax OK`

- [ ] **Step 3: Commit**

```bash
git add examples/counter.py
git commit -m "feat(pyrox): minimal counter example app"
```
