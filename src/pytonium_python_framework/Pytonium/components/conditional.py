"""Conditional rendering elements: Show and Switch.

Since render() is called once to establish the dependency graph, the
component structure cannot change based on if/else logic inside render().
Instead, conditional rendering is handled by these special control-flow
elements that manage mounting and unmounting sub-trees when conditions change.

Show: Renders one of two branches based on a boolean condition.
Switch: Renders one of multiple branches based on a value selector.

Usage:
    class App(Component):
        logged_in = State(False)
        tab = State("home")

        def render(self):
            return Div().child(
                Show(
                    when=lambda: self.logged_in,
                    then=lambda: Div().text("Welcome!"),
                    fallback=lambda: Div().text("Please log in"),
                )
            ).child(
                Switch(lambda: self.tab)
                    .case("home", lambda: Div().text("Home"))
                    .case("settings", lambda: Div().text("Settings"))
                    .default(lambda: Div().text("Not Found"))
            )
"""

from typing import Any, Callable, Optional

from .elements import Element, _generate_id
from .mutation_compiler import MutationCompiler, _js_string
from .state import DependencyTracker
from .types import UpdateCommand, UpdateType


class Show(Element):
    """Conditional element that renders one of two branches.

    Renders as a placeholder <div> in the DOM. When the condition changes,
    the old branch is unmounted and the new branch is mounted in its place.

    Args:
        when: Lambda returning a boolean condition.
        then: Lambda returning an Element to show when condition is True.
        fallback: Optional lambda returning an Element for when False.
    """

    def __init__(
        self,
        when: Callable,
        then: Callable,
        fallback: Optional[Callable] = None,
    ):
        super().__init__("div")
        self._when = when
        self._then_fn = then
        self._fallback_fn = fallback
        self._current_branch: Optional[str] = None  # "then", "fallback", or None
        self._current_element: Optional[Element] = None
        self._mutation_compiler: Optional[MutationCompiler] = None
        self._component = None
        self._event_router = None

        # Register the condition as a reactive binding
        self._condition_binding = {"when": when}

    def _setup_reactive(self, mutation_compiler, component, event_router):
        """Set up reactive tracking for this conditional element.

        Called during component mount initialization.
        """
        self._mutation_compiler = mutation_compiler
        self._component = component
        self._event_router = event_router

        # Evaluate initial condition
        self._evaluate_condition()

    def _evaluate_condition(self):
        """Evaluate the when condition and mount/unmount branches as needed."""
        try:
            condition = self._when()
        except Exception:
            condition = False

        new_branch = "then" if condition else "fallback"

        if new_branch == self._current_branch:
            return  # No change

        # Unmount current branch
        if self._current_element:
            DependencyTracker.remove_element_bindings(self._current_element)
            if self._event_router:
                self._event_router.remove_element_handlers(self._current_element)
            self._current_element = None

        # Mount new branch
        if new_branch == "then" and self._then_fn:
            self._current_element = self._then_fn()
        elif new_branch == "fallback" and self._fallback_fn:
            self._current_element = self._fallback_fn()

        self._current_branch = new_branch

        # Update the DOM
        if self._current_element and self._mutation_compiler:
            # Analyze dependencies for the new subtree
            if self._component:
                DependencyTracker.analyze(self._component, self._current_element)

            html = self._current_element.to_html()
            self._mutation_compiler.apply_batch([
                UpdateCommand(
                    node_id=self.node_id,
                    update_type=UpdateType.REPLACE_INNER_HTML,
                    html=html,
                )
            ])

            # Register event listeners for the new subtree
            if self._event_router:
                self._event_router._register_element_events(self._current_element)
        elif self._mutation_compiler:
            # Clear the placeholder
            self._mutation_compiler.apply_batch([
                UpdateCommand(
                    node_id=self.node_id,
                    update_type=UpdateType.REPLACE_INNER_HTML,
                    html="",
                )
            ])

    def to_html(self) -> str:
        """Generate initial HTML based on the current condition value.

        Returns a <div> with the data-pyt-id marker containing the
        initial branch's HTML.
        """
        try:
            condition = self._when()
        except Exception:
            condition = False

        inner_html = ""
        if condition and self._then_fn:
            self._current_element = self._then_fn()
            self._current_branch = "then"
            inner_html = self._current_element.to_html()
        elif not condition and self._fallback_fn:
            self._current_element = self._fallback_fn()
            self._current_branch = "fallback"
            inner_html = self._current_element.to_html()

        return f'<div data-pyt-id="{self.node_id}" data-pyt-show="true">{inner_html}</div>'


class Switch(Element):
    """Multi-branch conditional element based on a value selector.

    Renders the branch matching the selector's current value. When the
    selector value changes, the old branch is unmounted and the new
    branch is mounted.

    Usage:
        Switch(lambda: self.tab)
            .case("home", lambda: HomePage())
            .case("settings", lambda: SettingsPage())
            .default(lambda: NotFoundPage())
    """

    def __init__(self, selector: Callable):
        super().__init__("div")
        self._selector = selector
        self._cases: dict[Any, Callable] = {}
        self._default_fn: Optional[Callable] = None
        self._current_value: Any = None
        self._current_element: Optional[Element] = None
        self._mutation_compiler: Optional[MutationCompiler] = None
        self._component = None
        self._event_router = None

        # Register the selector as a reactive binding
        self._condition_binding = {"when": selector}

    def case(self, value: Any, element_fn: Callable) -> "Switch":
        """Register a branch for a specific selector value.

        Args:
            value: The value to match against the selector.
            element_fn: Lambda returning an Element for this branch.

        Returns:
            self for method chaining.
        """
        self._cases[value] = element_fn
        return self

    def default(self, element_fn: Callable) -> "Switch":
        """Register the default branch (used when no case matches).

        Args:
            element_fn: Lambda returning an Element for the default case.

        Returns:
            self for method chaining.
        """
        self._default_fn = element_fn
        return self

    def _setup_reactive(self, mutation_compiler, component, event_router):
        """Set up reactive tracking for this switch element."""
        self._mutation_compiler = mutation_compiler
        self._component = component
        self._event_router = event_router
        self._evaluate_condition()

    def _evaluate_condition(self):
        """Evaluate the selector and mount the matching branch."""
        try:
            new_value = self._selector()
        except Exception:
            new_value = None

        if new_value == self._current_value and self._current_element:
            return  # No change

        # Unmount current branch
        if self._current_element:
            DependencyTracker.remove_element_bindings(self._current_element)
            if self._event_router:
                self._event_router.remove_element_handlers(self._current_element)
            self._current_element = None

        self._current_value = new_value

        # Find matching branch
        element_fn = self._cases.get(new_value, self._default_fn)
        if element_fn:
            self._current_element = element_fn()

        # Update the DOM
        if self._current_element and self._mutation_compiler:
            if self._component:
                DependencyTracker.analyze(self._component, self._current_element)

            html = self._current_element.to_html()
            self._mutation_compiler.apply_batch([
                UpdateCommand(
                    node_id=self.node_id,
                    update_type=UpdateType.REPLACE_INNER_HTML,
                    html=html,
                )
            ])

            if self._event_router:
                self._event_router._register_element_events(self._current_element)
        elif self._mutation_compiler:
            self._mutation_compiler.apply_batch([
                UpdateCommand(
                    node_id=self.node_id,
                    update_type=UpdateType.REPLACE_INNER_HTML,
                    html="",
                )
            ])

    def to_html(self) -> str:
        """Generate initial HTML based on the current selector value."""
        try:
            value = self._selector()
        except Exception:
            value = None

        self._current_value = value
        inner_html = ""

        element_fn = self._cases.get(value, self._default_fn)
        if element_fn:
            self._current_element = element_fn()
            inner_html = self._current_element.to_html()

        return f'<div data-pyt-id="{self.node_id}" data-pyt-switch="true">{inner_html}</div>'
