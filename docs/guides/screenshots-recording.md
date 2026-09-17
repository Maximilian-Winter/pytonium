# Screenshots and Recording

Pytonium can capture the rendered browser viewport in every browser mode:
normal windows, frameless windows, visible off-screen rendering (OSR), and
headless OSR. Capture uses Chromium's DevTools Page protocol, so the output is
the web content itself rather than a desktop or monitor capture.

The following are deliberately excluded:

- Native title bars and window borders
- The mouse cursor
- Native context menus and other operating-system overlays
- Audio

Screenshots are PNG files. Recordings are silent H.264 MP4 files produced by
FFmpeg.

---

## Requirements

Screenshots do not require additional software. Recording requires an FFmpeg
build that includes the `libx264` encoder. FFmpeg is not bundled in Pytonium
wheels.

Verify your FFmpeg installation before recording:

```bash
ffmpeg -version
ffmpeg -hide_banner -encoders
```

The encoder list must contain `libx264`. Pytonium searches for `ffmpeg` on
`PATH`; alternatively, pass an explicit executable path to `start_recording()`.

!!! important "Keep pumping the message loop"
    Screenshot results and screencast frames arrive through CEF's message loop.
    Continue calling `update_message_loop()` while capture is active. A
    screenshot callback cannot run while your code is blocking without pumping
    the loop.

---

## Capture a Screenshot

`capture_screenshot()` starts an asynchronous viewport capture and immediately
returns its positive DevTools request ID:

```python
from pathlib import Path
import time

from Pytonium import Pytonium

app = Pytonium()
app.initialize("https://example.com", 1280, 720)

result = {"done": False}

def screenshot_finished(path, error):
    result["done"] = True
    if error is not None:
        print(f"Screenshot failed: {error}")
    else:
        print(f"Screenshot saved to {path}")

request_id = app.capture_screenshot(
    str(Path.cwd() / "viewport.png"),
    screenshot_finished,
)
print(f"Started DevTools request {request_id}")

while app.is_running() and not result["done"]:
    app.update_message_loop()
    time.sleep(0.01)

app.shutdown()
```

The callback receives `(completed_path, error)`:

- On success, `completed_path` is the absolute PNG path and `error` is `None`.
- On failure, `completed_path` is `None` and `error` is an exception.

If no callback is supplied, asynchronous failures are reported with a
`RuntimeWarning`.

```python
app.capture_screenshot("viewport.png", overwrite=True)
```

Existing files are protected by default. Pass `overwrite=True` only when the
destination may be replaced. The PNG is first written to a unique temporary
file beside the destination and then moved into place atomically.

---

## Record the Viewport

Start recording after the browser is initialized, keep pumping the message
loop, and explicitly stop the recording when finished:

```python
import time
from Pytonium import Pytonium

app = Pytonium()
app.initialize("https://example.com", 1280, 720)

try:
    app.start_recording(
        "demo.mp4",
        fps=30,
        quality=85,
        overwrite=True,
    )

    deadline = time.monotonic() + 10.0
    while app.is_running() and time.monotonic() < deadline:
        app.update_message_loop()
        time.sleep(0.01)

    if app.is_recording():
        completed_path = app.stop_recording()
        print(f"Recording saved to {completed_path}")
finally:
    app.shutdown()
```

To use an FFmpeg executable that is not on `PATH`:

```python
app.start_recording(
    "demo.mp4",
    ffmpeg_path=r"C:\tools\ffmpeg.exe",
)
```

### Recording behavior

- `fps` must be between 1 and 60.
- `quality` must be between 1 and 100. It controls the JPEG frames transferred
  from Chromium; the MP4 is encoded separately with H.264 CRF 23.
- The first frame fixes the output dimensions for the recording session.
- If the browser is resized, later frames are scaled and letterboxed to those
  original dimensions.
- Pytonium stores only the newest Chromium frame. A background sampler sends
  the newest available frame to FFmpeg at the requested constant frame rate.
  Static pages therefore retain the correct real-time duration.
- H.264 uses `yuv420p` and has no alpha channel. Transparent content is rendered
  against black.
- The MP4 contains no audio stream and is finalized with `faststart` metadata.

The destination is not exposed until FFmpeg exits successfully. Pytonium writes
to a unique temporary MP4 beside the requested destination and atomically moves
it into place after finalization. Partial files are removed after errors and
timeouts.

---

## Closing While Recording

`close_browser()`, `close_window()`, and `shutdown()` automatically finalize an
active recording. Explicitly calling `stop_recording()` is still recommended:
it returns the completed path and reports FFmpeg failures directly to your
code.

```python
if app.is_recording():
    try:
        path = app.stop_recording(timeout=30.0)
    except (RuntimeError, TimeoutError) as error:
        print(f"Could not finalize recording: {error}")
```

Calling `stop_recording()` when no recording is active raises `RuntimeError`.
Only one recording can be active for a browser at a time.

---

## Headless and OSR Capture

The same screenshot and recording methods work in OSR and headless mode. You do
not need to copy or encode the BGRA paint buffer yourself:

```python
import time
from Pytonium import Pytonium

app = Pytonium()
app.set_headless_mode(True)
app.initialize("https://example.com", 960, 540)

app.start_recording("headless.mp4", fps=24)
deadline = time.monotonic() + 5.0

while app.is_running() and time.monotonic() < deadline:
    app.update_message_loop()
    time.sleep(0.01)

app.stop_recording()
app.shutdown()
```

| Browser mode | Content captured | Native chrome captured |
|---|---|---|
| Normal | Browser viewport | No |
| Frameless | Browser viewport | No |
| Visible OSR | OSR browser surface | No |
| Headless OSR | Headless browser surface | No |

---

## Error Reference

Immediate validation failures are raised directly from the capture call.

| Condition | Exception |
|---|---|
| Browser has not been initialized | `RuntimeError` |
| Wrong output extension | `ValueError` |
| Output directory does not exist | `FileNotFoundError` |
| Destination already exists | `FileExistsError` |
| Screenshot callback is not callable | `TypeError` |
| FPS is outside 1–60 | `ValueError` |
| JPEG quality is outside 1–100 | `ValueError` |
| FFmpeg cannot be found | `FileNotFoundError` |
| FFmpeg does not provide `libx264` | `RuntimeError` |
| A recording is already active | `RuntimeError` |
| No recording is active when stopping | `RuntimeError` |
| FFmpeg cannot finalize in time | `TimeoutError` |

Protocol-level screenshot failures are delivered to the screenshot callback.
Recording failures are raised when `stop_recording()` finalizes the session.

---

## Troubleshooting

### The screenshot callback never runs

Ensure that `update_message_loop()` continues to run after
`capture_screenshot()`. Do not wait on a blocking event from the same thread
without pumping CEF.

### FFmpeg was not found

Run `ffmpeg -version` from the same terminal that launches the application. If
that fails, add FFmpeg to `PATH` or pass `ffmpeg_path` explicitly.

### `libx264` is missing

The selected FFmpeg build does not include the required H.264 encoder. Install
a build containing `libx264` and verify it with `ffmpeg -hide_banner -encoders`.

### The recording resolution does not change after resizing

This is intentional. The first screencast frame fixes the MP4 dimensions;
later sizes are scaled and letterboxed so FFmpeg receives a stable video
stream.

### The MP4 is absent after a failure

Pytonium publishes the destination only after successful FFmpeg finalization.
Failed or timed-out sessions remove their partial temporary files.

See the [`Pytonium` API reference](../api/pytonium.md#screenshots-recording)
for exact method signatures, or run the
[`pytonium_example_capture`](https://github.com/Maximilian-Winter/pytonium/tree/master/pytonium_examples/pytonium_example_capture)
example.
