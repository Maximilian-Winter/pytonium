"""Main-process adapter. Only this layer communicates with Pytonium."""
import multiprocessing as mp
import queue
import uuid

from worker import run_worker


class Controller:
    def __init__(self, workspace):
        context = mp.get_context("spawn")
        self.commands = context.Queue(64)
        self.frames = context.Queue(2)
        self.events = context.Queue(64)
        self.stop = context.Event()
        self.process = context.Process(target=run_worker, args=(str(workspace), self.commands, self.frames, self.events, self.stop), name="Murmuration simulation")
        self.failed = False
        self.generation = None
        self.process.start()

    def command(self, action: str, args: dict) -> dict:
        if not self.process.is_alive():
            return {"accepted": False, "error": "Simulation worker is unavailable. Restart the app."}
        identifier = uuid.uuid4().hex
        try:
            self.commands.put_nowait({"id": identifier, "action": action, "args": args})
            return {"accepted": True, "id": identifier}
        except queue.Full:
            return {"accepted": False, "error": "The worker is busy. Try again shortly."}

    def poll(self):
        updates = []
        for _ in range(64):
            try:
                event = self.events.get_nowait()
                if "status" in event:
                    self.generation = event["status"]["generation"]
                updates.append(event)
            except queue.Empty:
                break
        latest = None
        for _ in range(2):
            try:
                latest = self.frames.get_nowait()
            except queue.Empty:
                break
        if latest and latest["frame"]["generation"] == self.generation:
            updates.append({"type": "frame", **latest})
        if not self.process.is_alive() and not self.failed:
            self.failed = True
            updates.append({"type": "fatal", "message": f"Worker exited ({self.process.exitcode}). Restart the app; saved experiments remain available."})
        return updates

    def close(self):
        self.stop.set()
        # Drain queues while joining so a multiprocessing feeder cannot deadlock.
        import time
        deadline = time.monotonic() + 10
        while self.process.is_alive() and time.monotonic() < deadline:
            self.poll()
            self.process.join(.02)
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(2)
            print("Murmuration: worker shutdown timed out; the current recording may not have saved.")
        for channel in (self.commands, self.frames, self.events):
            channel.cancel_join_thread()
            channel.close()
