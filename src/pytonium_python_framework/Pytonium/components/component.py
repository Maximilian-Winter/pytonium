"""Component base class for Pytonium reactive components.

The Component class is the foundation of the reactive UI system. Subclasses
define State fields as class attributes and implement render() to return an
Element tree. The mount() method initializes the component: it calls render(),
analyzes dependencies, generates HTML, injects it into the browser DOM, and
registers event listeners.

After mounting, state changes trigger surgical DOM updates through the
dependency graph established during render analysis.
"""

from typing import Optional

from .elements import Element, reset_id_counter
from .mutation_compiler import MutationCompiler, _js_string
from .state import DependencyTracker, State


def _collect_node_ids(element: Element) -> set[str]:
    """Recursively collect all node IDs from an element tree.

    Args:
        element: Root element to collect from.

    Returns:
        Set of all data-pyt-id values in the tree.
    """
    ids = {element.node_id}
    for child in getattr(element, "_children", []):
        ids.update(_collect_node_ids(child))
    return ids


class Component:
    """Base class for reactive Pytonium components.

    Subclasses define reactive state using State descriptors at the class level
    and implement render() to return an Element tree. State changes after
    mounting automatically trigger minimal DOM updates.

    Usage:
        class Counter(Component):
            count = State(0)

            def increment(self):
                self.count += 1

            def render(self):
                return (
                    Div()
                        .child(H1().text(lambda: f"Count: {self.count}"))
                        .child(Button().text("+").on_click(self.increment))
                )

        p = Pytonium()
        p.initialize("data:text/html,<html><body></body></html>", 800, 600)
        counter = Counter()
        counter.mount(p)
    """

    def __init__(self, **kwargs):
        """Initialize the component with optional initial state values.

        Args:
            **kwargs: Initial values for State fields. Keys must match
                      State descriptor names defined on the class.
        """
        self._pytonium = None
        self._mutation_compiler: Optional[MutationCompiler] = None
        self._event_router = None
        self._element_tree: Optional[Element] = None
        self._mounted: bool = False
        self._node_ids: set[str] = set()
        self._container_id: Optional[str] = None
        self._child_components: list["Component"] = []

        # Set initial state values from kwargs
        for key, value in kwargs.items():
            cls = type(self)
            if hasattr(cls, key) and isinstance(getattr(cls, key), State):
                setattr(self, key, value)

    def render(self) -> Element:
        """Return the element tree for this component.

        Called once during mount to establish the dependency graph. The
        returned Element tree defines the initial HTML structure and all
        reactive bindings.

        Must be overridden by subclasses.

        Returns:
            Root Element of the component's UI tree.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement render()"
        )

    def on_mount(self):
        """Lifecycle hook called after the component is mounted.

        Override to perform initialization after the HTML is in the DOM
        (e.g., fetch data, start timers).
        """
        pass

    def on_update(self, changed_fields: set[str]):
        """Lifecycle hook called after state changes are applied to the DOM.

        Override to perform side effects in response to state changes.

        Args:
            changed_fields: Set of State field names that changed.
        """
        pass

    def on_unmount(self):
        """Lifecycle hook called before the component is removed from the DOM.

        Override to clean up resources (e.g., cancel timers, close connections).
        """
        pass

    def mount(self, pytonium, container_id: Optional[str] = None):
        """Mount this component into a Pytonium browser.

        Performs the full initialization sequence:
        1. Reset element ID counter
        2. Call render() to get element tree
        3. Register component with DependencyTracker
        4. Analyze element tree for reactive dependencies
        5. Initialize DynamicChildrenManagers for children_from elements
        6. Generate initial HTML
        7. Inject HTML into the DOM
        8. Register event listeners
        9. Call on_mount() lifecycle hook

        Args:
            pytonium: Pytonium instance with an initialized browser.
            container_id: Optional HTML element ID to mount into.
                          If None, replaces document.body contents.
        """
        from .event_router import EventRouter

        self._pytonium = pytonium
        self._container_id = container_id
        self._mutation_compiler = MutationCompiler(pytonium)
        self._event_router = EventRouter(pytonium)
        self._event_router.set_component(self)

        # 1. Reset ID counter for this component's render
        reset_id_counter()

        # 2. Call render() to get element tree
        self._element_tree = self.render()

        # 3. Register component with dependency tracker
        DependencyTracker.register_component(self)

        # 4. Analyze element tree for reactive dependencies
        DependencyTracker.analyze(self, self._element_tree)

        # 5. Initialize DynamicChildrenManagers
        self._init_dynamic_children(self._element_tree)

        # 6. Initialize conditional elements (Show/Switch)
        self._init_conditionals(self._element_tree)

        # 7. Collect all node IDs
        self._node_ids = _collect_node_ids(self._element_tree)

        # 8. Generate initial HTML
        html = self._element_tree.to_html()

        # 9. Inject into DOM
        if container_id:
            js = (
                f"(function(){{"
                f"var c=document.getElementById({_js_string(container_id)});"
                f"if(c){{c.innerHTML={_js_string(html)};}}"
                f"else{{document.body.innerHTML={_js_string(html)};}}"
                f"}})()"
            )
        else:
            js = f"document.body.innerHTML={_js_string(html)};"
        pytonium.execute_javascript(js)

        # 10. Register event listeners
        self._event_router.register_events(self._element_tree)

        # 11. Mark as mounted and call lifecycle hook
        self._mounted = True
        self.on_mount()

    def unmount(self):
        """Unmount the component, cleaning up all resources.

        Removes the component from the dependency tracker, cleans up event
        handlers, and calls the on_unmount lifecycle hook.
        """
        if not self._mounted:
            return

        # Unmount child components first
        for child_comp in self._child_components:
            child_comp.unmount()
        self._child_components.clear()

        # Clean up dependency tracking
        DependencyTracker.unregister_component(self)

        # Clean up event handlers
        if self._event_router:
            self._event_router.cleanup()

        self._mounted = False
        self.on_unmount()

    def _init_dynamic_children(self, element: Element):
        """Initialize DynamicChildrenManagers for children_from elements.

        Walks the element tree and creates a manager for each element with
        dynamic children configuration.

        Args:
            element: Root element to scan.
        """
        if hasattr(element, "_dynamic_children") and element._dynamic_children:
            from .dynamic_children import DynamicChildrenManager
            dyn = element._dynamic_children
            manager = DynamicChildrenManager(
                parent_node_id=element.node_id,
                source_fn=dyn["source"],
                key_fn=dyn["key"],
                render_item_fn=dyn["render_item"],
                mutation_compiler=self._mutation_compiler,
                component=self,
                event_router=self._event_router,
            )
            element._dynamic_manager = manager
            # Initialize with current items
            manager.initialize()

        for child in getattr(element, "_children", []):
            self._init_dynamic_children(child)

    def _init_conditionals(self, element: Element):
        """Initialize conditional elements (Show/Switch).

        Args:
            element: Root element to scan.
        """
        for child in getattr(element, "_children", []):
            if hasattr(child, "_setup_reactive") and callable(child._setup_reactive):
                child._setup_reactive(
                    mutation_compiler=self._mutation_compiler,
                    component=self,
                    event_router=self._event_router,
                )
            self._init_conditionals(child)
