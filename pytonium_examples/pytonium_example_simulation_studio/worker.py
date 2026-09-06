"""Worker owns model and disk operations. This module deliberately has no UI imports."""
import queue
import time
import uuid
from pathlib import Path

from engine import Config, DT, Flock
from storage import Library, Recording, sample


class Session:
    def __init__(self, workspace):
        self.library = Library(workspace)
        self.flock = Flock()
        self.mode, self.paused, self.speed = "live", False, 1
        self.recording = None
        self.active = []
        self.cursor = 0
        self.selected = -1
        self.generation = uuid.uuid4().hex
        self.sequence = 0
        self.history = []
        self.last_command = None

    def transition(self):
        self.generation = uuid.uuid4().hex
        self.sequence = 0

    def stop_recording(self):
        if self.recording:
            self.library.save(self.recording.finish(self.flock))
            self.recording = None

    def command(self, action, args):
        if action == "pause":
            self.paused = bool(args["paused"])
        elif action == "speed":
            if args["value"] not in (.5, 1, 2):
                raise ValueError("Choose 0.5×, 1×, or 2× speed.")
            self.speed = args["value"]
        elif action == "reset":
            config = Config(**args["config"]).validated()
            self.stop_recording()
            self.flock = Flock(config)
            self.mode, self.paused, self.active, self.history = "live", False, [], []
            self.transition()
        elif action == "configure":
            self.require_live()
            self.flock.configure(args["changes"])
            if self.recording:
                self.recording.event(self.flock, args["changes"])
        elif action == "step":
            self.require_live()
            if not self.paused:
                raise ValueError("Pause before stepping.")
            self.advance()
        elif action == "record":
            self.require_live()
            if self.recording:
                raise ValueError("A recording is already in progress.")
            self.recording = Recording(self.flock, args.get("name", "Untitled experiment"))
        elif action == "stop_recording":
            self.stop_recording()
        elif action in ("replay", "compare"):
            ids = args["ids"]
            if len(ids) != (1 if action == "replay" else 2) or len(set(ids)) != len(ids):
                raise ValueError("Choose one run for replay or two different runs for comparison.")
            loaded = [self.library.load(identifier) for identifier in ids]
            self.stop_recording()
            self.active, self.mode, self.cursor, self.paused = loaded, action, 0, True
            self.transition()
        elif action == "seek":
            if self.mode == "live":
                raise ValueError("Open a recording before seeking.")
            value = float(args["time"])
            if not 0 <= value <= self.duration:
                raise ValueError("Seek time is outside the recording.")
            self.cursor = value
        elif action == "select":
            self.selected = int(args["id"])
        elif action == "rename":
            self.library.rename(args["id"], args["name"])
        elif action == "delete":
            self.library.path(args["id"]).unlink()
        elif action == "import":
            self.library.import_run(args["path"])
        elif action == "export":
            self.library.export(args["id"], args["path"], args["kind"])
        elif action == "browse":
            path = Path(args.get("path") or str(Path.home())).expanduser().resolve()
            entries = []
            for child in path.iterdir():
                try:
                    if child.is_dir() or child.suffix == ".murmuration":
                        entries.append({"name": child.name, "path": str(child), "directory": child.is_dir()})
                except OSError:
                    continue
            return {"path": str(path), "parent": str(path.parent), "entries": sorted(entries, key=lambda e: (not e["directory"], e["name"].lower()))}
        elif action != "refresh":
            raise ValueError(f"Unknown command: {action}")

    def require_live(self):
        if self.mode != "live":
            raise ValueError("Replay is read-only. Use settings to start a live experiment.")

    @property
    def duration(self):
        return max((r[0]["duration"] for r in self.active), default=0)

    def advance(self):
        if self.mode == "live":
            self.flock.step()
            if self.flock.tick % 12 == 0:
                self.history.append([self.flock.time, *self.flock.metrics()])
                self.history = self.history[-600:]
            if self.recording and self.recording.capture(self.flock):
                self.stop_recording()
        else:
            self.cursor = min(self.duration, self.cursor + DT)
            if self.cursor >= self.duration:
                self.paused = True

    def status(self):
        return {"mode": self.mode, "paused": self.paused, "speed": self.speed,
                "generation": self.generation, "recording": self.recording is not None,
                "recorded": (self.flock.tick - self.recording.start_tick) * DT if self.recording else 0,
                "time": self.flock.time if self.mode == "live" else self.cursor,
                "duration": self.duration, "last_command": self.last_command}

    def frame(self):
        self.sequence += 1
        frames = [self.flock.frame(self.selected)] if self.mode == "live" else [sample(r, self.cursor) for r in self.active]
        return {"generation": self.generation, "sequence": self.sequence, "frames": frames}

    def detail(self):
        return {"config": self.flock.config.dict() if self.mode == "live" else sample(self.active[0], self.cursor)["config"],
                "library": self.library.list(),
                "experiments": [{"metadata": r[0], "metrics": r[1]["metrics"].tolist()} for r in self.active]}


def publish_latest(outbox, item):
    try:
        outbox.put_nowait(item)
    except queue.Full:
        try:
            outbox.get_nowait()
        except queue.Empty:
            pass
        try:
            outbox.put_nowait(item)
        except queue.Full:
            pass


def run_worker(workspace, commands, frames, events, stop):
    session = None
    try:
        session = Session(workspace)
        def emit(event):
            # Reliable events have backpressure; unlike display frames they are not discarded.
            while not stop.is_set():
                try:
                    events.put(event, timeout=.1)
                    return
                except queue.Full:
                    continue
        emit({"type": "detail", **session.detail(), "status": session.status()})
        next_tick, next_frame, next_metrics = time.perf_counter(), 0, 0
        while not stop.is_set():
            for _ in range(16):
                try:
                    message = commands.get_nowait()
                except queue.Empty:
                    break
                try:
                    result = session.command(message["action"], message.get("args", {}))
                    session.last_command = message["id"]
                    event = {"type": "completed", "id": message["id"], "action": message["action"], "result": result, "status": session.status()}
                    if message["action"] not in ("seek", "select", "pause", "speed", "step", "browse"):
                        event.update(session.detail())
                    emit(event)
                except Exception as exc:
                    emit({"type": "error", "id": message["id"], "message": str(exc)})
            now = time.perf_counter()
            was_recording = session.recording is not None
            if not session.paused and now >= next_tick:
                try:
                    session.advance()
                except Exception as exc:
                    session.paused = True
                    emit({"type": "error", "message": f"Simulation paused: {exc}. Save or reset to continue."})
                # No catch-up loop: slow machines advance simulation time more slowly.
                next_tick = max(next_tick + DT / session.speed, time.perf_counter())
            if was_recording and session.recording is None:
                emit({"type": "detail", **session.detail(), "status": session.status()})
            if now >= next_frame:
                publish_latest(frames, {"frame": session.frame(), "status": session.status()})
                next_frame = now + .05
            if now >= next_metrics:
                emit({"type": "metrics", "metrics": session.history if session.mode == "live" else [], "status": session.status()})
                next_metrics = now + .2
            stop.wait(.001)
    except BaseException as exc:
        try:
            events.put({"type": "fatal", "message": f"Simulation worker stopped: {exc}. Restart the app."}, timeout=.2)
        except queue.Full:
            pass
    finally:
        if session:
            try:
                session.stop_recording()
            except Exception:
                # Main process logs shutdown failure separately via exit status.
                raise
