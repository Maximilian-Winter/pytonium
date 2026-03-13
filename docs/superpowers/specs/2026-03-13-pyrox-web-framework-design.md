# Pyrox — Reactive Python Web Framework

**Date:** 2026-03-13
**Status:** Design approved, pending implementation plan
**Origin:** Exploration of using Pytonium's reactive component model over WebSocket for real web applications

---

## Overview

Pyrox is a standalone Python library that brings server-side reactive components to the web. Inspired by Pytonium's reactive component system, Pyrox lets developers build interactive web applications entirely in Python — no JavaScript framework, no build step, no virtual DOM.

The server renders components, tracks state, and sends surgical DOM mutations over WebSocket. A tiny JS client library (~3-5KB) applies mutations and relays user events back. Similar in spirit to Phoenix LiveView and Blazor Server, but Pythonic and lightweight.

**Key decisions:**
- **Standalone library** — no dependency on Pytonium or CEF
- **ASGI middleware** — works with FastAPI, Starlette, Litestar, any ASGI framework
- **Hybrid client** — server is source of truth, JS handles latency-sensitive UX (optimistic input echo, button disable, transitions)
- **Async-first** — event handlers are `async def`, automatic batching
- **Clean-room reimplementation** — Pytonium's reactive core as blueprint, redesigned for multi-user web from the ground up

---

## Architecture

### Four Layers

```
┌─────────────────────────────────────┐
│  Layer 4: ASGI Integration          │  Mount into FastAPI/Starlette
│  PyroxMiddleware, route handling     │
├─────────────────────────────────────┤
│  Layer 3: Session Manager           │  WebSocket ↔ Session ↔ Components
│  SessionStore protocol, lifecycle    │
├─────────────────────────────────────┤
│  Layer 2: Reactive Core             │  State, Elements, DependencyTracker
│  MutationCompiler, EventDispatcher   │  (Pytonium-inspired, async-native)
├─────────────────────────────────────┤
│  Layer 1: Transport Protocol        │  WebSocket message format (JSON)
│  Client JS lib ↔ Server codec       │  Optimistic updates, reconnection
└─────────────────────────────────────┘
```

### Package Structure

```
pyrox/
├── core/           # State, Elements, DependencyTracker, Computed
├── compiler/       # MutationCompiler (→ JSON), message codec
├── session/        # SessionManager, SessionStore protocol, lifecycle
├── asgi/           # PyroxMiddleware, WebSocket handler, static serving
├── client/         # pyrox.js (built JS lib, served automatically)
└── components/     # Optional pre-built components (later)
```

### Key Differences from Pytonium's Reactive Core

| Concern | Pytonium | Pyrox |
|---------|----------|-------|
| DependencyTracker | Class-level `_dependency_map` with `id(component)` keys | **Instance-level** — each component owns its tracker |
| Mutation output | JS string via `execute_javascript()` | JSON message via `session.send()` |
| Batching | Manual `begin_batch()`/`flush_batch()` | **Automatic** — batch opens on first state change, flushes when handler returns |
| Event handlers | Sync `def` | **`async def`** (sync supported via auto-wrapping) |
| State storage | `component.__dict__` | Same — instance `__dict__` |
| Computed | `@Computed` decorator | Same pattern, synchronous only (like Pytonium) |

---

## Layer 1: Transport Protocol

### Message Format — Bidirectional JSON over WebSocket

**Server → Client (DOM mutations):**
```json
{
  "type": "mutations",
  "batch": [
    {"op": "text", "id": "n3", "value": "Count: 5"},
    {"op": "attr", "id": "n7", "key": "disabled", "value": "true"},
    {"op": "insert", "id": "n2", "html": "<li data-pyrox-id=\"n9\">...</li>", "index": 3},
    {"op": "remove", "id": "n2", "child": "n5"},
    {"op": "class_add", "id": "n4", "value": "active"},
    {"op": "style", "id": "n6", "key": "opacity", "value": "0.5"}
  ]
}
```

**Client → Server (events):**
```json
{
  "type": "event",
  "node_id": "n3",
  "event": "click",
  "data": {"x": 120, "y": 45}
}
```

**Client → Server (input sync):**
```json
{
  "type": "input",
  "node_id": "n7",
  "value": "hello wor"
}
```

**Server → Client (initial render):**
```json
{
  "type": "mount",
  "html": "<div data-pyrox-id=\"n0\">...</div>",
  "container": "#app"
}
```

### Mutation Operations

| Op | Fields | Description |
|----|--------|-------------|
| `text` | `id`, `value` | Set textContent |
| `attr` | `id`, `key`, `value` | Set attribute |
| `remove_attr` | `id`, `key` | Remove attribute |
| `class_add` | `id`, `value` | Add CSS class |
| `class_remove` | `id`, `value` | Remove CSS class |
| `class_toggle` | `id`, `value` | Toggle CSS class |
| `style` | `id`, `key`, `value` | Set style property |
| `value` | `id`, `value` | Set input value |
| `insert` | `id`, `html`, `index` | Insert child at position |
| `remove` | `id`, `child` | Remove child by id |
| `move` | `id`, `child`, `index` | Move child to position |
| `inner_html` | `id`, `html` | Replace innerHTML |

---

## Layer 2: Reactive Core

### Component API

```python
class Counter(Component):
    count = State(0)
    name = State("world")

    async def increment(self):
        self.count += 1

    def render(self):
        return (
            Div()
                .child(H1().text(lambda: f"Hello, {self.name}! Count: {self.count}"))
                .child(Button().text("+").on_click(self.increment))
                .child(Input().bind_value(lambda: self.name).on_input(self.on_name_change))
        )

    async def on_name_change(self, event):
        self.name = event["value"]
```

### State Descriptor

- Same Python descriptor pattern as Pytonium
- `__set__` queues mutations into the component's batch list
- Batch is auto-flushed when the event handler that triggered the change returns
- For server-push scenarios (background tasks), call `await self.flush()` to send immediately
- `@Computed` properties are synchronous cached values (same as Pytonium), not async

### Flush API

Two flush mechanisms, clearly separated:

- **`_auto_flush()`** (private, called by framework): Called automatically by the EventDispatcher after each event handler returns. Not async — the dispatcher awaits the handler, then calls `_auto_flush()` synchronously.
- **`async flush()`** (public, called by developer): For server-push scenarios where state changes happen outside an event handler (e.g., background polling tasks). Awaitable because it sends over the WebSocket.

```python
class Component:
    def _auto_flush(self):
        """Called by EventDispatcher after handler returns. Not user-facing."""
        if self._batch:
            # Synchronous send — EventDispatcher handles the await
            self._session.send_sync({"type": "mutations", "batch": self._batch})
            self._batch = []

    async def flush(self):
        """Explicitly send queued mutations. Use in background tasks."""
        if self._batch:
            await self._session.send({"type": "mutations", "batch": self._batch})
            self._batch = []
            # If WebSocket is disconnected (grace period), mutations are silently dropped
```

### DependencyTracker — Instance-Scoped

```python
class Component:
    def __init__(self):
        self._tracker = DependencyTracker()  # Per-instance, not global
        self._compiler = MutationCompiler()
        self._batch: list[dict] = []
        self._session: Session | None = None
```

No `id()` reuse bugs, no weakref cleanup — session end = garbage collection.

### Element Builder — Identical API to Pytonium

```python
Div().id("main").cls("container").child(
    H1().text(lambda: f"Count: {self.count}"),
    Button().text("+").on_click(self.increment),
    Ul().children_from(
        source=lambda: self.items,
        key=lambda item: item["id"],
        render_item=lambda item, i: Li().text(item["name"]),
    ),
    Show(when=lambda: self.loading).child(Span().text("Loading...")),
)
```

### Lifecycle Hooks

All lifecycle hooks are `async def` and awaited by the framework:

```python
class Component:
    async def on_mount(self):
        """Called after initial HTML is sent to client. Start background tasks here."""
        pass

    async def on_update(self, changed_fields: set[str]):
        """Called after state changes are flushed. Perform side effects here."""
        pass

    async def on_unmount(self):
        """Called when session expires or component is removed. Cancel tasks here."""
        pass

    async def on_error(self, error: Exception, context: str):
        """Called when an event handler raises. Override for custom error handling."""
        pass
```

Sync handlers are supported via auto-wrapping (`asyncio.to_thread` for CPU-bound, or direct call for trivial sync handlers). The framework inspects the handler with `asyncio.iscoroutinefunction()` and wraps if needed.

### Input Binding Model

Two message types work together for inputs:

- **`"input"` messages**: Debounced value sync (every 50-100ms). The client sends the current input value. The server updates the bound State field silently (no mutation echoed back, since the client already has the value).
- **`"event"` messages**: Discrete events like `on_input`, `on_change`, `on_blur`. These trigger the registered handler.

For `Input().bind_value(lambda: self.name).on_input(self.on_name_change)`:
1. User types → client echoes keystroke locally (optimistic)
2. Client sends `{"type": "input", "node_id": "n7", "value": "hello"}` (debounced)
3. Server sets `self.name = "hello"` without emitting a `value` mutation back (client already shows it)
4. If the handler modifies the value (e.g., auto-capitalize), the server sends a `value` mutation to correct the client
5. Client receives `{"op": "value", ...}` → replaces its local value, reconciliation complete

### Node ID Generation

Node IDs use a per-component incrementing counter: `n0`, `n1`, `n2`, etc. Each component instance has its own counter starting at 0. IDs are prefixed with the component's session-scoped index to ensure uniqueness across components on the same page (e.g., component 0 gets `c0-n0`, `c0-n1`; component 1 gets `c1-n0`, `c1-n1`).

On reconnection, `render()` is called again and node IDs are regenerated from scratch. The server sends a full `{"type": "mount", ...}` message that replaces the container's innerHTML entirely. This means node IDs are **not** stable across reconnections — CSS transitions on reconnect will not animate (acceptable trade-off for simplicity).

### Component Composition

Components can be nested within other components' element trees:

```python
class App(Component):
    def render(self):
        return (
            Div()
                .child(Header())         # Header is a Component subclass
                .child(MainContent())
                .child(Footer())
        )
```

Nested component semantics:
- Each child component gets its own `DependencyTracker`, `MutationCompiler`, and batch
- Child components share the parent's Session (and its serialization lock)
- Node IDs are scoped by component index — no collisions
- `on_mount()` is called depth-first (children before parent)
- `on_unmount()` is called depth-first (children before parent)
- Parent state changes do NOT re-render children unless the child explicitly depends on parent state (via props or shared state — design TBD for v1; simple prop-passing is sufficient initially)

### Automatic Batching Flow

```
User clicks button
  → Client sends {"type": "event", "node_id": "n3", "event": "click"}
  → Server: EventDispatcher looks up handler
  → Server: Opens implicit batch
  → Server: Calls await component.increment()
  → State.__set__ → tracker resolves bindings → mutations queued
  → Server: Handler returns → batch auto-flushed
  → Server sends {"type": "mutations", "batch": [...]}
  → Client applies DOM mutations
```

---

## Layer 3: Session Management

### Session Lifecycle

```
WebSocket connects
  → SessionManager creates Session(id, websocket)
  → Component() instantiated, bound to session
  → component.render() called
  → Initial HTML sent via {"type": "mount", ...}
  → Session is now live

WebSocket disconnects
  → Session enters grace period (default 30s, configurable)
  → If reconnect within grace period:
      → Rebind WebSocket to existing Session
      → Send full re-render (server is source of truth)
  → If grace period expires:
      → component.on_unmount() called
      → Session garbage collected

WebSocket reconnects
  → Client sends {"type": "reconnect", "session_id": "abc123"}
  → Server finds existing session, rebinds, re-renders
```

### SessionStore Protocol

```python
class SessionStore(Protocol):
    async def get(self, session_id: str) -> Session | None: ...
    async def set(self, session_id: str, session: Session) -> None: ...
    async def delete(self, session_id: str) -> None: ...
    async def cleanup_expired(self) -> None: ...

class InMemoryStore:
    """Default store. Dict-based, single process."""
    def __init__(self):
        self._sessions: dict[str, Session] = {}
```

Swap to Redis/DB later by implementing the protocol — no core changes.

### Session Object

```python
class Session:
    id: str
    component: Component
    websocket: WebSocket | None    # None during disconnect grace period
    created_at: float
    last_active: float
    grace_until: float | None      # Set on disconnect
```

### Multiple Components Per Page

```python
@app.get("/dashboard")
async def dashboard():
    return pyrox.page(
        title="Dashboard",
        components={
            "#header": HeaderNav,
            "#main": DashboardPanel,
            "#sidebar": ActivityFeed(limit=20),
        }
    )
```

Each component gets its own tracker/compiler and its own batch list. Components within a session are processed sequentially — the EventDispatcher holds a per-session asyncio lock so that only one event handler runs at a time. This prevents interleaving of state changes across components. Background tasks (server push) must also acquire this lock before modifying state:

```python
class Session:
    _lock: asyncio.Lock  # Serializes all state mutations within this session

    # EventDispatcher acquires lock before calling handler:
    async def dispatch_event(self, component, handler, event_data):
        async with self._lock:
            await handler(event_data)
            component._auto_flush()

    # Background tasks use the same lock:
    async def push_update(self, component, updater):
        async with self._lock:
            await updater()
            await component.flush()
```

Multiple components' mutations are sent as separate WebSocket messages (not merged into one batch), keeping component boundaries clean.

---

## Layer 4: ASGI Integration

### Mounting

```python
from pyrox import Pyrox, Component, State, Div, H1, Button

# FastAPI
from fastapi import FastAPI
app = FastAPI()
pyrox = Pyrox()
pyrox.mount_component("/counter", Counter)
app.mount("/_pyrox", pyrox.asgi_app())

# Standalone (no framework needed)
import uvicorn
pyrox = Pyrox()
pyrox.mount_component("/", Counter)
uvicorn.run(pyrox.asgi_app(), port=8000)
```

### Auto-Served Routes

| Route | Purpose |
|-------|---------|
| `/_pyrox/pyrox.js` | Client JS library |
| `/_pyrox/ws?path=/counter` | WebSocket endpoint (path identifies which component route) |
| `/_pyrox/static/...` | Optional static files |
| Mounted paths (`/counter`) | HTML page shell with Pyrox bootstrap |

### Page Shell

```python
# Auto-generated (zero config)
pyrox.mount_component("/counter", Counter)
# Serves minimal HTML: <div id="app"></div> + pyrox.js

# Custom template
pyrox.mount_component("/dashboard", DashboardPanel, template="dashboard.html")
```

### Server Push (Background Updates)

```python
class LiveMonitor(Component):
    cpu = State(0.0)
    memory = State(0.0)

    async def on_mount(self):
        self._task = asyncio.create_task(self._poll())

    async def _poll(self):
        while True:
            async with self._session.lock():
                self.cpu = psutil.cpu_percent()
                self.memory = psutil.virtual_memory().percent
                await self.flush()
            await asyncio.sleep(1)

    async def on_unmount(self):
        self._task.cancel()
```

### Dependencies

```
pyrox (the package)
├── Required: none beyond stdlib (websockets handled by ASGI server)
├── Optional: uvicorn (for standalone serving)
└── Works with: FastAPI, Starlette, Litestar, any ASGI framework
```

Zero heavy dependencies. No React, no Node, no build step.

---

## The `pyrox.js` Client Library

**Size target:** ~3-5KB gzipped

**Responsibilities:**
- WebSocket connection management with auto-reconnect (exponential backoff)
- Apply mutation batches to DOM via `querySelector('[data-pyrox-id="..."]')` + direct DOM API
- Event delegation on document root for `[data-pyrox-id]` elements
- **Optimistic input echo:** keystrokes applied locally, reconciled on server confirmation
- **Debounced input sync:** send values every 50-100ms, not per keystroke
- **Button disable:** auto-disable on click until server responds (prevent double-submit)
- CSS transition support: mutations apply classes/styles, browser handles animations
- Connection status: `Pyrox.connected` property, `pyrox:disconnect`/`pyrox:reconnect` events

**What it does NOT do:**
- No client-side routing
- No client-side state management
- No templating engine
- No virtual DOM diffing

**Usage:**
```html
<script src="/_pyrox/pyrox.js"></script>
<script>Pyrox.connect("#app", {path: "/counter"});</script>
```

The `path` option tells the WebSocket which component route to connect to. The auto-generated page shell fills this in automatically. For multi-component pages, `Pyrox.connect()` is called once per container.

---

## Error Handling

### Atomic Batches

If an event handler raises an exception, the pending batch is discarded — no partial mutations reach the client. State values that were set before the error **remain changed** in the server-side component (no automatic rollback). This is intentional: rolling back state would require deep-copying all State fields before each handler, which is expensive and has unclear semantics for side effects (e.g., if the handler wrote to a database before the error). The `on_error()` hook gives the developer a chance to manually revert state if needed.

### Error Flow

1. Event handler raises an exception
2. EventDispatcher catches it, discards the pending mutation batch
3. `await component.on_error(error, context)` called — component can log, revert state, or send a user-facing message
4. If `on_error()` modifies state, those mutations are flushed normally
5. If `on_error()` does not send a custom message, the framework sends: `{"type": "error", "message": "..."}`
6. Client shows non-intrusive notification (configurable via `Pyrox.onError` callback in JS)

---

## Security

| Threat | Mitigation |
|--------|------------|
| Fabricated event node_ids | Server validates node_id exists in component's element tree |
| Fabricated event types | Server validates event type is registered for that node |
| XSS via state values | MutationCompiler HTML-escapes all text content by default |
| Session hijacking | Session IDs are `secrets.token_urlsafe()` |
| DoS via rapid events | Server-side rate limiting per session: max events/sec (default 60) and max input messages/sec (default 120), configurable per-app |
| Large payloads | Max WebSocket message size enforced (default 64KB) |

Explicit opt-in for raw HTML:
```python
H1().raw_html(lambda: self.trusted_content)  # No escaping — developer's responsibility
```

---

## Testing

### No Browser Needed

```python
from pyrox.testing import MockSession

async def test_counter_increment():
    session = MockSession()
    counter = Counter()
    await session.mount(counter)

    assert "Count: 0" in session.last_mount_html

    await session.fire("click", node_id=counter._element_tree.find("button").node_id)

    assert session.last_mutations == [
        {"op": "text", "id": "c0-n1", "value": "Count: 1"}
    ]

async def test_reconnection():
    session = MockSession()
    counter = Counter(count=5)
    await session.mount(counter)

    await session.disconnect()
    assert session.in_grace_period
    await session.reconnect()

    assert "Count: 5" in session.last_mount_html
```

`MockSession` replaces the WebSocket with an in-memory message buffer — fast, no infrastructure.

---

## Target Use Cases

- **Internal tools & dashboards** — admin panels, monitoring, data-heavy apps
- **Small-to-medium web apps** — forms, CRUD, real-time features
- **Prototyping** — go from idea to interactive web app in pure Python, fast

## Non-Goals (for v1)

- Client-side routing (server handles all navigation)
- Offline support (server is source of truth)
- SSR/SEO optimization (initial render is server-side, but not crawlable without JS)
- Redis/DB session stores (interface ready, implementation deferred)
- Pre-built component library (deferred to post-v1)
