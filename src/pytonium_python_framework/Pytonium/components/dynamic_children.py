"""Dynamic children management for reactive lists.

Handles the children_from() pattern — rendering a list of items from a
reactive source with keyed reconciliation. When the source list changes,
the manager detects additions, removals, and reorders, emitting minimal
DOM mutation commands.

Each item is identified by a stable key (extracted by the key function).
Items with the same key are assumed to represent the same logical item
and are reused rather than re-created.
"""

from typing import Any, Callable, Optional

from .elements import Element, reset_id_counter
from .mutation_compiler import MutationCompiler
from .state import DependencyTracker
from .types import UpdateCommand, UpdateType


class DynamicChildrenManager:
    """Manages a dynamic list of child elements with keyed reconciliation.

    Created during component mount for each Element with children_from()
    configuration. Tracks the current list of keys and their corresponding
    elements, and efficiently updates the DOM when the source list changes.

    Attributes:
        parent_id: The parent element's data-pyt-id.
        source: Lambda returning the current list of items.
        key: Function extracting a stable identity from each item.
        render_item: Function(item, index) → Element for each item.
    """

    def __init__(
        self,
        parent_node_id: str,
        source_fn: Callable,
        key_fn: Callable,
        render_item_fn: Callable,
        mutation_compiler: MutationCompiler,
        component: Any,
        event_router: Any = None,
    ):
        """Initialize the dynamic children manager.

        Args:
            parent_node_id: The parent element's data-pyt-id.
            source_fn: Lambda returning the current list of items.
            key_fn: Function extracting a stable key from each item.
            render_item_fn: Function(item, index) → Element for each item.
            mutation_compiler: MutationCompiler for sending DOM updates.
            component: The owning Component instance.
            event_router: EventRouter for registering events on new elements.
        """
        self.parent_id = parent_node_id
        self.source = source_fn
        self.key = key_fn
        self.render_item = render_item_fn
        self.mutation_compiler = mutation_compiler
        self.component = component
        self.event_router = event_router

        self.current_keys: list[str] = []
        self.key_to_element: dict[str, Element] = {}

    def initialize(self):
        """Initialize with the current source items.

        Called during component mount after the initial HTML is generated.
        Records the initial keys and elements without emitting DOM commands
        (since the initial HTML already contains these items).
        """
        try:
            items = self.source()
        except Exception:
            items = []

        self.current_keys = []
        self.key_to_element = {}

        for i, item in enumerate(items):
            item_key = str(self.key(item))
            # Re-render to get the Element (with its node_id)
            element = self.render_item(item, i)
            self.current_keys.append(item_key)
            self.key_to_element[item_key] = element

    def update(self):
        """Reconcile the current DOM with the new source list.

        Detects additions, removals, and reorders by comparing the new list
        of keys against the current keys. Emits minimal DOM mutation commands.

        Algorithm:
        1. Compute new keys from source
        2. Remove items no longer present
        3. Add new items
        4. Reorder surviving items if needed
        """
        try:
            new_items = self.source()
        except Exception as e:
            import traceback
            print(f"[Pytonium] Error evaluating dynamic children source: {e}")
            traceback.print_exc()
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
                    # Remove DOM node
                    commands.append(UpdateCommand(
                        node_id=self.parent_id,
                        update_type=UpdateType.REMOVE_CHILD,
                        value=element.node_id,
                    ))
                    # Clean up dependency tracking and event handlers
                    DependencyTracker.remove_element_bindings(element)
                    if self.event_router:
                        self.event_router.remove_element_handlers(element)

        # 2. Add new items at their correct positions
        for i, (key, item) in enumerate(zip(new_keys, new_items)):
            if key not in old_set:
                element = self.render_item(item, i)
                # Analyze dependencies for the new element
                DependencyTracker.analyze(self.component, element)
                self.key_to_element[key] = element
                # Generate HTML and insert
                html = element.to_html()
                commands.append(UpdateCommand(
                    node_id=self.parent_id,
                    update_type=UpdateType.INSERT_CHILD,
                    value=key,
                    index=i,
                    html=html,
                ))

        # 3. Detect if reordering is needed
        surviving_old = [k for k in self.current_keys if k in new_set]
        surviving_new = [k for k in new_keys if k in old_set]

        if surviving_old != surviving_new and len(surviving_new) > 1:
            # Reorder needed: emit move commands
            # Strategy: move each out-of-order element to its correct position
            for i, key in enumerate(new_keys):
                if key in old_set and key in self.key_to_element:
                    element = self.key_to_element[key]
                    commands.append(UpdateCommand(
                        node_id=self.parent_id,
                        update_type=UpdateType.MOVE_CHILD,
                        value=element.node_id,
                        index=i,
                    ))

        # Update tracking state
        self.current_keys = list(new_keys)

        # Send batch update
        if commands:
            self.mutation_compiler.apply_batch(commands)

        # Register event listeners for newly added elements
        if self.event_router:
            for key in new_keys:
                if key not in old_set and key in self.key_to_element:
                    self.event_router._register_element_events(
                        self.key_to_element[key]
                    )

    def cleanup(self):
        """Remove all tracked elements and clean up resources."""
        for key, element in self.key_to_element.items():
            DependencyTracker.remove_element_bindings(element)
            if self.event_router:
                self.event_router.remove_element_handlers(element)
        self.current_keys.clear()
        self.key_to_element.clear()
