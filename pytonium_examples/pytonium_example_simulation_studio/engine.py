"""Deterministic, headless flocking model. Distances are illustrative world units."""
from dataclasses import asdict, dataclass, replace
from itertools import product
import math

import numpy as np

DT = 1 / 60
WORLD = 40.0
OBSTACLE_RADIUS = 9.0
OFFSETS = tuple(product((-1, 0, 1), repeat=3))


@dataclass(frozen=True)
class Config:
    population: int = 500
    seed: int = 42
    separation: float = 1.5
    alignment: float = 1.0
    cohesion: float = 0.8
    radius: float = 10.0
    speed: float = 12.0
    obstacle: bool = False
    preset: str = "gathering"

    def validated(self):
        for key, low, high in (("population", 100, 2000), ("seed", 0, 2**32 - 1)):
            value = getattr(self, key)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{key} must be an integer between {low} and {high}.")
        for key, low, high in (("separation", 0, 4), ("alignment", 0, 4),
                               ("cohesion", 0, 4), ("radius", 3, 20), ("speed", 2, 25)):
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f"{key} must be a finite number between {low} and {high}.")
        if type(self.obstacle) is not bool or self.preset not in PRESETS:
            raise ValueError("Choose a valid obstacle setting and preset.")
        return self

    def dict(self):
        return asdict(self)


PRESETS = {
    "gathering": {"separation": 1.5, "alignment": 1.0, "cohesion": 0.8, "obstacle": False},
    "crossing": {"separation": 2.0, "alignment": 0.6, "cohesion": 0.4, "obstacle": False},
    "obstacle": {"separation": 1.7, "alignment": 1.2, "cohesion": 0.8, "obstacle": True},
}


def limited(vectors, maximum):
    norms = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors * np.minimum(1, maximum / np.maximum(norms, 1e-9))


class Flock:
    def __init__(self, config=None):
        self.config = (config or Config()).validated()
        rng = np.random.default_rng(self.config.seed)
        n = self.config.population
        self.positions = rng.uniform(-25, 25, (n, 3))
        self.velocities = limited(rng.normal(size=(n, 3)), 1) * self.config.speed * .6
        if self.config.preset == "crossing":
            signs = np.where(np.arange(n) < n // 2, 1, -1)
            self.positions[:, 0] = -signs * 24 + rng.normal(0, 3, n)
            self.velocities[:, 0] = signs * self.config.speed * .8
        self.tick = 0
        self.vectors = np.zeros((n, 3, 3))
        self._constrain()

    @property
    def time(self):
        return self.tick * DT

    def configure(self, changes):
        if set(changes) & {"population", "seed", "preset"}:
            raise ValueError("Population, seed, and preset changes require Reset.")
        self.config = replace(self.config, **changes).validated()
        self.velocities = limited(self.velocities, self.config.speed)
        self._constrain()

    def forces(self):
        """Batch agents by grid cell; only inspect the 27 neighboring cells."""
        p, v, c = self.positions, self.velocities, self.config
        cells = np.floor(p / c.radius).astype(int)
        grid = {}
        for i, cell in enumerate(cells):
            grid.setdefault(tuple(cell), []).append(i)
        result = np.zeros((len(p), 3, 3))
        for cell, indices in grid.items():
            nearby = [j for offset in OFFSETS for j in grid.get(tuple(cell[k] + offset[k] for k in range(3)), ())]
            a, b = np.asarray(indices), np.asarray(nearby)
            delta = p[b][None, :, :] - p[a][:, None, :]
            d2 = np.sum(delta * delta, axis=2)
            mask = (d2 < c.radius**2) & (a[:, None] != b[None, :])
            count = mask.sum(axis=1, keepdims=True)
            safe = np.maximum(count, 1)
            # Overlap gets a stable antisymmetric direction, never division by zero.
            overlap = mask & (d2 < 1e-12)
            delta[:, :, 0] += overlap * np.sign(b[None, :] - a[:, None]) * .01
            separation = -np.sum(delta * (mask / np.maximum(d2, .01))[:, :, None], axis=1)
            alignment = mask @ v[b] / safe - v[a]
            alignment[count[:, 0] == 0] = 0
            cohesion = np.sum(delta * mask[:, :, None], axis=1) / safe
            result[a, 0] = limited(separation * 12, 12)
            result[a, 1] = limited(alignment, 12)
            result[a, 2] = limited(cohesion * .6, 12)
        return result

    def step(self):
        c = self.config
        self.vectors = self.forces()
        force = self.vectors[:, 0] * c.separation + self.vectors[:, 1] * c.alignment + self.vectors[:, 2] * c.cohesion
        force -= np.sign(self.positions) * np.maximum(np.abs(self.positions) - (WORLD - 9), 0) * 3
        if c.obstacle:
            distance = np.linalg.norm(self.positions, axis=1, keepdims=True)
            force += self.positions / np.maximum(distance, 1e-9) * np.maximum(OBSTACLE_RADIUS + 7 - distance, 0) * 5
        self.velocities = limited(self.velocities + limited(force, 30) * DT, c.speed)
        self.positions += self.velocities * DT
        self._constrain()
        if not np.isfinite(self.positions).all() or not np.isfinite(self.velocities).all():
            raise ValueError("Simulation became non-finite. Reset the experiment.")
        self.tick += 1

    def _constrain(self):
        hit = np.abs(self.positions) > WORLD
        self.velocities[hit] *= -.5
        np.clip(self.positions, -WORLD, WORLD, out=self.positions)
        if self.config.obstacle:
            distance = np.linalg.norm(self.positions, axis=1)
            inside = distance < OBSTACLE_RADIUS
            normal = self.positions[inside] / np.maximum(distance[inside, None], 1e-9)
            normal[distance[inside] < 1e-9] = (1, 0, 0)
            self.positions[inside] = normal * OBSTACLE_RADIUS
            inward = np.minimum(np.sum(self.velocities[inside] * normal, axis=1), 0)
            self.velocities[inside] -= normal * inward[:, None]

    def metrics(self):
        speed = np.linalg.norm(self.velocities, axis=1)
        directions = self.velocities / np.maximum(speed[:, None], 1e-9)
        return [float(speed.mean()), float(np.linalg.norm(directions.mean(axis=0))),
                float(np.sqrt(np.mean(np.sum((self.positions - self.positions.mean(axis=0))**2, axis=1))))]

    def frame(self, selected=-1):
        frame = {"time": self.time, "positions": self.positions.astype(np.float32).tolist(),
                 "velocities": self.velocities.astype(np.float32).tolist()}
        if 0 <= selected < len(self.positions):
            frame["selection"] = {"id": selected, "vectors": self.vectors[selected].tolist()}
        return frame
