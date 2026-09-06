"""Headless model, persistence and process acceptance tests. Run unittest discover."""
import csv
import json
from pathlib import Path
import queue
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import Config, DT, Flock, OBSTACLE_RADIUS, WORLD
from storage import Library, Recording, read_archive, sample, save_archive
from worker import Session, publish_latest
from controller import Controller


class ModelTests(unittest.TestCase):
    def test_repeatability(self):
        a, b = Flock(Config(population=100)), Flock(Config(population=100))
        for _ in range(30):
            a.step(); b.step()
        np.testing.assert_array_equal(a.positions, b.positions)
        np.testing.assert_array_equal(a.velocities, b.velocities)

    def test_bounds_overlap_and_obstacle(self):
        flock = Flock(Config(population=100, obstacle=True))
        flock.positions[:] = 0
        flock.velocities[:] = 100
        flock.positions[:20] = 60
        for _ in range(20):
            flock.step()
        self.assertTrue(np.isfinite(flock.positions).all())
        self.assertLessEqual(np.abs(flock.positions).max(), WORLD)
        self.assertLessEqual(np.linalg.norm(flock.velocities, axis=1).max(), flock.config.speed + 1e-9)
        self.assertGreaterEqual(np.linalg.norm(flock.positions, axis=1).min(), OBSTACLE_RADIUS - 1e-9)

    def test_rules(self):
        flock = Flock(Config(population=100))
        # A lone pair, with all remaining agents outside the pair's neighborhood.
        flock.positions[:] = 35
        flock.positions[0] = (0, 0, 0); flock.positions[1] = (2, 0, 0)
        flock.velocities[:] = 0; flock.velocities[1] = (0, 3, 0)
        forces = flock.forces()
        self.assertLess(forces[0, 0, 0], 0)
        self.assertGreater(forces[0, 1, 1], 0)
        self.assertGreater(forces[0, 2, 0], 0)
        flock.positions[1] = 0
        forces = flock.forces()
        self.assertLess(forces[0, 0, 0], 0)
        self.assertGreater(forces[1, 0, 0], 0)

    def test_validation_and_metrics(self):
        for config in (Config(population=99), Config(seed=-1), Config(speed=float('nan')), Config(obstacle=1)):
            with self.assertRaises(ValueError): config.validated()
        flock = Flock(Config(population=100))
        with self.assertRaises(ValueError): flock.configure({'seed': 2})
        flock.velocities[:] = (3, 0, 0)
        self.assertAlmostEqual(flock.metrics()[0], 3)
        self.assertAlmostEqual(flock.metrics()[1], 1)
        flock.configure({'speed': 2})
        self.assertLessEqual(np.linalg.norm(flock.velocities, axis=1).max(), 2)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.library = Library(self.temp.name)
        self.flock = Flock(Config(population=100))

    def recording(self):
        recording = Recording(self.flock, 'Test run')
        for _ in range(24):
            self.flock.step(); recording.capture(self.flock)
        self.flock.configure({'cohesion': 2})
        recording.event(self.flock, {'cohesion': 2})
        return recording.finish(self.flock)

    def test_round_trip_sampling_and_csv(self):
        metadata, arrays = self.recording()
        self.library.save((metadata, arrays))
        loaded = self.library.load(metadata['id'])
        for name in arrays:
            np.testing.assert_array_equal(arrays[name], loaded[1][name])
        self.assertEqual(loaded[0]['events'], metadata['events'])
        middle = sample(loaded, .05)
        np.testing.assert_allclose(middle['positions'], (arrays['positions'][0] + arrays['positions'][1]) / 2, rtol=1e-6)
        self.assertEqual(sample(loaded, 100)['time'], metadata['duration'])
        self.assertEqual(sample(loaded, 100)['config']['cohesion'], 2)
        out = Path(self.temp.name) / 'metrics.csv'
        self.library.export(metadata['id'], out, 'csv')
        with out.open() as stream: rows = list(csv.reader(stream))
        self.assertEqual(len(rows), len(arrays['metrics']) + 1)
        self.assertEqual(float(rows[-1][1]), arrays['metrics'][-1, 1])
        with self.assertRaises(ValueError): self.library.export(metadata['id'], out, 'csv')

    def test_import_rename_delete(self):
        recording = self.recording(); self.library.save(recording)
        identifier = recording[0]['id']
        self.library.rename(identifier, 'Renamed')
        self.assertEqual(self.library.load(identifier)[0]['name'], 'Renamed')
        self.library.import_run(self.library.path(identifier))
        self.assertEqual(len(self.library.list()['runs']), 2)
        self.library.path(identifier).unlink()
        self.assertEqual(len(self.library.list()['runs']), 1)
        with self.assertRaises(ValueError): self.library.path('../escape')

    def test_corrupt_version_nonfinite(self):
        path = Path(self.temp.name) / 'bad.murmuration'
        path.write_bytes(b'not a zip')
        with self.assertRaises(ValueError): read_archive(path)
        metadata, arrays = self.recording(); metadata['version'] = 100
        save_archive(path, metadata, arrays)
        with self.assertRaisesRegex(ValueError, 'version'): read_archive(path)
        metadata['version'] = 1; arrays['positions'][0, 0, 0] = np.nan
        save_archive(path, metadata, arrays)
        with self.assertRaisesRegex(ValueError, 'non-finite'): read_archive(path)

    def test_atomic_save_preserves_previous(self):
        recording = self.recording(); self.library.save(recording)
        path = self.library.path(recording[0]['id']); previous = path.read_bytes()
        with patch('storage.os.replace', side_effect=OSError('disk failure')):
            with self.assertRaises(OSError): self.library.save(recording)
        self.assertEqual(path.read_bytes(), previous)
        self.assertFalse(list(Path(self.temp.name).glob('*.tmp')))


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.session = Session(self.temp.name)
        self.session.command('reset', {'config': Config(population=100).dict()})

    def test_pause_step_configure_reset_recording(self):
        s = self.session
        with self.assertRaises(ValueError): s.command('step', {})
        s.command('pause', {'paused': True}); tick = s.flock.tick
        s.command('step', {}); self.assertEqual(s.flock.tick, tick+1)
        s.command('record', {'name': 'Before reset'})
        s.command('configure', {'changes': {'alignment': 2}})
        self.assertEqual(s.recording.metadata['events'][0]['changes'], {'alignment': 2})
        generation = s.generation
        s.command('reset', {'config': Config(population=100, seed=1).dict()})
        self.assertNotEqual(generation, s.generation)
        self.assertIsNone(s.recording)
        self.assertEqual(len(s.library.list()['runs']), 1)

    def test_limit_replay_compare(self):
        s = self.session
        with patch('storage.LIMIT_SECONDS', .2):
            for name in ('A', 'B'):
                s.command('record', {'name': name})
                for _ in range(12): s.advance()
                self.assertIsNone(s.recording)
        ids = [r['id'] for r in s.library.list()['runs']]
        s.command('compare', {'ids': ids})
        self.assertEqual(s.mode, 'compare'); self.assertTrue(s.paused)
        s.command('seek', {'time': .1})
        self.assertEqual(len(s.frame()['frames']), 2)
        with self.assertRaises(ValueError): s.command('configure', {'changes': {'cohesion': 1}})
        s.command('pause', {'paused': False})
        for _ in range(20): s.advance()
        self.assertTrue(s.paused); self.assertEqual(s.cursor, s.duration)

    def test_failed_reset_preserves_recording(self):
        s = self.session; s.command('record', {'name': 'Keep me'})
        with self.assertRaises(ValueError): s.command('reset', {'config': {'population': 1}})
        self.assertIsNotNone(s.recording)

    def test_bounded_display_queue(self):
        out = queue.Queue(2)
        for i in range(100): publish_latest(out, i)
        self.assertEqual(out.qsize(), 2)
        self.assertEqual([out.get(), out.get()], [98, 99])


class ProcessTests(unittest.TestCase):
    def test_spawn_shutdown_and_failure(self):
        with tempfile.TemporaryDirectory() as workspace:
            controller = Controller(workspace)
            try:
                deadline = time.monotonic() + 15; updates = []
                while time.monotonic() < deadline and not any(u['type']=='frame' for u in updates):
                    updates.extend(controller.poll()); time.sleep(.02)
                self.assertTrue(any(u['type']=='frame' for u in updates), updates)
                response = controller.command('pause', {'paused': True})
                self.assertTrue(response['accepted'])
                controller.process.terminate(); controller.process.join(3)
                self.assertTrue(any(u['type']=='fatal' for u in controller.poll()))
                self.assertFalse(controller.command('step', {})['accepted'])
            finally: controller.close()
            self.assertFalse(controller.process.is_alive())


if __name__ == '__main__':
    unittest.main()
