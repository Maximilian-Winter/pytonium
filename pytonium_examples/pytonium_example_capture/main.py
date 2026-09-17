"""Capture the browser viewport without native window chrome."""

from pathlib import Path
import time

from Pytonium import Pytonium


output_dir = Path(__file__).resolve().parent
app = Pytonium()
app.initialize(
    "data:text/html,<style>body{font:32px sans-serif;background:%23141b2d;"
    "color:white;display:grid;place-items:center;height:100vh;margin:0}"
    "span{animation:pulse 1s infinite alternate}@keyframes pulse{to{"
    "transform:scale(1.3);color:%2358d3ff}}</style>"
    "<span>Pytonium capture</span>",
    960,
    540,
)

# Give the page time to finish its first layout before capturing it.
ready_at = time.monotonic() + 0.5
while app.is_running() and time.monotonic() < ready_at:
    app.update_message_loop()
    time.sleep(0.01)


def screenshot_done(path, error):
    if error:
        print(f"Screenshot failed: {error}")
    else:
        print(f"Screenshot saved to {path}")


# Both operations capture only the rendered browser content. FFmpeg must be
# installed on PATH for recording (or pass ffmpeg_path=...).
app.capture_screenshot(
    str(output_dir / "capture.png"), screenshot_done, overwrite=True
)
app.start_recording(
    str(output_dir / "capture.mp4"), fps=30, quality=85, overwrite=True
)

started = time.monotonic()
while app.is_running() and time.monotonic() - started < 5.0:
    app.update_message_loop()
    time.sleep(0.01)

if app.is_recording():
    print(f"Recording saved to {app.stop_recording()}")
app.shutdown()
