"""Report actual fixed-step throughput; this is not a rendering benchmark."""
from pathlib import Path
import platform
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from engine import Config, Flock

print(platform.platform(), platform.processor(), 'Python', platform.python_version(), 'NumPy', np.__version__)
for count in (500, 2000):
    model = Flock(Config(population=count))
    start = time.perf_counter()
    for _ in range(120):
        model.step()
    elapsed = time.perf_counter() - start
    print(f'{count} agents: {120 / elapsed:.1f} steps/s; {elapsed:.2f} wall seconds for 2 simulated seconds')
