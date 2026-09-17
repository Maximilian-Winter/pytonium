import importlib.util
from pathlib import Path
import shutil
import subprocess
import time

import pytest


CAPTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "pytonium_python_framework"
    / "Pytonium"
    / "capture.py"
)


def _load_capture_module():
    spec = importlib.util.spec_from_file_location("pytonium_capture", CAPTURE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_prepare_output_path_validates_extension_and_existing_file(tmp_path):
    capture = _load_capture_module()
    with pytest.raises(ValueError, match=".png"):
        capture.prepare_output_path(tmp_path / "capture.jpg", ".png", False)

    existing = tmp_path / "capture.png"
    existing.write_bytes(b"old")
    with pytest.raises(FileExistsError):
        capture.prepare_output_path(existing, ".png", False)
    assert capture.prepare_output_path(existing, ".png", True) == str(existing)


def test_write_png_atomic_validates_data_and_overwrite(tmp_path):
    capture = _load_capture_module()
    output = tmp_path / "capture.png"
    png = capture.PNG_SIGNATURE + b"test-data"

    assert capture.write_png_atomic(str(output), png, False) == str(output)
    assert output.read_bytes() == png
    with pytest.raises(FileExistsError):
        capture.write_png_atomic(str(output), png, False)
    with pytest.raises(RuntimeError, match="invalid PNG"):
        capture.write_png_atomic(str(tmp_path / "bad.png"), b"bad", False)


def test_recording_session_creates_constant_rate_h264_mp4(tmp_path):
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        pytest.skip("FFmpeg tools are not installed")

    encoders = subprocess.run(
        [ffmpeg, "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        check=False,
    )
    if "libx264" not in encoders.stdout:
        pytest.skip("FFmpeg does not provide libx264")

    frame = tmp_path / "frame.jpg"
    resized_frame = tmp_path / "resized-frame.jpg"
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "color=c=blue:s=320x240",
            "-frames:v", "1", str(frame),
        ],
        check=True,
    )
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "color=c=red:s=640x360",
            "-frames:v", "1", str(resized_frame),
        ],
        check=True,
    )

    capture = _load_capture_module()
    output = tmp_path / "recording.mp4"
    session = capture.RecordingSession(
        output,
        fps=10,
        quality=85,
        ffmpeg_path=ffmpeg,
        overwrite=False,
    )
    session.start()
    session.push_frame(frame.read_bytes(), 320, 240)
    time.sleep(0.25)
    # The output resolution remains locked to the first frame. FFmpeg scales
    # and letterboxes later frames when the browser viewport is resized.
    session.push_frame(resized_frame.read_bytes(), 640, 360)
    time.sleep(0.3)
    assert session.finish() == str(output)

    probe = subprocess.run(
        [
            ffprobe,
            "-v", "error",
            "-show_entries", "stream=codec_name,codec_type,width,height",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "codec_name=h264" in probe
    assert "codec_type=audio" not in probe
    assert "width=320" in probe
    assert "height=240" in probe
    duration_line = next(
        line for line in probe.splitlines() if line.startswith("duration=")
    )
    assert 0.4 <= float(duration_line.split("=", 1)[1]) <= 0.8


@pytest.mark.parametrize("fps", [0, 61, 1.5, True])
def test_recording_session_rejects_invalid_fps(tmp_path, fps):
    capture = _load_capture_module()
    with pytest.raises(ValueError, match="fps"):
        capture.RecordingSession(
            tmp_path / "recording.mp4",
            fps=fps,
            quality=85,
            ffmpeg_path=None,
            overwrite=False,
        )


@pytest.mark.parametrize("quality", [0, 101, 2.5, False])
def test_recording_session_rejects_invalid_quality(tmp_path, quality):
    capture = _load_capture_module()
    with pytest.raises(ValueError, match="quality"):
        capture.RecordingSession(
            tmp_path / "recording.mp4",
            fps=30,
            quality=quality,
            ffmpeg_path=None,
            overwrite=False,
        )


def test_recording_session_reports_missing_ffmpeg(tmp_path):
    capture = _load_capture_module()
    with pytest.raises(FileNotFoundError, match="FFmpeg"):
        capture.RecordingSession(
            tmp_path / "recording.mp4",
            fps=30,
            quality=85,
            ffmpeg_path=tmp_path / "missing-ffmpeg",
            overwrite=False,
        )


def test_installed_api_rejects_capture_before_initialization():
    try:
        from Pytonium import Pytonium
    except ImportError:
        pytest.skip("Pytonium wheel is not installed in this test environment")

    app = Pytonium()
    assert app.is_recording() is False
    with pytest.raises(RuntimeError, match="initialized browser"):
        app.capture_screenshot("capture.png")
    with pytest.raises(RuntimeError, match="initialized browser"):
        app.start_recording("capture.mp4")
    with pytest.raises(RuntimeError, match="No recording"):
        app.stop_recording()


def test_installed_api_exposes_capture_methods():
    try:
        from Pytonium import Pytonium
    except ImportError:
        pytest.skip("Pytonium wheel is not installed in this test environment")

    for name in (
        "capture_screenshot",
        "start_recording",
        "stop_recording",
        "is_recording",
    ):
        assert callable(getattr(Pytonium, name))
