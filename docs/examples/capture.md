---
title: Screenshots and Recording
---

# Screenshots and Recording

The capture example saves a PNG screenshot and records five seconds of the
animated browser viewport to a silent H.264 MP4. Neither output includes the
native title bar, window border, cursor, or native menus.

## Run the Example

Install FFmpeg with `libx264`, make sure `ffmpeg` is available on `PATH`, then
run:

```bash
cd pytonium_examples/pytonium_example_capture
python main.py
```

The example writes these files beside `main.py`:

- `capture.png`
- `capture.mp4`

It uses `overwrite=True`, so running it again replaces those two outputs.

## Core Capture Code

```python
app.capture_screenshot(
    "capture.png",
    screenshot_done,
    overwrite=True,
)

app.start_recording(
    "capture.mp4",
    fps=30,
    quality=85,
    overwrite=True,
)

while app.is_running() and time.monotonic() - started < 5.0:
    app.update_message_loop()
    time.sleep(0.01)

if app.is_recording():
    app.stop_recording()
```

See the complete
[`main.py`](https://github.com/Maximilian-Winter/pytonium/blob/master/pytonium_examples/pytonium_example_capture/main.py)
and the [Screenshots and Recording guide](../guides/screenshots-recording.md)
for lifecycle, error-handling, headless, and custom FFmpeg examples.
