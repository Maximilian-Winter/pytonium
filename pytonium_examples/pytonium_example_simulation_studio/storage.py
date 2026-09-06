"""Portable, versioned recordings; no executable serialization or archive extraction."""
from datetime import datetime, timezone
import csv
import io
import json
import os
from pathlib import Path
import tempfile
import uuid
import zipfile

import numpy as np

from engine import Config, DT

VERSION = 1
LIMIT_SECONDS = 120
ARRAYS = ("times", "positions", "velocities", "metrics")


class Recording:
    def __init__(self, flock, name="Untitled experiment"):
        self.start_tick = flock.tick
        self.metadata = {"version": VERSION, "id": uuid.uuid4().hex,
                         "name": clean_name(name), "created": datetime.now(timezone.utc).isoformat(),
                         "config": flock.config.dict(), "events": []}
        self.times, self.positions, self.velocities, self.metrics = [], [], [], []
        self.capture(flock, force=True)

    def capture(self, flock, force=False):
        tick = flock.tick - self.start_tick
        t = tick * DT
        if (force or tick % 6 == 0) and (not self.times or self.times[-1] != t):
            self.times.append(t)
            self.positions.append(flock.positions.astype(np.float32).copy())
            self.velocities.append(flock.velocities.astype(np.float32).copy())
        if (force or tick % 12 == 0) and (not self.metrics or self.metrics[-1][0] != t):
            self.metrics.append([t, *flock.metrics()])
        return t >= LIMIT_SECONDS

    def event(self, flock, changes):
        self.metadata["events"].append({"time": (flock.tick - self.start_tick) * DT, "changes": changes})

    def finish(self, flock):
        self.capture(flock, force=True)
        arrays = {key: np.asarray(getattr(self, key)) for key in ARRAYS}
        self.metadata["duration"] = float(arrays["times"][-1])
        return self.metadata, arrays


def clean_name(name):
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100:
        raise ValueError("Enter a name between 1 and 100 characters.")
    return name.strip()


def save_archive(path, metadata, arrays):
    """Replace only after the complete archive has been flushed to disk."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".tmp", delete=False) as stream:
            temp = Path(stream.name)
            with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
                archive.writestr("metadata.json", json.dumps(metadata, allow_nan=False))
                for name in ARRAYS:
                    buf = io.BytesIO()
                    np.save(buf, arrays[name], allow_pickle=False)
                    archive.writestr(name + ".npy", buf.getvalue())
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if temp and temp.exists():
            temp.unlink()


def read_archive(path, metadata_only=False):
    try:
        with zipfile.ZipFile(path) as archive:
            if len(archive.infolist()) != 5 or set(archive.namelist()) != {"metadata.json", *(name + ".npy" for name in ARRAYS)}:
                raise ValueError("Recording archive has unexpected contents.")
            if sum(i.file_size for i in archive.infolist()) > 100_000_000 or archive.getinfo("metadata.json").file_size > 2_000_000:
                raise ValueError("Recording exceeds the supported archive size.")
            metadata = json.loads(archive.read("metadata.json"))
            if metadata.get("version") != VERSION:
                raise ValueError("Unsupported recording version. Open it with a compatible Murmuration version.")
            clean_name(metadata["name"])
            Config(**metadata["config"]).validated()
            if metadata_only:
                return metadata
            arrays = {name: np.load(io.BytesIO(archive.read(name + ".npy")), allow_pickle=False) for name in ARRAYS}
        times, p, v, metrics = (arrays[key] for key in ARRAYS)
        n = metadata["config"]["population"]
        if times.ndim != 1 or not 1 <= len(times) <= 1202 or p.shape != (len(times), n, 3) or v.shape != p.shape:
            raise ValueError("Recording contains invalid frame dimensions.")
        if metrics.ndim != 2 or metrics.shape[1] != 4 or not 1 <= len(metrics) <= 602:
            raise ValueError("Recording contains invalid metrics.")
        if any(a.dtype.kind not in "fiu" or not np.isfinite(a).all() for a in arrays.values()):
            raise ValueError("Recording contains non-finite or unsupported values.")
        if times[0] != 0 or times[-1] > LIMIT_SECONDS + DT or np.any(np.diff(times) <= 0):
            raise ValueError("Recording timestamps are invalid.")
        if metrics[0, 0] != 0 or np.any(np.diff(metrics[:, 0]) <= 0) or metrics[-1, 0] > times[-1]:
            raise ValueError("Metric timestamps are invalid.")
        if abs(float(metadata["duration"]) - float(times[-1])) > 1e-5:
            raise ValueError("Recording duration does not match its frames.")
        config = Config(**metadata["config"])
        last_time = 0
        for event in metadata["events"]:
            t = event["time"]
            if not isinstance(t, (int, float)) or not np.isfinite(t) or not last_time <= t <= times[-1]:
                raise ValueError("Recording parameter timestamps are invalid.")
            changes = event["changes"]
            if set(changes) - {"separation", "alignment", "cohesion", "radius", "speed", "obstacle"}:
                raise ValueError("Recording contains unsupported parameter changes.")
            config = Config(**(config.dict() | changes)).validated()
            last_time = t
        return metadata, arrays
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, EOFError) as exc:
        raise ValueError(f"Cannot open recording: {exc}") from exc


def sample(recording, time):
    metadata, arrays = recording
    times = arrays["times"]
    t = float(np.clip(time, 0, times[-1]))
    right = min(int(np.searchsorted(times, t, side="right")), len(times) - 1)
    left = max(0, right - 1)
    alpha = 0 if left == right else (t - times[left]) / (times[right] - times[left])
    config = metadata["config"].copy()
    for event in metadata["events"]:
        if event["time"] <= t:
            config.update(event["changes"])
    return {"time": t, "config": config,
            **{key: (arrays[key][left] * (1 - alpha) + arrays[key][right] * alpha).tolist()
               for key in ("positions", "velocities")}}


class Library:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, identifier):
        if not isinstance(identifier, str) or len(identifier) != 32 or any(c not in "0123456789abcdef" for c in identifier):
            raise ValueError("Invalid experiment identifier.")
        return self.root / (identifier + ".murmuration")

    def list(self):
        entries, errors = [], []
        for path in self.root.glob("*.murmuration"):
            try:
                entry = read_archive(path, metadata_only=True)
                entry["id"] = path.stem
                entries.append(entry)
            except ValueError as exc:
                errors.append(f"{path.name}: {exc}")
        return {"runs": sorted(entries, key=lambda item: item["created"], reverse=True), "errors": errors}

    def save(self, recording):
        metadata, arrays = recording
        save_archive(self.path(metadata["id"]), metadata, arrays)

    def load(self, identifier):
        return read_archive(self.path(identifier))

    def rename(self, identifier, name):
        metadata, arrays = self.load(identifier)
        metadata["name"] = clean_name(name)
        save_archive(self.path(identifier), metadata, arrays)

    def import_run(self, path):
        metadata, arrays = read_archive(path)
        metadata["id"] = uuid.uuid4().hex
        self.save((metadata, arrays))

    def export(self, identifier, path, kind):
        path = Path(path).expanduser()
        if path.exists():
            raise ValueError("That file already exists. Choose a new name.")
        metadata, arrays = self.load(identifier)
        if kind == "archive":
            save_archive(path, metadata, arrays)
        elif kind == "csv":
            with path.open("x", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(("simulation_seconds", "average_speed", "directional_alignment", "flock_spread"))
                writer.writerows(arrays["metrics"])
        else:
            raise ValueError("Choose CSV or recording archive export.")
