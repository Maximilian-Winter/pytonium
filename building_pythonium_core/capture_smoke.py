"""Manual end-to-end smoke test for browser-content capture.

Run after installing a freshly built wheel::

    python building_pythonium_core/capture_smoke.py

The test intentionally uses headless OSR so it does not capture or create any
native window chrome. FFmpeg must be available on PATH.
"""

from __future__ import annotations

import shutil
import struct
import sys
import tempfile
import time
from pathlib import Path


def _pump(app, seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while app.is_running() and time.monotonic() < deadline:
        app.update_message_loop()
        time.sleep(0.005)


def main() -> int:
    from Pytonium import Pytonium

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        print("FAIL: FFmpeg is not available on PATH")
        return 1

    paint_frames = 0

    def on_paint(_buffer, _width, _height):
        nonlocal paint_frames
        paint_frames += 1

    app = Pytonium()
    shutdown_complete = False
    app.set_headless_mode(True)
    # Deliberately registered before initialize(): this covers the regression
    # where the callback was previously discarded before OsrWindowHeadless
    # existed.
    app.on_paint(on_paint)

    html = (
        "data:text/html,"
        "<style>html,body{margin:0;width:100%;height:100%;overflow:hidden}"
        "body{background:%23131a2a;color:white;display:grid;place-items:center}"
        ".dot{width:80px;height:80px;border-radius:50%;background:%234fc3f7;"
        "animation:move 1s ease-in-out infinite alternate}"
        "@keyframes move{to{transform:translateX(180px);background:%23ff4081}}"
        "</style><div><h1>Pytonium capture</h1><div class='dot'></div></div>"
    )

    try:
        app.initialize(html, 640, 360)
        _pump(app, 0.75)
        if paint_frames == 0:
            raise AssertionError("pre-initialize on_paint callback received no frames")

        with tempfile.TemporaryDirectory(prefix="pytonium-capture-") as temp:
            output = Path(temp)
            screenshot = output / "viewport.png"
            recording = output / "viewport.mp4"
            screenshot_result = []

            app.capture_screenshot(
                str(screenshot),
                lambda path, error: screenshot_result.append((path, error)),
            )
            deadline = time.monotonic() + 5.0
            while not screenshot_result and time.monotonic() < deadline:
                app.update_message_loop()
                time.sleep(0.005)

            if not screenshot_result:
                raise TimeoutError("screenshot callback did not run")
            if screenshot_result[0][1] is not None:
                raise screenshot_result[0][1]
            png = screenshot.read_bytes()
            if not png.startswith(b"\x89PNG\r\n\x1a\n"):
                raise AssertionError("invalid PNG signature")
            width, height = struct.unpack(">II", png[16:24])
            if (width, height) != (640, 360):
                raise AssertionError(f"unexpected PNG size: {width}x{height}")

            app.start_recording(str(recording), fps=20, ffmpeg_path=ffmpeg)
            _pump(app, 1.25)
            completed = app.stop_recording()
            if Path(completed) != recording or recording.stat().st_size == 0:
                raise AssertionError("recording was not finalized")

            # Closing a browser must also finalize an active recording.
            close_recording = output / "closed-browser.mp4"
            app.start_recording(str(close_recording), fps=20, ffmpeg_path=ffmpeg)
            _pump(app, 0.5)
            app.close_browser()
            if close_recording.stat().st_size == 0:
                raise AssertionError("browser close did not finalize recording")

            print(
                f"PASS: {paint_frames} paint frames, PNG {width}x{height}, "
                f"MP4 {recording.stat().st_size} bytes, close-finalize OK"
            )
            app.shutdown()
            shutdown_complete = True
        return 0
    finally:
        if not shutdown_complete:
            app.shutdown()


if __name__ == "__main__":
    sys.exit(main())
