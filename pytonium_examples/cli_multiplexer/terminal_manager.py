"""Terminal session manager for Pytonium-based terminal multiplexer.

Adapted from Agora's terminal_service.py.  Instead of WebSocket I/O,
sessions push output through Pytonium's state system and receive input
via bound Python functions called from JavaScript.

Platform support:
  - Unix:    Full PTY via stdlib ``pty`` (interactive, colors, resize)
  - Windows: subprocess.Popen pipe fallback (local echo on client side)
"""

import asyncio
import logging
import os
import platform
import subprocess
import struct
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from Pytonium import Pytonium

logger = logging.getLogger("termux.terminal")

_SYSTEM = platform.system()

# Unix PTY support
if _SYSTEM != "Windows":
    import fcntl
    import pty
    import termios
    HAS_PTY = True
else:
    HAS_PTY = False


@dataclass
class TerminalSession:
    id: str
    working_dir: str
    created_at: datetime
    shell: str
    mode: str  # "pty" or "pipe"
    status: str = "running"
    cols: int = 80
    rows: int = 24
    _output_buffer: list = field(default_factory=list, repr=False)
    _buffer_lock: threading.Lock = field(
        default_factory=threading.Lock, repr=False
    )
    _process: Optional[subprocess.Popen] = field(default=None, repr=False)
    _master_fd: Optional[int] = field(default=None, repr=False)
    _reader_thread: Optional[threading.Thread] = field(default=None, repr=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "working_dir": self.working_dir,
            "shell": self.shell,
            "mode": self.mode,
            "cols": self.cols,
            "rows": self.rows,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
        }


class TerminalManager:
    """Manages terminal sessions with platform-aware PTY/pipe support.

    Output is buffered in each session and polled by the Pytonium main
    loop, which pushes it to the browser via execute_javascript().
    """

    def __init__(self):
        self._sessions: dict[str, TerminalSession] = {}

    # ── Session creation ─────────────────────────────────────

    def create_session(
        self, working_dir: str, cols: int = 80, rows: int = 24
    ) -> TerminalSession:
        path = Path(working_dir)
        if not path.exists() or not path.is_dir():
            raise ValueError(f"Invalid working directory: {working_dir}")

        session_id = uuid.uuid4().hex[:8]

        if HAS_PTY:
            session = self._create_unix_pty(session_id, working_dir, cols, rows)
        else:
            session = self._create_pipe_fallback(session_id, working_dir, cols, rows)

        self._sessions[session_id] = session
        logger.info(
            "Terminal %s created: mode=%s shell=%s cwd=%s",
            session_id, session.mode, session.shell, working_dir,
        )
        return session

    def _create_unix_pty(
        self, session_id: str, working_dir: str, cols: int, rows: int
    ) -> TerminalSession:
        shell = os.environ.get("SHELL", "/bin/bash")
        master_fd, slave_fd = pty.openpty()

        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)

        env = os.environ.copy()
        env["TERM"] = "xterm-256color"
        env["COLORTERM"] = "truecolor"

        process = subprocess.Popen(
            [shell, "-l"],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=working_dir,
            env=env,
            preexec_fn=os.setsid,
        )
        os.close(slave_fd)

        session = TerminalSession(
            id=session_id,
            working_dir=working_dir,
            created_at=datetime.now(timezone.utc),
            shell=shell,
            mode="pty",
            cols=cols,
            rows=rows,
            _process=process,
            _master_fd=master_fd,
        )

        reader = threading.Thread(
            target=self._read_fd_thread,
            args=(master_fd, session),
            name=f"pty-reader-{session_id}",
            daemon=True,
        )
        reader.start()
        session._reader_thread = reader
        return session

    def _create_pipe_fallback(
        self, session_id: str, working_dir: str, cols: int, rows: int
    ) -> TerminalSession:
        if _SYSTEM == "Windows":
            shell = os.environ.get("COMSPEC", "cmd.exe")
            args = [shell]
        else:
            shell = os.environ.get("SHELL", "/bin/bash")
            args = [shell, "-i"]

        env = os.environ.copy()
        env["TERM"] = "xterm-256color"

        process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=working_dir,
            env=env,
            bufsize=0,
        )

        session = TerminalSession(
            id=session_id,
            working_dir=working_dir,
            created_at=datetime.now(timezone.utc),
            shell=shell,
            mode="pipe",
            cols=cols,
            rows=rows,
            _process=process,
        )

        reader = threading.Thread(
            target=self._read_pipe_thread,
            args=(process, session),
            name=f"pipe-reader-{session_id}",
            daemon=True,
        )
        reader.start()
        session._reader_thread = reader
        return session

    # ── Reader threads ────────────────────────────────────────

    def _read_fd_thread(self, fd: int, session: TerminalSession):
        """Background thread: blocking read from PTY master fd."""
        try:
            while session.status == "running":
                try:
                    data = os.read(fd, 4096)
                    if not data:
                        break
                    with session._buffer_lock:
                        session._output_buffer.append(data)
                except OSError:
                    break
        except Exception as exc:
            logger.debug("PTY reader error: %s", exc)
        finally:
            session.status = "exited"

    def _read_pipe_thread(
        self, process: subprocess.Popen, session: TerminalSession
    ):
        """Background thread: blocking read from subprocess stdout pipe."""
        try:
            stdout = process.stdout
            if stdout is None:
                return
            while session.status == "running":
                try:
                    data = stdout.read(4096)
                except (OSError, ValueError):
                    break
                if not data:
                    break
                with session._buffer_lock:
                    session._output_buffer.append(data)
        except Exception as exc:
            logger.error("Pipe reader exception: %s", exc, exc_info=True)
        finally:
            session.status = "exited"

    # ── I/O ──────────────────────────────────────────────────

    def write(self, session_id: str, data: bytes) -> bool:
        """Write raw bytes to a terminal session's stdin."""
        session = self._sessions.get(session_id)
        if not session or session.status != "running":
            return False
        proc = session._process
        if proc is None:
            return False
        try:
            if session.mode == "pty" and session._master_fd is not None:
                os.write(session._master_fd, data)
            elif proc.stdin is not None:
                proc.stdin.write(data)
                proc.stdin.flush()
            else:
                return False
            return True
        except (OSError, BrokenPipeError, ValueError):
            session.status = "exited"
            return False

    def drain_output(self, session_id: str) -> bytes:
        """Drain and return all buffered output for a session.

        Called from the Pytonium main loop to collect output and push
        it to the browser via execute_javascript().
        """
        session = self._sessions.get(session_id)
        if not session:
            return b""
        with session._buffer_lock:
            if not session._output_buffer:
                return b""
            combined = b"".join(session._output_buffer)
            session._output_buffer.clear()
            return combined

    def resize(self, session_id: str, cols: int, rows: int) -> bool:
        session = self._sessions.get(session_id)
        if not session or session.status != "running":
            return False
        session.cols = cols
        session.rows = rows
        if session.mode == "pty" and session._master_fd is not None:
            try:
                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                fcntl.ioctl(session._master_fd, termios.TIOCSWINSZ, winsize)
                return True
            except OSError:
                pass
        return False

    # ── Session management ───────────────────────────────────

    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[dict]:
        for session in self._sessions.values():
            if session.status == "running" and session._process is not None:
                rc = session._process.poll()
                if rc is not None:
                    session.status = f"exited ({rc})"
        return [s.to_dict() for s in self._sessions.values()]

    def kill_session(self, session_id: str) -> bool:
        session = self._sessions.pop(session_id, None)
        if not session:
            return False
        session.status = "exited"
        if session._process is not None:
            try:
                session._process.terminate()
            except (OSError, ProcessLookupError):
                pass
        if session._master_fd is not None:
            try:
                os.close(session._master_fd)
            except OSError:
                pass
        logger.info("Terminal %s killed", session_id)
        return True

    def cleanup(self):
        """Kill all sessions (for shutdown)."""
        for sid in list(self._sessions.keys()):
            self.kill_session(sid)


# Module-level singleton
terminal_manager = TerminalManager()
