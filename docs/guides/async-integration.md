# Async Integration

Pytonium's browser window requires a message loop to process events (rendering,
user input, JavaScript execution).  You can drive this loop manually with a
`while` loop, or use Pytonium's built-in async helpers to integrate with
Python's `asyncio`.

---

## Traditional Loop

The simplest approach is a blocking `while` loop:

```python
import time
from Pytonium import Pytonium

p = Pytonium()
p.initialize("https://example.com", 800, 600)

while p.is_running():
    p.update_message_loop()
    time.sleep(0.016)  # ~60fps

p.shutdown()
```

This works well for simple applications, but blocks the main thread -- you
cannot run other async tasks alongside it.

---

## Single Instance Async

`run_pytonium_async()` wraps the message loop as an `asyncio` coroutine:

```python
import asyncio
from Pytonium import Pytonium, run_pytonium_async

p = Pytonium()
p.initialize("https://example.com", 800, 600)

asyncio.run(run_pytonium_async(p))
p.shutdown()
```

| Parameter   | Type       | Default  | Description                                        |
|-------------|------------|----------|----------------------------------------------------|
| `pytonium`  | `Pytonium` | *(required)* | An initialized Pytonium instance.              |
| `interval`  | `float`    | `0.016`  | Seconds between message loop updates (~60fps).     |

The coroutine runs until `p.is_running()` returns `False` (i.e., the user
closes the window).

---

## Multi-Instance Async

`run_pytonium_multi_async()` handles multiple browser windows in a single async
loop:

```python
import asyncio
from Pytonium import Pytonium, run_pytonium_multi_async

p1 = Pytonium()
p1.initialize("https://example.com", 800, 600)

p2 = Pytonium()
p2.create_browser("https://example.org", 600, 400)

asyncio.run(run_pytonium_multi_async([p1, p2]))
p1.shutdown()
```

| Parameter   | Type              | Default  | Description                                      |
|-------------|-------------------|----------|--------------------------------------------------|
| `instances` | `list[Pytonium]`  | *(required)* | A list of initialized Pytonium instances.    |
| `interval`  | `float`           | `0.016`  | Seconds between message loop updates (~60fps).   |

!!! note "Global message loop"
    CEF's message loop is global.  `run_pytonium_multi_async` calls
    `update_message_loop()` on the first instance in the list, which processes
    events for **all** browser windows.  The coroutine runs until **all**
    instances stop running.

---

## Combining with Background Tasks

The real power of async integration is running Pytonium alongside other
coroutines using `asyncio.gather()`:

```python
import asyncio
import time
from Pytonium import Pytonium, run_pytonium_async

async def periodic_update(p):
    """Push data to the browser every second."""
    counter = 0
    while p.is_running():
        counter += 1
        p.set_state("app", "counter", counter)
        p.set_state("app", "timestamp", time.time())
        await asyncio.sleep(1.0)

async def main():
    p = Pytonium()
    p.initialize("https://example.com", 800, 600)

    await asyncio.gather(
        run_pytonium_async(p),
        periodic_update(p),
    )

    p.shutdown()

asyncio.run(main())
```

!!! tip "Task cancellation"
    When the browser window closes, `run_pytonium_async` returns.
    `asyncio.gather` then waits for remaining tasks.  Check `p.is_running()`
    in your background coroutines to exit cleanly.

---

## Controlling the Frame Rate

The `interval` parameter controls how frequently the message loop is polled:

| Interval   | Approximate FPS | Use Case                       |
|------------|-----------------|--------------------------------|
| `0.033`    | ~30fps          | Low-power / background apps    |
| `0.016`    | ~60fps          | Standard (default)             |
| `0.008`    | ~120fps         | High refresh rate displays     |
| `0.004`    | ~240fps         | Smoothest possible             |

```python
# Run at ~30fps to save CPU
asyncio.run(run_pytonium_async(p, interval=0.033))

# Run at ~120fps for smoother animations
asyncio.run(run_pytonium_async(p, interval=0.008))
```

!!! note "CPU usage"
    Lower intervals mean more CPU usage.  For most desktop applications,
    the default `0.016` (60fps) is a good balance between responsiveness
    and efficiency.

---

## Complete Example: Dashboard with Live Data

=== "Python (main.py)"

    ```python
    import asyncio
    import time
    import random
    from Pytonium import Pytonium, run_pytonium_async, returns_value_to_javascript

    async def system_monitor(p):
        """Simulate system monitoring data."""
        while p.is_running():
            p.set_state("system", "cpu", round(random.uniform(5, 95), 1))
            p.set_state("system", "memory", round(random.uniform(30, 90), 1))
            p.set_state("system", "uptime", round(time.time() % 86400))
            await asyncio.sleep(2.0)

    async def notification_service(p):
        """Check for notifications periodically."""
        messages = [
            "System running normally",
            "Backup completed",
            "Update available",
        ]
        idx = 0
        while p.is_running():
            p.set_state("notifications", "latest", messages[idx % len(messages)])
            idx += 1
            await asyncio.sleep(10.0)

    async def main():
        p = Pytonium()

        @returns_value_to_javascript("string")
        def get_version():
            return "1.0.0"

        p.bind_function_to_javascript(get_version, javascript_object="app")
        p.add_custom_scheme("app", "./web/")
        p.initialize("app://dashboard.html", 1024, 768)

        await asyncio.gather(
            run_pytonium_async(p),
            system_monitor(p),
            notification_service(p),
        )

        p.shutdown()

    asyncio.run(main())
    ```

=== "JavaScript (web/dashboard.html)"

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard</title>
        <style>
            body { font-family: sans-serif; background: #1a1a2e; color: #eee; padding: 2rem; }
            .metric { font-size: 2rem; margin: 1rem 0; }
            .label { font-size: 0.9rem; opacity: 0.6; }
        </style>
    </head>
    <body>
        <h1>System Dashboard</h1>
        <div class="metric"><span class="label">CPU</span><br><span id="cpu">--</span>%</div>
        <div class="metric"><span class="label">Memory</span><br><span id="mem">--</span>%</div>
        <div class="metric"><span class="label">Notification</span><br><span id="notif">--</span></div>

        <script>
            function onReady() {
                Pytonium.appState.registerForStateUpdates("sysUpdate", ["system"], false, true);
                Pytonium.appState.registerForStateUpdates("notifUpdate", ["notifications"], false, true);

                window.addEventListener("sysUpdate", (e) => {
                    if (e.detail.key === "cpu") document.getElementById("cpu").textContent = e.detail.value;
                    if (e.detail.key === "memory") document.getElementById("mem").textContent = e.detail.value;
                });

                window.addEventListener("notifUpdate", (e) => {
                    if (e.detail.key === "latest") document.getElementById("notif").textContent = e.detail.value;
                });
            }

            if (window.PytoniumReady) onReady();
            else window.addEventListener("PytoniumReady", onReady);
        </script>
    </body>
    </html>
    ```

---

## Import Reference

```python
from Pytonium import Pytonium, run_pytonium_async, run_pytonium_multi_async
```

Both async helpers are exported from the `Pytonium` package `__init__.py`.
