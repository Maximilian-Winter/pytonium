"""Event routing from JavaScript DOM events to Python handlers.

The EventRouter binds a single Python function to JavaScript that receives
all DOM events routed by node ID. During mount, it injects JS event listeners
for each element with event handlers. When an event fires, the JS listener
serializes event data and calls the bound Python function, which dispatches
to the correct handler.

This approach uses one bound function for all events, minimizing the number
of Python-JS bindings required.
"""

import inspect
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .mutation_compiler import _js_string


@dataclass
class EventData:
    """Deserialized DOM event data passed to Python handlers.

    Contains the most commonly needed event properties. Handlers can accept
    this as their single argument, or take no arguments.

    Attributes:
        type: Event type (e.g., "click", "keydown", "input").
        value: e.target.value (for input/textarea/select elements).
        key: Keyboard key name (for keydown/keyup events).
        key_code: Keyboard key code.
        client_x: Mouse X position relative to viewport.
        client_y: Mouse Y position relative to viewport.
        shift_key: Whether Shift was held.
        ctrl_key: Whether Ctrl was held.
        alt_key: Whether Alt was held.
        meta_key: Whether Meta/Cmd was held.
        checked: e.target.checked (for checkboxes).
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


def _accepts_event_arg(handler: Callable) -> bool:
    """Check if a handler function accepts an EventData argument.

    Returns True if the handler has at least one parameter without a default
    value (excluding 'self').  Parameters with defaults are assumed to be
    closure captures (e.g., ``lambda t=t: ...``), not event data slots.
    """
    try:
        sig = inspect.signature(handler)
        params = [
            p for p in sig.parameters.values()
            if p.name != "self"
            and p.default is inspect.Parameter.empty
        ]
        return len(params) >= 1
    except (ValueError, TypeError):
        return False


class EventRouter:
    """Routes DOM events from JavaScript to Python handlers.

    The router maintains a mapping of (node_id, event_type) → handler.
    A single Python function is bound to JavaScript as the event receiver.
    JS event listeners serialize event data and call this function.

    IMPORTANT: Call ``EventRouter.prepare(pytonium)`` (or the convenience
    wrapper ``Component.setup(pytonium)``) **before** ``pytonium.initialize()``
    so that the global event-handler binding is available when CEF's
    ``OnContextCreated`` fires.  Bindings registered after the page has
    already loaded will NOT be visible in JavaScript.

    Usage:
        p = Pytonium()
        EventRouter.prepare(p)          # or Component.setup(p)
        p.initialize(url, w, h)
        router = EventRouter(p)
        router.register_events(element_tree)
        # Later, when component unmounts:
        router.cleanup()
    """

    # Class-level registry of all active routers (for the global handler)
    _active_routers: dict[int, "EventRouter"] = {}
    _bound_to_js: bool = False
    _prepared: bool = False
    _component_ref = None

    def __init__(self, pytonium):
        """Initialize with a Pytonium instance.

        Args:
            pytonium: Pytonium instance for binding functions and executing JS.
        """
        self._pytonium = pytonium
        self._handlers: dict[tuple[str, str], dict] = {}
        self._router_id = id(self)
        self._component = None
        EventRouter._active_routers[self._router_id] = self

    @classmethod
    def prepare(cls, pytonium):
        """Pre-register the global event handler with JavaScript.

        MUST be called **before** ``pytonium.initialize()`` so the binding
        is available when CEF's ``OnContextCreated`` fires.  Bindings added
        after the page loads are not picked up by the renderer process.

        It is safe to call this multiple times — subsequent calls are no-ops.

        Args:
            pytonium: Pytonium instance (not yet initialized).
        """
        if cls._bound_to_js:
            return

        def _pyt_event_handler(node_id: str, event_type: str, event_json: str):
            """Global event handler called from JavaScript."""
            for router in cls._active_routers.values():
                handler_info = router._handlers.get((node_id, event_type))
                if handler_info:
                    router._dispatch_event(
                        handler_info, node_id, event_type, event_json
                    )
                    return

        pytonium.bind_function_to_javascript(
            _pyt_event_handler,
            name="_event",
            javascript_object="_internal",
        )

        def _pyt_buffered_input(data_json: str):
            """Handle buffered input events (requestAnimationFrame batched)."""
            try:
                data = json.loads(data_json)
            except (json.JSONDecodeError, TypeError):
                return
            for node_id, value in data.items():
                for router in cls._active_routers.values():
                    handler_info = router._handlers.get((node_id, "input"))
                    if handler_info:
                        event_data = EventData(type="input", value=str(value))
                        handler = handler_info["handler"]
                        component = router._component
                        if component:
                            from .state import DependencyTracker
                            DependencyTracker.begin_batch(component)
                        try:
                            if _accepts_event_arg(handler):
                                handler(event_data)
                            else:
                                handler()
                        except Exception:
                            import traceback
                            traceback.print_exc()
                        finally:
                            if component:
                                DependencyTracker.flush_batch(component)

        pytonium.bind_function_to_javascript(
            _pyt_buffered_input,
            name="_buffered_input",
            javascript_object="_internal",
        )

        cls._bound_to_js = True
        cls._prepared = True

    def set_component(self, component):
        """Set the component for batch context during event handling.

        Args:
            component: The Component instance that owns these events.
        """
        self._component = component

    def register_events(self, element, bind_to_js: bool = True):
        """Register event listeners for an element tree.

        Walks the element tree recursively. For each element with event
        handlers, registers the handler in the Python routing table and
        injects a JS event listener that calls back to Python.

        Args:
            element: Root Element of the tree.
            bind_to_js: Whether to bind the global event handler to JS.
                        Set to True for the first call, False for subtrees.
        """
        if bind_to_js and not EventRouter._bound_to_js:
            self._bind_global_handler()
            EventRouter._bound_to_js = True

        self._register_element_events(element)

    def _bind_global_handler(self):
        """Bind the global event handler function to JavaScript.

        Creates a single Python function accessible as
        Pytonium._internal._event() in JavaScript.
        """
        router_id = self._router_id

        def _pyt_event_handler(node_id: str, event_type: str, event_json: str):
            """Global event handler called from JavaScript."""
            for router in EventRouter._active_routers.values():
                handler_info = router._handlers.get((node_id, event_type))
                if handler_info:
                    router._dispatch_event(
                        handler_info, node_id, event_type, event_json
                    )
                    return

        self._pytonium.bind_function_to_javascript(
            _pyt_event_handler,
            name="_event",
            javascript_object="_internal",
        )

        # Also bind the buffered input handler for high-frequency events
        def _pyt_buffered_input(data_json: str):
            """Handle buffered input events (requestAnimationFrame batched)."""
            try:
                data = json.loads(data_json)
            except (json.JSONDecodeError, TypeError):
                return
            for node_id, value in data.items():
                for router in EventRouter._active_routers.values():
                    handler_info = router._handlers.get((node_id, "input"))
                    if handler_info:
                        event_data = EventData(type="input", value=str(value))
                        handler = handler_info["handler"]
                        component = router._component
                        if component:
                            from .state import DependencyTracker
                            DependencyTracker.begin_batch(component)
                        try:
                            if _accepts_event_arg(handler):
                                handler(event_data)
                            else:
                                handler()
                        except Exception:
                            import traceback
                            traceback.print_exc()
                        finally:
                            if component:
                                DependencyTracker.flush_batch(component)

        self._pytonium.bind_function_to_javascript(
            _pyt_buffered_input,
            name="_buffered_input",
            javascript_object="_internal",
        )

    def _register_element_events(self, element):
        """Register events for a single element and recurse into children."""
        for event_type, event_info in getattr(element, "_events", {}).items():
            handler = event_info.get("handler")
            if handler is None:
                continue

            # Store handler in routing table
            self._handlers[(element.node_id, event_type)] = event_info

            # Generate JS event listener
            js = self._generate_listener_js(
                element.node_id,
                event_type,
                event_info,
            )
            self._pytonium.execute_javascript(js)

        # Recurse into children
        for child in getattr(element, "_children", []):
            self._register_element_events(child)

        # Recurse into conditional elements' active branch (Show/Switch)
        current = getattr(element, "_current_element", None)
        if current is not None:
            self._register_element_events(current)

    def _generate_listener_js(
        self, node_id: str, event_type: str, event_info: dict
    ) -> str:
        """Generate JavaScript code to register a DOM event listener.

        Args:
            node_id: The element's data-pyt-id.
            event_type: DOM event type (e.g., "click", "keydown").
            event_info: Handler configuration dict.

        Returns:
            JavaScript code string.
        """
        prevent_default = event_info.get("prevent_default", False)
        buffered = event_info.get("buffered", False)
        debounce_ms = event_info.get("debounce_ms", 0)

        prevent_js = "e.preventDefault();" if prevent_default else ""

        # Buffered input events use requestAnimationFrame batching
        if buffered and event_type == "input":
            return self._generate_buffered_listener_js(
                node_id, debounce_ms
            )

        # Standard event listener
        return (
            f"(function(){{"
            f'var el=document.querySelector(\'[data-pyt-id="{node_id}"]\');'
            f"if(el){{el.addEventListener('{event_type}',function(e){{"
            f"{prevent_js}"
            f"Pytonium._internal._event('{node_id}','{event_type}',"
            f"JSON.stringify({{"
            f"value:e.target?e.target.value||'':'',"
            f"key:e.key||'',"
            f"keyCode:e.keyCode||0,"
            f"clientX:e.clientX||0,"
            f"clientY:e.clientY||0,"
            f"shiftKey:!!e.shiftKey,"
            f"ctrlKey:!!e.ctrlKey,"
            f"altKey:!!e.altKey,"
            f"metaKey:!!e.metaKey,"
            f"checked:e.target?!!e.target.checked:false"
            f"}}));}});}}}})();"
        )

    def _generate_buffered_listener_js(
        self, node_id: str, debounce_ms: int
    ) -> str:
        """Generate JS for a buffered input listener using requestAnimationFrame.

        Instead of one IPC call per keystroke, buffers values and sends
        at most once per animation frame (~16ms at 60fps).

        Args:
            node_id: The element's data-pyt-id.
            debounce_ms: Additional debounce delay (0 = frame-only buffering).

        Returns:
            JavaScript code string.
        """
        if debounce_ms > 0:
            # Debounced: wait N ms after last input before sending
            return (
                f"(function(){{"
                f'var el=document.querySelector(\'[data-pyt-id="{node_id}"]\');'
                f"if(el){{var t=null;"
                f"el.addEventListener('input',function(e){{"
                f"clearTimeout(t);"
                f"t=setTimeout(function(){{"
                f"var d={{}};d['{node_id}']=el.value;"
                f"Pytonium._internal._buffered_input(JSON.stringify(d));"
                f"}},{debounce_ms});"
                f"}});}}}})();"
            )

        # Frame-buffered: send on next requestAnimationFrame
        return (
            f"(function(){{"
            f'var el=document.querySelector(\'[data-pyt-id="{node_id}"]\');'
            f"if(el){{var buf={{}},sched=false;"
            f"el.addEventListener('input',function(e){{"
            f"buf['{node_id}']=e.target.value;"
            f"if(!sched){{sched=true;"
            f"requestAnimationFrame(function(){{"
            f"Pytonium._internal._buffered_input(JSON.stringify(buf));"
            f"buf={{}};sched=false;"
            f"}});}}"
            f"}});}}}})();"
        )

    def _dispatch_event(
        self,
        handler_info: dict,
        node_id: str,
        event_type: str,
        event_json: str,
    ):
        """Dispatch a received event to its Python handler.

        Wraps the handler call in a batch context so that all state changes
        from a single event are coalesced into one DOM update batch.

        Args:
            handler_info: Dict with 'handler' and optional config.
            node_id: The element's data-pyt-id.
            event_type: DOM event type.
            event_json: Serialized event data from JavaScript.
        """
        handler = handler_info["handler"]

        # Deserialize event data
        event_data = EventData(type=event_type)
        try:
            data = json.loads(event_json)
            event_data.value = data.get("value", "")
            event_data.key = data.get("key", "")
            event_data.key_code = data.get("keyCode", 0)
            event_data.client_x = data.get("clientX", 0.0)
            event_data.client_y = data.get("clientY", 0.0)
            event_data.shift_key = data.get("shiftKey", False)
            event_data.ctrl_key = data.get("ctrlKey", False)
            event_data.alt_key = data.get("altKey", False)
            event_data.meta_key = data.get("metaKey", False)
            event_data.checked = data.get("checked", False)
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

        # Begin batch for this event handler
        component = self._component
        if component:
            from .state import DependencyTracker
            DependencyTracker.begin_batch(component)

        try:
            if _accepts_event_arg(handler):
                handler(event_data)
            else:
                handler()
        except Exception:
            import traceback
            traceback.print_exc()
        finally:
            if component:
                from .state import DependencyTracker
                DependencyTracker.flush_batch(component)

    def remove_handler(self, node_id: str, event_type: str):
        """Remove a specific event handler.

        Args:
            node_id: The element's data-pyt-id.
            event_type: DOM event type to remove.
        """
        self._handlers.pop((node_id, event_type), None)

    def remove_element_handlers(self, element):
        """Remove all event handlers for an element and its children.

        Args:
            element: Element whose handlers to remove.
        """
        for event_type in list(getattr(element, "_events", {}).keys()):
            self._handlers.pop((element.node_id, event_type), None)
        for child in getattr(element, "_children", []):
            self.remove_element_handlers(child)

    def cleanup(self):
        """Remove all handlers and unregister this router."""
        self._handlers.clear()
        EventRouter._active_routers.pop(self._router_id, None)
        if not EventRouter._active_routers and not EventRouter._prepared:
            EventRouter._bound_to_js = False
