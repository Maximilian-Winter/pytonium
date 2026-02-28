"""Computed properties for reactive components.

Computed properties are derived values that automatically cache their result
and recompute only when their State dependencies change. They participate
in the dependency tracking system, so DOM nodes bound to a Computed property
update transitively when upstream State fields change.

Usage:
    class MyComponent(Component):
        items = State([])
        filter = State("all")

        @Computed
        def visible_items(self):
            if self.filter == "all":
                return self.items
            return [i for i in self.items if i["status"] == self.filter]

        def render(self):
            return Ul().children_from(
                lambda: self.visible_items,
                key=lambda i: i["id"],
                render_item=lambda item, idx: Li().text(item["name"]),
            )
"""

from typing import Any, Callable

from .state import DependencyTracker


class Computed:
    """Descriptor for cached, auto-updating derived properties.

    When used as a decorator on a Component method, Computed:
    1. Tracks which State fields the method accesses during evaluation
    2. Caches the result until a dependency changes
    3. Records its own access in the DependencyTracker (so DOM bindings
       that read a Computed trigger updates when it changes)
    4. Invalidates when any upstream State field changes

    The invalidation chain: State changes → Computed invalidated → DOM nodes
    bound to Computed are updated (by re-evaluating the Computed on next
    access, which produces a new value, which becomes the DOM update).

    Usage:
        @Computed
        def total(self):
            return sum(item["price"] for item in self.items)
    """

    def __init__(self, func: Callable):
        """Initialize with the method to be computed.

        Args:
            func: The method to cache and auto-update. Should be a method
                  on a Component subclass (receives self as first argument).
        """
        self._func = func
        self._name: str = func.__name__
        self._private_name: str = ""

    def __set_name__(self, owner, name: str):
        """Called when the descriptor is assigned to a class attribute.

        Sets up the private storage names for the cached value and dirty flag.

        Args:
            owner: The class that owns this descriptor.
            name: The attribute name this descriptor is assigned to.
        """
        self._name = name
        self._private_name = f"_computed_{name}"

    def __get__(self, obj, objtype=None):
        """Get the computed value, recomputing if dirty.

        On access:
        1. Records this Computed as a dependency (for outer tracking contexts)
        2. Returns cached value if not dirty
        3. If dirty, recomputes: evaluates the function in tracking mode to
           discover dependencies, caches the result, registers deps

        Args:
            obj: Component instance. None if accessed on the class.
            objtype: The class.

        Returns:
            The computed value if accessed on an instance, the descriptor
            itself if accessed on the class.
        """
        if obj is None:
            return self

        # Record access for outer tracking (e.g., another Computed or a
        # DOM binding that reads this Computed)
        DependencyTracker.record_access(obj, self._name)

        dirty_attr = f"_computed_dirty_{self._name}"

        # Return cached value if not dirty
        if not getattr(obj, dirty_attr, True):
            return getattr(obj, self._private_name, None)

        # Recompute: track which State fields are accessed
        value, deps = DependencyTracker.track(lambda: self._func(obj))

        # Cache the result
        setattr(obj, self._private_name, value)
        setattr(obj, dirty_attr, False)

        # Register dependencies: when any dep changes, invalidate this Computed
        DependencyTracker.register_computed_deps(obj, self._name, deps)

        return value

    def invalidate(self, obj):
        """Mark this Computed as dirty, forcing recomputation on next access.

        Called by the DependencyTracker when an upstream State field changes.

        Args:
            obj: The Component instance whose Computed value is invalidated.
        """
        setattr(obj, f"_computed_dirty_{self._name}", True)
