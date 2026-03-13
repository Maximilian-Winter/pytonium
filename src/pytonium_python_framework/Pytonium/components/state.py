"""State descriptor and DependencyTracker for reactive components.

The State descriptor intercepts attribute access on Component classes to
enable automatic dependency tracking and change notification. The
DependencyTracker maintains the mapping from (component, field) pairs to
DOM node bindings, enabling surgical updates when state changes.
"""

import weakref
from typing import Any, Callable, Optional

from .types import Binding, UpdateCommand, UpdateType


class State:
    """Reactive state descriptor for Component classes.

    When used as a class attribute on a Component, State intercepts reads and
    writes to enable automatic dependency tracking. Reads during render() are
    captured by the DependencyTracker. Writes trigger notification of all
    dependent DOM bindings.

    Usage:
        class MyComponent(Component):
            count = State(0)
            name = State("world")
    """

    def __init__(self, default=None):
        """Initialize with a default value.

        Args:
            default: Default value for this state field. Should be immutable
                     or a fresh copy will NOT be made per instance — use
                     __init__ to set mutable defaults per-instance.
        """
        self.default = default
        self.name: str = ""
        self._private_name: str = ""

    def __set_name__(self, owner, name):
        """Called when the descriptor is assigned to a class attribute."""
        self.name = name
        self._private_name = f"_state_{name}"

    def __get__(self, obj, objtype=None):
        """Get the current value, recording access if tracking is active."""
        if obj is None:
            return self
        # Record access for dependency tracking during render/computed
        DependencyTracker.record_access(obj, self.name)
        return getattr(obj, self._private_name, self.default)

    def __set__(self, obj, value):
        """Set a new value, notifying the DependencyTracker if changed."""
        old_value = getattr(obj, self._private_name, self.default)
        setattr(obj, self._private_name, value)
        # Only notify if the value actually changed
        if old_value is not value and old_value != value:
            DependencyTracker.notify_change(obj, self.name, old_value, value)


class DependencyTracker:
    """Tracks dependencies between State fields and DOM node bindings.

    During render(), the tracker operates in recording mode: it captures
    which State fields are accessed by each reactive lambda. After render(),
    these captured dependencies form the dependency map used to emit minimal
    DOM update commands when state changes.

    The tracker uses weak references to component instances to allow garbage
    collection of unmounted components.

    Class-level (static) API — all methods are classmethods operating on
    shared class state. This is intentional: there is one global dependency
    graph per process.
    """

    # --- Class state ---
    _current_tracking: Optional[set] = None
    _tracking_stack: list = []

    # (component_id, field_name) → list[Binding]
    _dependency_map: dict[tuple[int, str], list[Binding]] = {}

    # component_id → weakref.ref(component)
    _component_refs: dict[int, weakref.ref] = {}

    # (component_id, field_name) → list of (component_id, computed_name)
    # Used for transitive invalidation of Computed properties
    _computed_deps: dict[tuple[int, str], list[tuple[int, str]]] = {}

    # component_id → MutationCompiler
    _component_compilers: dict[int, Any] = {}

    # component_id → Component (for on_update callback)
    _component_instances: dict[int, weakref.ref] = {}

    # Batch context for coalescing updates within a single event handler
    _batch_active: bool = False
    _batch_commands: list[UpdateCommand] = []
    _batch_compiler: Any = None
    _batch_changed_fields: set[str] = set()
    _batch_component_id: Optional[int] = None

    @classmethod
    def reset(cls):
        """Reset all tracking state. Used in tests and between mounts."""
        cls._current_tracking = None
        cls._tracking_stack = []
        cls._dependency_map = {}
        cls._component_refs = {}
        cls._computed_deps = {}
        cls._component_compilers = {}
        cls._component_instances = {}
        cls._batch_active = False
        cls._batch_commands = []
        cls._batch_compiler = None
        cls._batch_changed_fields = set()
        cls._batch_component_id = None

    @classmethod
    def record_access(cls, component, field_name: str):
        """Record a State field access during dependency tracking.

        Called by State.__get__(). If tracking is active (during render or
        Computed evaluation), adds (component, field_name) to the current
        tracking set.
        """
        if cls._current_tracking is not None:
            cls._current_tracking.add((id(component), field_name))

    @classmethod
    def track(cls, callback: Callable) -> tuple[Any, set]:
        """Execute callback while recording which State fields are accessed.

        Supports nesting: if track() is called while already tracking (e.g.,
        a Computed accessing another Computed), the inner tracking set is
        independent.

        Args:
            callback: Zero-argument callable to execute.

        Returns:
            Tuple of (callback result, set of (component_id, field_name) pairs).
        """
        # Push current tracking context
        cls._tracking_stack.append(cls._current_tracking)
        deps: set[tuple[int, str]] = set()
        cls._current_tracking = deps
        try:
            result = callback()
        finally:
            cls._current_tracking = cls._tracking_stack.pop()
        return result, deps

    @classmethod
    def _cleanup_component(cls, comp_id: int):
        """Auto-cleanup when a component is garbage collected without unmount.

        Called via weakref.finalize — removes all stale bindings, computed
        deps, and refs for the given component id, preventing id() reuse
        from triggering stale bindings on a new object at the same address.
        """
        keys_to_remove = [k for k in cls._dependency_map if k[0] == comp_id]
        for key in keys_to_remove:
            del cls._dependency_map[key]
        computed_keys = [k for k in cls._computed_deps if k[0] == comp_id]
        for key in computed_keys:
            del cls._computed_deps[key]
        cls._component_refs.pop(comp_id, None)
        cls._component_compilers.pop(comp_id, None)
        cls._component_instances.pop(comp_id, None)

    @classmethod
    def register_component(cls, component):
        """Register a component for dependency tracking.

        Must be called before analyze(). Stores a weak reference to the
        component and its MutationCompiler. Also installs a weak-reference
        finalizer to auto-clean the dependency map if the component is
        garbage collected without unmount() being called.

        Args:
            component: Component instance to register.
        """
        comp_id = id(component)
        cls._component_refs[comp_id] = weakref.ref(component)
        cls._component_instances[comp_id] = weakref.ref(component)
        if hasattr(component, "_mutation_compiler") and component._mutation_compiler:
            cls._component_compilers[comp_id] = component._mutation_compiler
        # Install GC finalizer to prevent stale bindings on id() reuse
        weakref.finalize(component, cls._cleanup_component, comp_id)

    @classmethod
    def unregister_component(cls, component):
        """Remove all dependency mappings for a component.

        Called during unmount to clean up the dependency graph.

        Args:
            component: Component instance to unregister.
        """
        comp_id = id(component)
        # Remove all bindings for this component
        keys_to_remove = [
            key for key in cls._dependency_map if key[0] == comp_id
        ]
        for key in keys_to_remove:
            del cls._dependency_map[key]
        # Remove computed deps
        computed_keys_to_remove = [
            key for key in cls._computed_deps if key[0] == comp_id
        ]
        for key in computed_keys_to_remove:
            del cls._computed_deps[key]
        # Remove refs
        cls._component_refs.pop(comp_id, None)
        cls._component_compilers.pop(comp_id, None)
        cls._component_instances.pop(comp_id, None)

    @classmethod
    def add_binding(cls, component_id: int, field_name: str, binding: Binding):
        """Add a reactive binding for a specific state field.

        Args:
            component_id: id() of the component instance.
            field_name: Name of the State field.
            binding: Binding object describing the DOM update.
        """
        key = (component_id, field_name)
        if key not in cls._dependency_map:
            cls._dependency_map[key] = []
        cls._dependency_map[key].append(binding)

    @classmethod
    def analyze(cls, component, element):
        """Analyze an element tree to discover and register all dependencies.

        Walks the element tree recursively. For each element with reactive
        bindings (lambdas), executes the lambda in tracking mode to discover
        which State fields it reads, then registers the binding in the
        dependency map.

        Args:
            component: The owning Component instance.
            element: Root Element of the tree to analyze.
        """
        comp_id = id(component)
        cls._analyze_element(comp_id, element)

    @classmethod
    def _analyze_element(cls, comp_id: int, element):
        """Recursively analyze a single element and its children."""
        # Analyze reactive bindings on this element
        for raw_binding in getattr(element, "_bindings", []):
            binding_type = raw_binding.get("type")
            transform = raw_binding.get("transform")
            if transform is None or not callable(transform):
                continue

            # Execute the transform in tracking mode to find dependencies
            _value, deps = cls.track(transform)

            # Create a Binding for each discovered dependency
            for dep_comp_id, dep_field in deps:
                update_type = _binding_type_to_update_type(binding_type)
                binding = Binding(
                    node_id=element.node_id,
                    update_type=update_type,
                    key=raw_binding.get("key", ""),
                    transform=transform,
                )
                cls.add_binding(dep_comp_id, dep_field, binding)

        # Analyze dynamic children (children_from) — handled by DynamicChildrenManager
        if hasattr(element, "_dynamic_children") and element._dynamic_children:
            dyn = element._dynamic_children
            source = dyn.get("source")
            if source and callable(source):
                _value, deps = cls.track(source)
                for dep_comp_id, dep_field in deps:
                    binding = Binding(
                        node_id=element.node_id,
                        update_type=UpdateType.REPLACE_INNER_HTML,
                        key="_dynamic_children",
                        transform=None,  # Handled by DynamicChildrenManager
                        _dynamic_manager_element=element,
                    )
                    cls.add_binding(dep_comp_id, dep_field, binding)

        # Analyze conditional elements (Show/Switch)
        if hasattr(element, "_condition_binding") and element._condition_binding:
            cond = element._condition_binding
            when_fn = cond.get("when")
            if when_fn and callable(when_fn):
                _value, deps = cls.track(when_fn)
                for dep_comp_id, dep_field in deps:
                    binding = Binding(
                        node_id=element.node_id,
                        update_type=UpdateType.REPLACE_INNER_HTML,
                        key="_conditional",
                        transform=None,
                        _conditional_element=element,
                    )
                    cls.add_binding(dep_comp_id, dep_field, binding)

        # Recurse into children
        for child in getattr(element, "_children", []):
            cls._analyze_element(comp_id, child)

        # Recurse into conditional elements' active branch (Show/Switch)
        current = getattr(element, "_current_element", None)
        if current is not None:
            cls._analyze_element(comp_id, current)

    @classmethod
    def remove_element_bindings(cls, element):
        """Remove all bindings referencing a specific element's node_id.

        Used when elements are removed from the DOM (e.g., dynamic list
        reconciliation, conditional unmount).

        Args:
            element: Element whose bindings should be removed.
        """
        node_id = element.node_id
        for key in list(cls._dependency_map.keys()):
            cls._dependency_map[key] = [
                b for b in cls._dependency_map[key] if b.node_id != node_id
            ]
            if not cls._dependency_map[key]:
                del cls._dependency_map[key]
        # Recurse into children
        for child in getattr(element, "_children", []):
            cls.remove_element_bindings(child)

    @classmethod
    def notify_change(cls, component, field_name: str, old_value, new_value):
        """Process a state change and emit DOM update commands.

        Called by State.__set__() when a value changes. Looks up all bindings
        for (component, field_name), re-evaluates each transform lambda, and
        sends the resulting UpdateCommands to the MutationCompiler.

        If batch mode is active (inside an event handler), commands are
        accumulated instead of sent immediately.

        Args:
            component: The Component instance whose state changed.
            field_name: Name of the State field that changed.
            old_value: Previous value.
            new_value: New value.
        """
        comp_id = id(component)
        comp_ref = cls._component_refs.get(comp_id)
        if comp_ref is None or comp_ref() is None:
            return

        key = (comp_id, field_name)
        bindings = cls._dependency_map.get(key, [])

        commands: list[UpdateCommand] = []
        for binding in bindings:
            # Handle special binding types (dynamic children, conditionals)
            if binding.key == "_dynamic_children":
                manager = getattr(
                    binding._dynamic_manager_element, "_dynamic_manager", None
                )
                if manager:
                    manager.update()
                continue

            if binding.key == "_conditional":
                cond_element = getattr(binding, "_conditional_element", None)
                if cond_element and hasattr(cond_element, "_evaluate_condition"):
                    cond_element._evaluate_condition()
                continue

            # Standard binding: re-evaluate transform and emit command
            if binding.transform is None:
                continue
            try:
                new_val = binding.transform()
            except Exception as e:
                import traceback
                print(
                    f"[Pytonium] Error evaluating binding for "
                    f"{field_name} on node {binding.node_id}: {e}"
                )
                traceback.print_exc()
                continue

            val_str = _serialize_value(new_val)

            if binding.update_type == UpdateType.TOGGLE_CLASS:
                # For class toggle, value is "true" or "false"
                commands.append(UpdateCommand(
                    node_id=binding.node_id,
                    update_type=UpdateType.TOGGLE_CLASS,
                    key=binding.key,
                    value=val_str,
                ))
            else:
                commands.append(UpdateCommand(
                    node_id=binding.node_id,
                    update_type=binding.update_type,
                    key=binding.key,
                    value=val_str,
                ))

        # Invalidate affected Computed properties
        computed_deps = cls._computed_deps.get(key, [])
        for computed_comp_id, computed_name in computed_deps:
            computed_ref = cls._component_refs.get(computed_comp_id)
            if computed_ref and computed_ref():
                computed_comp = computed_ref()
                # Mark computed as dirty
                setattr(computed_comp, f"_computed_dirty_{computed_name}", True)
                # Trigger re-evaluation of bindings that depend on this computed
                cls.notify_change(computed_comp, computed_name, None, None)

        if not commands:
            return

        # Batch mode: accumulate commands
        if cls._batch_active:
            cls._batch_commands.extend(commands)
            cls._batch_changed_fields.add(field_name)
            return

        # Immediate mode: send commands now
        compiler = cls._component_compilers.get(comp_id)
        if compiler:
            compiler.apply_batch(commands)

        # Call on_update lifecycle hook
        comp_instance = cls._component_instances.get(comp_id)
        if comp_instance and comp_instance():
            instance = comp_instance()
            if hasattr(instance, "on_update") and instance._mounted:
                try:
                    instance.on_update({field_name})
                except Exception:
                    import traceback
                    traceback.print_exc()

    @classmethod
    def register_computed_deps(
        cls, component, computed_name: str, deps: set[tuple[int, str]]
    ):
        """Register which State fields a Computed property depends on.

        When any of these State fields change, the Computed is invalidated.

        Args:
            component: The Component instance.
            computed_name: Name of the Computed property.
            deps: Set of (component_id, field_name) pairs.
        """
        comp_id = id(component)
        for dep_comp_id, dep_field in deps:
            key = (dep_comp_id, dep_field)
            if key not in cls._computed_deps:
                cls._computed_deps[key] = []
            entry = (comp_id, computed_name)
            if entry not in cls._computed_deps[key]:
                cls._computed_deps[key].append(entry)

    @classmethod
    def begin_batch(cls, component):
        """Begin batching update commands.

        All state changes until flush_batch() will accumulate commands
        instead of sending them immediately. Used by EventRouter to coalesce
        updates from a single event handler.

        Args:
            component: The Component whose updates to batch.
        """
        cls._batch_active = True
        cls._batch_commands = []
        cls._batch_changed_fields = set()
        cls._batch_component_id = id(component)
        cls._batch_compiler = cls._component_compilers.get(id(component))

    @classmethod
    def flush_batch(cls, component):
        """Flush accumulated batch commands as a single update.

        Sends all accumulated commands to the MutationCompiler in one batch
        and calls the on_update lifecycle hook with all changed field names.

        Args:
            component: The Component whose batch to flush.
        """
        commands = cls._batch_commands
        changed_fields = cls._batch_changed_fields
        compiler = cls._batch_compiler

        cls._batch_active = False
        cls._batch_commands = []
        cls._batch_changed_fields = set()
        cls._batch_compiler = None
        cls._batch_component_id = None

        if commands and compiler:
            compiler.apply_batch(commands)

        # Call on_update with all changed fields
        if changed_fields and hasattr(component, "on_update") and component._mounted:
            try:
                component.on_update(changed_fields)
            except Exception:
                import traceback
                traceback.print_exc()


def _binding_type_to_update_type(binding_type: str) -> UpdateType:
    """Map internal binding type strings to UpdateType enum values."""
    mapping = {
        "text_content": UpdateType.SET_TEXT_CONTENT,
        "attribute": UpdateType.SET_ATTRIBUTE,
        "class_toggle": UpdateType.TOGGLE_CLASS,
        "style": UpdateType.SET_STYLE,
        "value": UpdateType.SET_VALUE,
    }
    return mapping.get(binding_type, UpdateType.SET_TEXT_CONTENT)


def _serialize_value(value) -> str:
    """Convert a Python value to its string representation for JS.

    Booleans become "true"/"false", None becomes "", everything else
    uses str().
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)
