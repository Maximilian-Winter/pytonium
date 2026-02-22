"""Dashboard backend — provides top processes and system info not in state namespaces."""

import json
import platform

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class WidgetBackend:
    """Bound to JS as `widget.*` methods."""

    def get_top_processes(self, count=8):
        """Return JSON string of top processes by CPU usage."""
        if not HAS_PSUTIL:
            return "[]"
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = p.info
                procs.append({
                    "pid": info["pid"],
                    "name": info["name"] or "?",
                    "cpu": round(info["cpu_percent"] or 0, 1),
                    "mem": round(info["memory_percent"] or 0, 1),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        procs.sort(key=lambda x: x["cpu"], reverse=True)
        return json.dumps(procs[:int(count)])

    def get_system_info(self):
        """Return static system info as JSON string."""
        info = {
            "os": f"{platform.system()} {platform.release()}",
            "machine": platform.machine(),
            "processor": platform.processor() or "Unknown",
            "python": platform.python_version(),
        }
        if HAS_PSUTIL:
            info["cpu_count_logical"] = psutil.cpu_count(logical=True)
            info["cpu_count_physical"] = psutil.cpu_count(logical=False)
            mem = psutil.virtual_memory()
            info["ram_total_gb"] = round(mem.total / (1024 ** 3), 1)
        return json.dumps(info)

    def get_disk_partitions(self):
        """Return disk partition info as JSON string."""
        if not HAS_PSUTIL:
            return "[]"
        parts = []
        for p in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(p.mountpoint)
                parts.append({
                    "device": p.device,
                    "mountpoint": p.mountpoint,
                    "fstype": p.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "percent": round(usage.percent, 1),
                })
            except (PermissionError, OSError):
                pass
        return json.dumps(parts)
