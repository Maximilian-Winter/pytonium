"""
Pytonium System Control Center

A focused hardware/OS monitoring dashboard with safe system interactions.
Uses psutil for real-time system statistics — no other dependencies needed.

Install: pip install psutil
"""

import os
import sys
import time
import platform
import psutil
from datetime import datetime
from threading import Thread

from Pytonium import Pytonium, returns_value_to_javascript


# ============================================================================
# Window Control Functions (standard frameless window pattern)
# ============================================================================

@returns_value_to_javascript("boolean")
def window_is_maximized() -> bool:
    return pytonium.is_maximized()


@returns_value_to_javascript("object")
def window_get_position():
    x, y = pytonium.get_window_position()
    return {"x": x, "y": y}


@returns_value_to_javascript("object")
def window_get_size():
    w, h = pytonium.get_window_size()
    return {"width": w, "height": h}


def window_minimize():
    pytonium.minimize_window()


def window_maximize():
    if pytonium.is_maximized():
        pytonium.restore_window()
    else:
        pytonium.maximize_window()


def window_close():
    pytonium.close_window()


def window_start_drag():
    pytonium.start_window_drag()


def window_resize(new_width: int, new_height: int, anchor: int):
    pytonium.resize_window(new_width, new_height, anchor)


# ============================================================================
# System Information (on-demand, called once or on tab switch)
# ============================================================================

@returns_value_to_javascript("object")
def get_system_info():
    """One-time system information: OS, hardware, battery, boot time."""
    uname = platform.uname()
    cpu_freq = psutil.cpu_freq()
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    mem = psutil.virtual_memory()

    info = {
        "os_name": f"{uname.system} {uname.release}",
        "os_version": uname.version,
        "architecture": uname.machine,
        "hostname": uname.node,
        "username": os.getlogin() if hasattr(os, "getlogin") else "unknown",
        "cpu_model": uname.processor or "Unknown",
        "cpu_cores_physical": psutil.cpu_count(logical=False) or 0,
        "cpu_cores_logical": psutil.cpu_count(logical=True) or 0,
        "cpu_freq_max": round(cpu_freq.max, 0) if cpu_freq else 0,
        "ram_total_gb": round(mem.total / (1024 ** 3), 1),
        "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
        "python_version": platform.python_version(),
    }

    # Battery (optional — desktops won't have one)
    battery = psutil.sensors_battery()
    if battery:
        info["battery_percent"] = round(battery.percent, 1)
        info["battery_plugged"] = battery.power_plugged
        info["battery_secs_left"] = battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else -1
    else:
        info["battery_percent"] = None

    return info


@returns_value_to_javascript("array")
def get_disk_partitions():
    """List disk partitions with usage statistics."""
    partitions = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total / (1024 ** 3), 1),
                "used_gb": round(usage.used / (1024 ** 3), 1),
                "free_gb": round(usage.free / (1024 ** 3), 1),
                "percent": round(usage.percent, 1),
            })
        except (PermissionError, OSError):
            continue
    return partitions


# ============================================================================
# System Actions (JS → Python calls)
# ============================================================================

@returns_value_to_javascript("object")
def kill_process(pid: int):
    """Kill a process by PID. Refuses system-critical PIDs."""
    protected_pids = {0, 4}  # PID 0 = idle, PID 4 = System (Windows)
    own_pid = os.getpid()

    if pid in protected_pids:
        return {"success": False, "error": "Cannot kill system process"}
    if pid == own_pid:
        return {"success": False, "error": "Cannot kill own process"}

    try:
        proc = psutil.Process(pid)
        proc_name = proc.name()
        proc.kill()
        return {"success": True, "name": proc_name}
    except psutil.NoSuchProcess:
        return {"success": False, "error": "Process no longer exists"}
    except psutil.AccessDenied:
        return {"success": False, "error": "Access denied — may require admin privileges"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@returns_value_to_javascript("boolean")
def open_folder(path: str) -> bool:
    """Open a folder in the system file explorer."""
    if not os.path.isdir(path):
        return False
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            import subprocess
            subprocess.Popen(["open", path])
        else:
            import subprocess
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        return False


# ============================================================================
# Network (on-demand)
# ============================================================================

@returns_value_to_javascript("array")
def get_connections():
    """Get active network connections (top 20 by status)."""
    connections = []
    try:
        for conn in psutil.net_connections(kind="inet")[:20]:
            local = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
            remote = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
            proc_name = ""
            if conn.pid:
                try:
                    proc_name = psutil.Process(conn.pid).name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    proc_name = f"PID {conn.pid}"
            connections.append({
                "local": local,
                "remote": remote,
                "status": conn.status,
                "pid": conn.pid or 0,
                "process": proc_name,
            })
    except (psutil.AccessDenied, PermissionError):
        pass
    return connections


# ============================================================================
# State Handler
# ============================================================================

class ControlCenterStateHandler:
    def update_state(self, namespace: str, key: str, value):
        pass  # State from JS is received but not acted upon


# ============================================================================
# Background Stats Thread
# ============================================================================

# History buffers for charts (last 60 data points = 30 seconds at 500ms)
_cpu_history = []
_net_down_history = []
_net_up_history = []
_mem_history = []

# Previous counters for delta calculation
_prev_net_io = None
_prev_disk_io = None
_prev_time = None


def background_updater():
    """Push system stats every 500ms via Pytonium state."""
    global _prev_net_io, _prev_disk_io, _prev_time
    global _cpu_history, _net_down_history, _net_up_history, _mem_history

    _prev_net_io = psutil.net_io_counters()
    _prev_disk_io = psutil.disk_io_counters()
    _prev_time = time.time()

    while True:
        time.sleep(0.5)
        if not pytonium.is_running():
            break

        try:
            now = time.time()
            dt = now - _prev_time
            if dt <= 0:
                dt = 0.5

            # --- CPU ---
            cpu_total = psutil.cpu_percent(interval=None)
            cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
            cpu_freq = psutil.cpu_freq()

            _cpu_history.append(cpu_total)
            if len(_cpu_history) > 60:
                _cpu_history.pop(0)

            # --- Memory ---
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            _mem_history.append(mem.percent)
            if len(_mem_history) > 60:
                _mem_history.pop(0)

            # --- Disk I/O ---
            disk_io = psutil.disk_io_counters()
            disk_read_speed = 0
            disk_write_speed = 0
            if disk_io and _prev_disk_io:
                disk_read_speed = (disk_io.read_bytes - _prev_disk_io.read_bytes) / dt
                disk_write_speed = (disk_io.write_bytes - _prev_disk_io.write_bytes) / dt
            _prev_disk_io = disk_io

            # --- Network ---
            net_io = psutil.net_io_counters()
            net_down_speed = 0
            net_up_speed = 0
            if net_io and _prev_net_io:
                net_down_speed = (net_io.bytes_recv - _prev_net_io.bytes_recv) / dt
                net_up_speed = (net_io.bytes_sent - _prev_net_io.bytes_sent) / dt
            _prev_net_io = net_io

            _net_down_history.append(net_down_speed)
            _net_up_history.append(net_up_speed)
            if len(_net_down_history) > 60:
                _net_down_history.pop(0)
            if len(_net_up_history) > 60:
                _net_up_history.pop(0)

            _prev_time = now

            # --- Network interfaces ---
            addrs = psutil.net_if_addrs()
            if_stats = psutil.net_if_stats()
            interfaces = []
            for name, addr_list in addrs.items():
                ip = ""
                mac = ""
                for addr in addr_list:
                    if addr.family.name == "AF_INET":
                        ip = addr.address
                    elif addr.family.name == "AF_LINK" or addr.family.name == "AF_PACKET":
                        mac = addr.address
                is_up = if_stats[name].isup if name in if_stats else False
                interfaces.append({
                    "name": name,
                    "ip": ip,
                    "mac": mac,
                    "is_up": is_up,
                })

            # --- Uptime ---
            uptime_seconds = int(now - psutil.boot_time())

            # --- Push stats ---
            pytonium.set_state("stats", "stats", {
                "cpu": round(cpu_total, 1),
                "cpu_per_core": [round(c, 1) for c in cpu_per_core],
                "cpu_freq": round(cpu_freq.current, 0) if cpu_freq else 0,
                "memory_percent": round(mem.percent, 1),
                "memory_used_gb": round(mem.used / (1024 ** 3), 2),
                "memory_total_gb": round(mem.total / (1024 ** 3), 2),
                "memory_available_gb": round(mem.available / (1024 ** 3), 2),
                "swap_percent": round(swap.percent, 1),
                "swap_used_gb": round(swap.used / (1024 ** 3), 2),
                "swap_total_gb": round(swap.total / (1024 ** 3), 2),
                "disk_read_speed": round(disk_read_speed),
                "disk_write_speed": round(disk_write_speed),
                "uptime_seconds": uptime_seconds,
                "cpu_history": list(_cpu_history),
                "mem_history": list(_mem_history),
                "net_down_history": [round(x) for x in _net_down_history],
                "net_up_history": [round(x) for x in _net_up_history],
            })

            # --- Push network ---
            pytonium.set_state("network", "stats", {
                "interfaces": interfaces,
                "total_down": round(net_down_speed),
                "total_up": round(net_up_speed),
            })

            # --- Push processes ---
            procs = []
            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
                try:
                    info = proc.info
                    mem_mb = info["memory_info"].rss / (1024 ** 2) if info["memory_info"] else 0
                    procs.append({
                        "pid": info["pid"],
                        "name": info["name"] or "Unknown",
                        "cpu": round(info["cpu_percent"] or 0, 1),
                        "memory": round(mem_mb, 1),
                        "status": info["status"] or "unknown",
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort by CPU descending, take top 15
            procs.sort(key=lambda p: p["cpu"], reverse=True)
            pytonium.set_state("processes", "list", {"top": procs[:15]})

        except Exception:
            pass


# ============================================================================
# Main Application
# ============================================================================

def main():
    global pytonium

    pytonium = Pytonium()
    pytonium.set_frameless_window(True)

    # Window controls
    pytonium.bind_function_to_javascript(window_is_maximized, "isMaximized", "window")
    pytonium.bind_function_to_javascript(window_get_position, "getPosition", "window")
    pytonium.bind_function_to_javascript(window_get_size, "getSize", "window")
    pytonium.bind_function_to_javascript(window_minimize, "minimize", "window")
    pytonium.bind_function_to_javascript(window_maximize, "maximize", "window")
    pytonium.bind_function_to_javascript(window_close, "close", "window")
    pytonium.bind_function_to_javascript(window_start_drag, "startDrag", "window")
    pytonium.bind_function_to_javascript(window_resize, "resize", "window")

    # System API
    pytonium.bind_function_to_javascript(get_system_info, "getSystemInfo", "system")
    pytonium.bind_function_to_javascript(get_disk_partitions, "getDiskPartitions", "system")
    pytonium.bind_function_to_javascript(kill_process, "killProcess", "system")
    pytonium.bind_function_to_javascript(open_folder, "openFolder", "system")

    # Network API
    pytonium.bind_function_to_javascript(get_connections, "getConnections", "network")

    # State handler
    state_handler = ControlCenterStateHandler()
    pytonium.add_state_handler(state_handler, ["stats", "network", "processes"])

    # Initialize
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "index.html")
    pytonium.initialize(f"file:///{html_path}", 1400, 900)

    # Start background stats thread
    Thread(target=background_updater, daemon=True).start()

    # Kick off one cpu_percent call so next call is non-blocking
    psutil.cpu_percent(interval=None)
    psutil.cpu_percent(interval=None, percpu=True)

    print("System Control Center started")

    while pytonium.is_running():
        time.sleep(0.01)
        pytonium.update_message_loop()


if __name__ == "__main__":
    main()
