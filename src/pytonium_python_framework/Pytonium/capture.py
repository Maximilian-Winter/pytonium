"""Browser-content capture helpers used by the Cython Pytonium wrapper."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
import uuid
from typing import Optional


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def prepare_output_path(path, suffix: str, overwrite: bool) -> str:
    output = Path(os.fspath(path)).expanduser().resolve()
    if output.suffix.lower() != suffix:
        raise ValueError(f"Capture output must use the {suffix} extension")
    if not output.parent.exists():
        raise FileNotFoundError(f"Output directory does not exist: {output.parent}")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists: {output}")
    return str(output)


def write_png_atomic(path: str, data: bytes, overwrite: bool) -> str:
    if not data.startswith(PNG_SIGNATURE):
        raise RuntimeError("CEF returned invalid PNG screenshot data")

    output = Path(path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists: {output}")

    temporary = output.with_name(
        f".{output.stem}.{uuid.uuid4().hex}.part{output.suffix}"
    )
    try:
        temporary.write_bytes(data)
        if output.exists() and not overwrite:
            raise FileExistsError(f"Output file already exists: {output}")
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return str(output)


def _jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Read JPEG dimensions without adding an image-library dependency."""
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return 0, 0

    index = 2
    while index + 3 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        index += 2
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        if index + 2 > len(data):
            break
        segment_length = int.from_bytes(data[index:index + 2], "big")
        if segment_length < 2 or index + segment_length > len(data):
            break
        if marker in {
            0xC0, 0xC1, 0xC2, 0xC3,
            0xC5, 0xC6, 0xC7,
            0xC9, 0xCA, 0xCB,
            0xCD, 0xCE, 0xCF,
        } and segment_length >= 7:
            height = int.from_bytes(data[index + 3:index + 5], "big")
            width = int.from_bytes(data[index + 5:index + 7], "big")
            return width, height
        index += segment_length
    return 0, 0


def _resolve_ffmpeg(ffmpeg_path: Optional[str]) -> str:
    if ffmpeg_path:
        candidate = os.fspath(ffmpeg_path)
        resolved = shutil.which(candidate)
        if resolved is None and Path(candidate).is_file():
            resolved = str(Path(candidate).resolve())
    else:
        resolved = shutil.which("ffmpeg")

    if resolved is None:
        raise FileNotFoundError(
            "FFmpeg was not found. Install it on PATH or pass ffmpeg_path."
        )

    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        probe = subprocess.run(
            [resolved, "-hide_banner", "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
            check=False,
            creationflags=creation_flags,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"Unable to execute FFmpeg: {exc}") from exc

    if probe.returncode != 0:
        detail = probe.stderr.strip() or f"exit code {probe.returncode}"
        raise RuntimeError(f"Unable to query FFmpeg encoders: {detail}")
    if "libx264" not in probe.stdout:
        raise RuntimeError("The selected FFmpeg build does not provide libx264")
    return resolved


class RecordingSession:
    """Resample the latest CEF JPEG frame into a constant-rate MP4 stream."""

    def __init__(
        self,
        path,
        *,
        fps: int,
        quality: int,
        ffmpeg_path: Optional[str],
        overwrite: bool,
    ) -> None:
        if not isinstance(fps, int) or isinstance(fps, bool) or not 1 <= fps <= 60:
            raise ValueError("fps must be an integer between 1 and 60")
        if (
            not isinstance(quality, int)
            or isinstance(quality, bool)
            or not 1 <= quality <= 100
        ):
            raise ValueError("quality must be an integer between 1 and 100")

        self.path = prepare_output_path(path, ".mp4", overwrite)
        self.fps = fps
        self.quality = quality
        self.overwrite = overwrite
        self.ffmpeg_path = _resolve_ffmpeg(ffmpeg_path)

        output = Path(self.path)
        token = uuid.uuid4().hex
        self._temporary_path = output.with_name(
            f".{output.stem}.{token}.part{output.suffix}"
        )
        self._log_path = output.with_name(f".{output.stem}.{token}.ffmpeg.log")

        self._condition = threading.Condition()
        self._latest_frame: Optional[bytes] = None
        self._width = 0
        self._height = 0
        self._stop_requested = False
        self._error: Optional[BaseException] = None
        self._process: Optional[subprocess.Popen] = None
        self._thread = threading.Thread(
            target=self._writer_main,
            name="PytoniumFFmpegRecorder",
            daemon=True,
        )
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._thread.start()

    def push_frame(self, data: bytes, width: int, height: int) -> None:
        with self._condition:
            if self._stop_requested:
                return
            if width <= 0 or height <= 0:
                width, height = _jpeg_dimensions(data)
            if width <= 0 or height <= 0:
                self._error = RuntimeError(
                    "Unable to determine screencast frame dimensions"
                )
                self._stop_requested = True
            else:
                self._latest_frame = data
                if self._width == 0:
                    self._width = width
                    self._height = height
            self._condition.notify_all()

    def fail(self, message: str) -> None:
        with self._condition:
            if self._error is None:
                self._error = RuntimeError(message)
            self._stop_requested = True
            self._condition.notify_all()

    @property
    def is_recording(self) -> bool:
        with self._condition:
            return self._started and not self._stop_requested

    def finish(self, timeout: float = 30.0) -> str:
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        with self._condition:
            self._stop_requested = True
            self._condition.notify_all()

        self._thread.join(timeout)
        if self._thread.is_alive():
            self._terminate_process()
            self._thread.join(5.0)
            self._cleanup()
            raise TimeoutError("Timed out while finalizing the FFmpeg recording")

        if self._error is not None:
            error = self._error
            self._cleanup()
            raise error
        if not self._temporary_path.exists():
            self._cleanup()
            raise RuntimeError("Recording stopped before any frames were captured")

        output = Path(self.path)
        if output.exists() and not self.overwrite:
            self._cleanup()
            raise FileExistsError(f"Output file already exists: {output}")
        os.replace(self._temporary_path, output)
        self._log_path.unlink(missing_ok=True)
        return str(output)

    def abort(self) -> None:
        with self._condition:
            self._stop_requested = True
            self._condition.notify_all()
        if self._started:
            self._thread.join(2.0)
        self._terminate_process()
        if self._started and self._thread.is_alive():
            self._thread.join(3.0)
        self._cleanup()

    def _writer_main(self) -> None:
        log_file = None
        try:
            with self._condition:
                self._condition.wait_for(
                    lambda: self._latest_frame is not None
                    or self._stop_requested
                    or self._error is not None
                )
                if self._latest_frame is None:
                    return
                width = max(2, self._width - (self._width % 2))
                height = max(2, self._height - (self._height % 2))

            filter_graph = (
                f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
            )
            command = [
                self.ffmpeg_path,
                "-hide_banner",
                "-loglevel", "error",
                "-y",
                "-framerate", str(self.fps),
                "-f", "image2pipe",
                "-vcodec", "mjpeg",
                "-i", "pipe:0",
                "-vf", filter_graph,
                "-an",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(self._temporary_path),
            ]
            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            log_file = self._log_path.open("wb")
            self._process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=log_file,
                bufsize=0,
                creationflags=creation_flags,
            )

            start_time = time.monotonic()
            frames_written = 0
            while True:
                with self._condition:
                    now = time.monotonic()
                    target_frames = max(
                        1, int((now - start_time) * self.fps) + 1
                    )
                    frame = self._latest_frame
                    stopping = self._stop_requested or self._error is not None

                while frames_written < target_frames:
                    if self._process.stdin is None or frame is None:
                        raise RuntimeError("FFmpeg input pipe is unavailable")
                    self._process.stdin.write(frame)
                    frames_written += 1

                if stopping:
                    break

                next_deadline = start_time + frames_written / self.fps
                with self._condition:
                    self._condition.wait(
                        timeout=max(0.0, next_deadline - time.monotonic())
                    )

            if self._process.stdin is not None:
                self._process.stdin.close()
            return_code = self._process.wait()
            log_file.close()
            log_file = None
            if return_code != 0 and self._error is None:
                detail = self._read_log()
                self._error = RuntimeError(
                    f"FFmpeg exited with code {return_code}: {detail}"
                )
        except (BrokenPipeError, OSError, subprocess.SubprocessError) as exc:
            if self._error is None:
                self._error = RuntimeError(f"FFmpeg recording failed: {exc}")
            self._terminate_process()
        except BaseException as exc:
            if self._error is None:
                self._error = exc
            self._terminate_process()
        finally:
            if log_file is not None:
                log_file.close()

    def _terminate_process(self) -> None:
        process = self._process
        if process is None or process.poll() is not None:
            return
        try:
            process.terminate()
            process.wait(timeout=3)
        except (OSError, subprocess.SubprocessError):
            try:
                process.kill()
            except OSError:
                pass

    def _read_log(self) -> str:
        try:
            detail = self._log_path.read_text(encoding="utf-8", errors="replace")
            return detail.strip() or "no FFmpeg error output"
        except OSError:
            return "unable to read FFmpeg error output"

    def _cleanup(self) -> None:
        self._temporary_path.unlink(missing_ok=True)
        self._log_path.unlink(missing_ok=True)
