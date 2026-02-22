"""System services - polls system data and pushes to widget state namespaces."""

import time
from datetime import datetime

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("PytoniumShell: psutil not installed. System services will be limited.")


class SystemServices:
    """Periodically collects system data and pushes it to widget state namespaces."""

    def __init__(self, shell):
        self.shell = shell
        self.poll_interval = 1.0  # seconds
        self._last_poll = 0.0
        self._running = False

    def start(self):
        """Start the polling service."""
        self._running = True
        self._last_poll = 0.0  # trigger immediate first poll

    def stop(self):
        """Stop the polling service."""
        self._running = False

    def poll(self):
        """Poll system data if enough time has elapsed."""
        if not self._running:
            return

        now = time.time()
        if now - self._last_poll < self.poll_interval:
            return
        self._last_poll = now

        self._poll_datetime()

        if HAS_PSUTIL:
            self._poll_cpu()
            self._poll_memory()
            self._poll_disk()
            self._poll_network()
            self._poll_battery()

    def _push_state(self, namespace, key, value):
        """Push a state update to all widgets subscribed to the namespace."""
        for widget in self.shell.widget_manager.active_widgets:
            state_namespaces = widget.manifest.get("state_namespaces", [])
            if namespace in state_namespaces:
                try:
                    widget.pytonium.set_state(namespace, key, value)
                except Exception:
                    pass  # widget may have closed

    def _poll_datetime(self):
        """Push date/time state."""
        now = datetime.now()
        self._push_state("datetime", "time", now.strftime("%H:%M"))
        self._push_state("datetime", "time_seconds", now.strftime("%H:%M:%S"))
        self._push_state("datetime", "date", now.strftime("%d.%m.%Y"))
        self._push_state("datetime", "day", now.strftime("%A"))

    def _poll_cpu(self):
        """Push CPU usage state."""
        cpu = psutil.cpu_percent(percpu=True)
        avg = sum(cpu) / len(cpu) if cpu else 0.0
        self._push_state("system", "cpu_percent", cpu)
        self._push_state("system", "cpu_avg", round(avg, 1))

    def _poll_memory(self):
        """Push memory usage state."""
        mem = psutil.virtual_memory()
        self._push_state("system", "mem_total", mem.total)
        self._push_state("system", "mem_used", mem.used)
        self._push_state("system", "mem_percent", round(mem.percent, 1))

    def _poll_disk(self):
        """Push disk usage state."""
        try:
            disk = psutil.disk_usage("/")
            self._push_state("system", "disk_total", disk.total)
            self._push_state("system", "disk_used", disk.used)
            self._push_state("system", "disk_percent", round(disk.percent, 1))
        except Exception:
            pass

    def _poll_network(self):
        """Push network I/O state."""
        net = psutil.net_io_counters()
        self._push_state("system", "net_sent", net.bytes_sent)
        self._push_state("system", "net_recv", net.bytes_recv)

    def _poll_battery(self):
        """Push battery state if available."""
        battery = psutil.sensors_battery()
        if battery:
            self._push_state("system", "battery_percent", round(battery.percent, 1))
            self._push_state("system", "battery_charging", battery.power_plugged)
