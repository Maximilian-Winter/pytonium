# Control Center Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rewrite `pytonium_example_control_center` as a focused hardware/OS dashboard with tab-based panels, clean dark minimal UI, Chart.js charts, and safe system interactions (kill process, open folder, copy IP).

**Architecture:** Two-file structure (`main.py` + `index.html`), psutil-only Python backend with background thread pushing stats every 500ms via Pytonium state system, Chart.js CDN for real-time charts, frameless window with custom titlebar.

**Tech Stack:** Python 3.10+, psutil, Pytonium framework, Chart.js (CDN), pure CSS (no framework)

---

### Task 1: Write the new Python backend (`main.py`)

**Files:**
- Rewrite: `pytonium_examples/pytonium_example_control_center/main.py`

**Step 1: Write the complete new `main.py`**

Replace the entire file with the following. This removes all data analysis (pandas/matplotlib), unit conversion, text analysis, echo, color palette, and task demo functions. It adds per-core CPU, disk partitions, network interfaces, active connections, process killing, and folder opening.

```python
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
```

**Step 2: Verify no syntax errors**

Run: `python -c "import ast; ast.parse(open('pytonium_examples/pytonium_example_control_center/main.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add pytonium_examples/pytonium_example_control_center/main.py
git commit -m "refactor(control-center): rewrite backend as focused system dashboard

Remove data analysis (pandas/matplotlib), unit conversion, text analysis.
Add per-core CPU, disk partitions, network interfaces, connections,
process killing, folder opening. psutil-only dependency."
```

---

### Task 2: Delete `data_analyzer.py`

**Files:**
- Delete: `pytonium_examples/pytonium_example_control_center/data_analyzer.py`

**Step 1: Delete the file**

```bash
git rm pytonium_examples/pytonium_example_control_center/data_analyzer.py
```

**Step 2: Commit**

```bash
git commit -m "chore(control-center): remove data_analyzer.py (pandas/matplotlib)

Data analysis features are already covered by the data_studio example."
```

---

### Task 3: Write the new `index.html` — complete rewrite

**Files:**
- Rewrite: `pytonium_examples/pytonium_example_control_center/index.html`

**Step 1: Write the complete new `index.html`**

This is the largest task. The file contains all CSS, HTML structure, and JavaScript for the 5-tab dashboard. Key features:

- **CSS:** Clean dark minimal design system (no glassmorphism, no blur, no glow)
- **HTML:** Tab bar + 5 tab panels (Overview, CPU & Processes, Memory & Storage, Network, System)
- **JS:** Chart.js integration, state event listeners, process killing with confirmation, folder opening, IP copying

The complete file content follows. Because this file is large (~1100 lines), the implementing engineer should write it as a single `Write` operation.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Control Center</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
            --bg-primary: #0f1117;
            --bg-secondary: #1a1d27;
            --bg-tertiary: #242837;
            --border: #2d3348;
            --text-primary: #e4e7ef;
            --text-secondary: #8b92a8;
            --accent-blue: #4a9eff;
            --accent-green: #34d399;
            --accent-yellow: #fbbf24;
            --accent-red: #f87171;
            --accent-purple: #a78bfa;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* ---- Resize Handles ---- */
        .resize-handle { position: fixed; z-index: 10000; }
        .resize-handle.n { top:0; left:8px; right:8px; height:8px; cursor:ns-resize; }
        .resize-handle.s { bottom:0; left:8px; right:8px; height:8px; cursor:ns-resize; }
        .resize-handle.e { top:8px; right:0; bottom:8px; width:8px; cursor:ew-resize; }
        .resize-handle.w { top:8px; left:0; bottom:8px; width:8px; cursor:ew-resize; }
        .resize-handle.nw { top:0; left:0; width:8px; height:8px; cursor:nwse-resize; }
        .resize-handle.ne { top:0; right:0; width:8px; height:8px; cursor:nesw-resize; }
        .resize-handle.sw { bottom:0; left:0; width:8px; height:8px; cursor:nesw-resize; }
        .resize-handle.se { bottom:0; right:0; width:8px; height:8px; cursor:nwse-resize; }

        /* ---- Titlebar ---- */
        .titlebar {
            position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
            height: 48px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            display: flex; align-items: center; justify-content: space-between;
            padding: 0 16px;
            user-select: none;
        }
        .titlebar-left { display: flex; align-items: center; gap: 10px; }
        .title-text { font-size: 14px; font-weight: 600; color: var(--text-primary); }
        .titlebar-controls { display: flex; gap: 4px; }
        .titlebar-btn {
            width: 32px; height: 32px; border: none; border-radius: 6px;
            background: transparent; color: var(--text-secondary);
            cursor: pointer; display: flex; align-items: center; justify-content: center;
            font-size: 13px; transition: background 0.15s, color 0.15s;
        }
        .titlebar-btn:hover { background: var(--bg-tertiary); color: var(--text-primary); }
        .titlebar-btn.close:hover { background: var(--accent-red); color: white; }

        /* ---- Tab Bar ---- */
        .tab-bar {
            position: fixed; top: 48px; left: 0; right: 0; z-index: 999;
            height: 40px;
            background: var(--bg-primary);
            border-bottom: 1px solid var(--border);
            display: flex; align-items: stretch;
            padding: 0 16px;
        }
        .tab-btn {
            background: none; border: none; border-bottom: 2px solid transparent;
            color: var(--text-secondary); font-size: 13px; font-weight: 500;
            padding: 0 16px; cursor: pointer; transition: color 0.15s, border-color 0.15s;
        }
        .tab-btn:hover { color: var(--text-primary); }
        .tab-btn.active { color: var(--accent-blue); border-bottom-color: var(--accent-blue); }

        /* ---- Main Content ---- */
        .main-content {
            padding: 104px 24px 24px;
            max-width: 1400px;
            margin: 0 auto;
        }
        .tab-panel { display: none; }
        .tab-panel.active { display: block; }

        /* ---- Cards ---- */
        .card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
        }
        .card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }
        .metric-card { text-align: center; }
        .metric-label { font-size: 12px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
        .metric-value { font-size: 2rem; font-weight: 700; font-family: 'Consolas', 'SF Mono', monospace; }
        .metric-sub { font-size: 12px; color: var(--text-secondary); margin-top: 4px; }
        .metric-value.green { color: var(--accent-green); }
        .metric-value.yellow { color: var(--accent-yellow); }
        .metric-value.red { color: var(--accent-red); }
        .metric-value.blue { color: var(--accent-blue); }
        .metric-value.purple { color: var(--accent-purple); }

        /* ---- Section Titles ---- */
        .section-title {
            font-size: 13px; font-weight: 600; color: var(--text-secondary);
            text-transform: uppercase; letter-spacing: 0.5px;
            margin-bottom: 12px;
        }

        /* ---- Charts ---- */
        .chart-container { position: relative; height: 250px; margin-bottom: 20px; }
        .chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
        @media (max-width: 900px) { .chart-row { grid-template-columns: 1fr; } }

        /* ---- Core Bars ---- */
        .core-bar-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 8px; margin-bottom: 20px; }
        .core-bar { display: flex; align-items: center; gap: 10px; }
        .core-bar-label { font-size: 12px; color: var(--text-secondary); min-width: 60px; font-family: monospace; }
        .core-bar-track { flex: 1; height: 16px; background: var(--bg-tertiary); border-radius: 4px; overflow: hidden; }
        .core-bar-fill { height: 100%; border-radius: 4px; transition: width 0.3s, background-color 0.3s; }
        .core-bar-pct { font-size: 12px; min-width: 40px; text-align: right; font-family: monospace; }

        /* ---- Process Table ---- */
        .table-wrap { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { text-align: left; padding: 10px 12px; color: var(--text-secondary); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }
        td { padding: 8px 12px; border-bottom: 1px solid var(--border); }
        tr:hover td { background: var(--bg-tertiary); }
        tr:last-child td { border-bottom: none; }

        /* ---- Buttons ---- */
        .btn {
            padding: 6px 14px; border: 1px solid var(--border); border-radius: 6px;
            background: transparent; color: var(--text-secondary); font-size: 12px;
            cursor: pointer; transition: all 0.15s;
        }
        .btn:hover { border-color: var(--text-secondary); color: var(--text-primary); }
        .btn-danger { border-color: var(--accent-red); color: var(--accent-red); }
        .btn-danger:hover { background: var(--accent-red); color: white; }
        .btn-small { padding: 4px 10px; font-size: 11px; }

        /* ---- Usage Bars (disk partitions) ---- */
        .usage-bar-track { width: 100%; height: 8px; background: var(--bg-tertiary); border-radius: 4px; overflow: hidden; margin-top: 8px; }
        .usage-bar-fill { height: 100%; border-radius: 4px; }

        /* ---- Network Interface Cards ---- */
        .if-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin-bottom: 20px; }
        .if-card { padding: 16px; }
        .if-name { font-weight: 600; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
        .if-status { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
        .if-status.up { background: var(--accent-green); }
        .if-status.down { background: var(--accent-red); }
        .if-detail { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; display: flex; justify-content: space-between; }

        /* ---- Partition Cards ---- */
        .partition-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; margin-bottom: 20px; }
        .partition-card { padding: 16px; }
        .partition-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .partition-device { font-weight: 600; font-family: monospace; }
        .partition-details { font-size: 12px; color: var(--text-secondary); }
        .partition-details span { margin-right: 12px; }

        /* ---- System Info Grid ---- */
        .info-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
        .info-card { padding: 20px; }
        .info-card h3 { font-size: 14px; margin-bottom: 12px; color: var(--accent-blue); }
        .info-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
        .info-row:last-child { border-bottom: none; }
        .info-label { color: var(--text-secondary); }
        .info-value { font-family: monospace; text-align: right; }

        /* ---- Donut Chart (SVG) ---- */
        .donut-wrap { display: flex; align-items: center; gap: 24px; margin-bottom: 20px; }
        .donut-svg { width: 120px; height: 120px; }
        .donut-center { font-size: 1.5rem; font-weight: 700; font-family: monospace; }
        .donut-legend { font-size: 13px; }
        .donut-legend div { margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }
        .donut-legend .dot { width: 10px; height: 10px; border-radius: 50%; }

        /* ---- Confirm Dialog ---- */
        .dialog-overlay {
            display: none; position: fixed; inset: 0; z-index: 9999;
            background: rgba(0,0,0,0.6); align-items: center; justify-content: center;
        }
        .dialog-overlay.show { display: flex; }
        .dialog-box {
            background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 10px;
            padding: 24px; min-width: 360px; max-width: 440px;
        }
        .dialog-box h3 { margin-bottom: 12px; font-size: 16px; }
        .dialog-box p { color: var(--text-secondary); font-size: 14px; margin-bottom: 20px; }
        .dialog-actions { display: flex; gap: 10px; justify-content: flex-end; }
        .dialog-actions .btn { padding: 8px 20px; font-size: 13px; }

        /* ---- Quick Stats Row ---- */
        .quick-stats { display: flex; flex-wrap: wrap; gap: 24px; margin-top: 12px; }
        .quick-stat { font-size: 13px; color: var(--text-secondary); }
        .quick-stat strong { color: var(--text-primary); margin-left: 4px; }
    </style>
</head>
<body>

<!-- Resize Handles -->
<div class="resize-handle n" data-edge="n"></div>
<div class="resize-handle s" data-edge="s"></div>
<div class="resize-handle e" data-edge="e"></div>
<div class="resize-handle w" data-edge="w"></div>
<div class="resize-handle nw" data-corner="nw"></div>
<div class="resize-handle ne" data-corner="ne"></div>
<div class="resize-handle sw" data-corner="sw"></div>
<div class="resize-handle se" data-corner="se"></div>

<!-- Titlebar -->
<div class="titlebar" id="titlebar">
    <div class="titlebar-left">
        <span class="title-text">System Control Center</span>
    </div>
    <div class="titlebar-controls">
        <button class="titlebar-btn" onclick="Pytonium.window.minimize()" title="Minimize">&#x2014;</button>
        <button class="titlebar-btn" onclick="Pytonium.window.maximize()" title="Maximize">&#x25A1;</button>
        <button class="titlebar-btn close" onclick="Pytonium.window.close()" title="Close">&#x2715;</button>
    </div>
</div>

<!-- Tab Bar -->
<div class="tab-bar">
    <button class="tab-btn active" data-tab="overview">Overview</button>
    <button class="tab-btn" data-tab="cpu">CPU &amp; Processes</button>
    <button class="tab-btn" data-tab="memory">Memory &amp; Storage</button>
    <button class="tab-btn" data-tab="network">Network</button>
    <button class="tab-btn" data-tab="system">System</button>
</div>

<!-- Main Content -->
<div class="main-content">

    <!-- ===== OVERVIEW TAB ===== -->
    <div class="tab-panel active" id="tab-overview">
        <div class="card-grid">
            <div class="card metric-card">
                <div class="metric-label">CPU Usage</div>
                <div class="metric-value" id="ov-cpu">--</div>
                <div class="metric-sub" id="ov-cpu-sub">--</div>
            </div>
            <div class="card metric-card">
                <div class="metric-label">Memory</div>
                <div class="metric-value" id="ov-mem">--</div>
                <div class="metric-sub" id="ov-mem-sub">--</div>
            </div>
            <div class="card metric-card">
                <div class="metric-label">Network</div>
                <div class="metric-value blue" id="ov-net">--</div>
                <div class="metric-sub" id="ov-net-sub">--</div>
            </div>
            <div class="card metric-card">
                <div class="metric-label">Uptime</div>
                <div class="metric-value purple" id="ov-uptime">--</div>
                <div class="metric-sub" id="ov-uptime-sub">--</div>
            </div>
        </div>
        <div class="chart-row">
            <div class="card">
                <div class="section-title">CPU History</div>
                <div class="chart-container"><canvas id="chart-ov-cpu"></canvas></div>
            </div>
            <div class="card">
                <div class="section-title">Memory History</div>
                <div class="chart-container"><canvas id="chart-ov-mem"></canvas></div>
            </div>
        </div>
        <div class="card" style="padding: 16px;">
            <div class="quick-stats" id="ov-quick-stats"></div>
        </div>
    </div>

    <!-- ===== CPU & PROCESSES TAB ===== -->
    <div class="tab-panel" id="tab-cpu">
        <div class="section-title">Per-Core Usage</div>
        <div class="card" style="margin-bottom: 20px; padding: 16px;">
            <div class="core-bar-list" id="core-bars"></div>
        </div>
        <div class="card" style="margin-bottom: 20px;">
            <div class="section-title">CPU History</div>
            <div class="chart-container"><canvas id="chart-cpu-history"></canvas></div>
        </div>
        <div class="card">
            <div class="section-title">Top Processes</div>
            <div class="table-wrap">
                <table>
                    <thead><tr>
                        <th>Name</th><th>PID</th><th>CPU %</th><th>Memory (MB)</th><th>Status</th><th></th>
                    </tr></thead>
                    <tbody id="process-table"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- ===== MEMORY & STORAGE TAB ===== -->
    <div class="tab-panel" id="tab-memory">
        <div class="card-grid" style="grid-template-columns: 1fr 1fr;">
            <div class="card">
                <div class="section-title">RAM Usage</div>
                <div class="donut-wrap">
                    <svg class="donut-svg" viewBox="0 0 36 36" id="ram-donut">
                        <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--bg-tertiary)" stroke-width="3"/>
                        <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--accent-blue)" stroke-width="3"
                            stroke-dasharray="0 100" stroke-linecap="round" id="ram-donut-fill"
                            transform="rotate(-90 18 18)"/>
                        <text x="18" y="19" text-anchor="middle" dominant-baseline="middle"
                            fill="var(--text-primary)" font-size="6" font-weight="bold" font-family="monospace"
                            id="ram-donut-text">--%</text>
                    </svg>
                    <div class="donut-legend" id="ram-legend"></div>
                </div>
            </div>
            <div class="card">
                <div class="section-title">Swap</div>
                <div class="donut-wrap">
                    <svg class="donut-svg" viewBox="0 0 36 36" id="swap-donut">
                        <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--bg-tertiary)" stroke-width="3"/>
                        <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--accent-purple)" stroke-width="3"
                            stroke-dasharray="0 100" stroke-linecap="round" id="swap-donut-fill"
                            transform="rotate(-90 18 18)"/>
                        <text x="18" y="19" text-anchor="middle" dominant-baseline="middle"
                            fill="var(--text-primary)" font-size="6" font-weight="bold" font-family="monospace"
                            id="swap-donut-text">--%</text>
                    </svg>
                    <div class="donut-legend" id="swap-legend"></div>
                </div>
            </div>
        </div>
        <div class="card" style="margin-bottom: 20px;">
            <div class="section-title">Memory History</div>
            <div class="chart-container"><canvas id="chart-mem-history"></canvas></div>
        </div>
        <div class="section-title">Disk Partitions</div>
        <div class="partition-grid" id="disk-partitions"></div>
    </div>

    <!-- ===== NETWORK TAB ===== -->
    <div class="tab-panel" id="tab-network">
        <div class="section-title">Interfaces</div>
        <div class="if-grid" id="net-interfaces"></div>
        <div class="card" style="margin-bottom: 20px;">
            <div class="section-title">Network Speed</div>
            <div class="chart-container"><canvas id="chart-net-speed"></canvas></div>
        </div>
        <div class="card">
            <div class="section-title" style="display: flex; justify-content: space-between; align-items: center;">
                Active Connections
                <button class="btn btn-small" onclick="refreshConnections()">Refresh</button>
            </div>
            <div class="table-wrap">
                <table>
                    <thead><tr>
                        <th>Local Address</th><th>Remote Address</th><th>Status</th><th>Process</th>
                    </tr></thead>
                    <tbody id="connections-table"></tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- ===== SYSTEM TAB ===== -->
    <div class="tab-panel" id="tab-system">
        <div class="info-grid" id="system-info-grid">
            <div class="card info-card" style="grid-column: 1 / -1; text-align: center; color: var(--text-secondary);">
                Loading system information...
            </div>
        </div>
    </div>
</div>

<!-- Kill Process Confirm Dialog -->
<div class="dialog-overlay" id="kill-dialog">
    <div class="dialog-box">
        <h3>Kill Process</h3>
        <p id="kill-dialog-msg">Are you sure you want to kill this process?</p>
        <div class="dialog-actions">
            <button class="btn" onclick="closeKillDialog()">Cancel</button>
            <button class="btn btn-danger" onclick="confirmKill()">Kill Process</button>
        </div>
    </div>
</div>

<script>
// ========================================================================
// Tab Navigation
// ========================================================================
const tabBtns = document.querySelectorAll('.tab-btn');
const tabPanels = document.querySelectorAll('.tab-panel');
let activeTab = 'overview';

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        activeTab = tab;
        tabBtns.forEach(b => b.classList.remove('active'));
        tabPanels.forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('tab-' + tab).classList.add('active');

        // Load on-demand data when switching to tabs
        if (tab === 'memory') loadDiskPartitions();
        if (tab === 'network') refreshConnections();
        if (tab === 'system') loadSystemInfo();
    });
});

// ========================================================================
// Helpers
// ========================================================================
function formatBytes(bytes) {
    if (bytes < 1024) return bytes.toFixed(0) + ' B/s';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB/s';
    return (bytes / 1024 / 1024).toFixed(2) + ' MB/s';
}

function formatUptime(seconds) {
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (d > 0) return d + 'd ' + h + 'h';
    if (h > 0) return h + 'h ' + m + 'm';
    return m + 'm';
}

function usageColor(pct) {
    if (pct < 50) return 'var(--accent-green)';
    if (pct < 80) return 'var(--accent-yellow)';
    return 'var(--accent-red)';
}

function usageClass(pct) {
    if (pct < 50) return 'green';
    if (pct < 80) return 'yellow';
    return 'red';
}

// ========================================================================
// Chart.js Setup
// ========================================================================
const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    plugins: { legend: { display: false } },
    scales: {
        x: { display: false },
        y: {
            beginAtZero: true,
            grid: { color: 'rgba(45, 51, 72, 0.5)' },
            ticks: { color: '#8b92a8', font: { size: 11 } },
        }
    }
};

function makeLineChart(canvasId, label, color, maxY) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array(60).fill(''),
            datasets: [{
                label: label,
                data: Array(60).fill(null),
                borderColor: color,
                backgroundColor: color + '20',
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2,
            }]
        },
        options: {
            ...chartDefaults,
            scales: {
                ...chartDefaults.scales,
                y: { ...chartDefaults.scales.y, max: maxY || undefined }
            }
        }
    });
}

function makeDualLineChart(canvasId, label1, color1, label2, color2) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array(60).fill(''),
            datasets: [
                {
                    label: label1, data: Array(60).fill(null),
                    borderColor: color1, backgroundColor: color1 + '20',
                    fill: true, tension: 0.3, pointRadius: 0, borderWidth: 2,
                },
                {
                    label: label2, data: Array(60).fill(null),
                    borderColor: color2, backgroundColor: color2 + '20',
                    fill: true, tension: 0.3, pointRadius: 0, borderWidth: 2,
                }
            ]
        },
        options: {
            ...chartDefaults,
            plugins: {
                legend: {
                    display: true,
                    labels: { color: '#8b92a8', boxWidth: 12, font: { size: 11 } }
                }
            }
        }
    });
}

// Create charts
let chartOvCpu, chartOvMem, chartCpuHistory, chartMemHistory, chartNetSpeed;

// ========================================================================
// State Event Handlers
// ========================================================================
function updateStats(stats) {
    // Overview tab
    const cpuPct = stats.cpu + '%';
    const memPct = stats.memory_percent + '%';
    document.getElementById('ov-cpu').textContent = cpuPct;
    document.getElementById('ov-cpu').className = 'metric-value ' + usageClass(stats.cpu);
    document.getElementById('ov-cpu-sub').textContent = stats.cpu_per_core.length + ' cores @ ' + stats.cpu_freq + ' MHz';

    document.getElementById('ov-mem').textContent = memPct;
    document.getElementById('ov-mem').className = 'metric-value ' + usageClass(stats.memory_percent);
    document.getElementById('ov-mem-sub').textContent = stats.memory_used_gb + ' / ' + stats.memory_total_gb + ' GB';

    document.getElementById('ov-uptime').textContent = formatUptime(stats.uptime_seconds);
    const days = Math.floor(stats.uptime_seconds / 86400);
    const hours = Math.floor((stats.uptime_seconds % 86400) / 3600);
    const mins = Math.floor((stats.uptime_seconds % 3600) / 60);
    document.getElementById('ov-uptime-sub').textContent = days + 'd ' + hours + 'h ' + mins + 'm';

    // Quick stats
    document.getElementById('ov-quick-stats').innerHTML =
        '<div class="quick-stat">Cores:<strong>' + stats.cpu_per_core.length + '</strong></div>' +
        '<div class="quick-stat">Frequency:<strong>' + stats.cpu_freq + ' MHz</strong></div>' +
        '<div class="quick-stat">Disk Read:<strong>' + formatBytes(stats.disk_read_speed) + '</strong></div>' +
        '<div class="quick-stat">Disk Write:<strong>' + formatBytes(stats.disk_write_speed) + '</strong></div>';

    // Update charts
    if (stats.cpu_history && chartOvCpu) {
        chartOvCpu.data.labels = stats.cpu_history.map((_, i) => i);
        chartOvCpu.data.datasets[0].data = stats.cpu_history;
        chartOvCpu.update('none');
    }
    if (stats.mem_history && chartOvMem) {
        chartOvMem.data.labels = stats.mem_history.map((_, i) => i);
        chartOvMem.data.datasets[0].data = stats.mem_history;
        chartOvMem.update('none');
    }

    // CPU tab charts
    if (stats.cpu_history && chartCpuHistory) {
        chartCpuHistory.data.labels = stats.cpu_history.map((_, i) => i);
        chartCpuHistory.data.datasets[0].data = stats.cpu_history;
        chartCpuHistory.update('none');
    }

    // Memory tab chart
    if (stats.mem_history && chartMemHistory) {
        chartMemHistory.data.labels = stats.mem_history.map((_, i) => i);
        chartMemHistory.data.datasets[0].data = stats.mem_history;
        chartMemHistory.update('none');
    }

    // Per-core bars (CPU tab)
    const barsEl = document.getElementById('core-bars');
    if (barsEl && stats.cpu_per_core) {
        let html = '';
        stats.cpu_per_core.forEach((pct, i) => {
            html += '<div class="core-bar">' +
                '<span class="core-bar-label">Core ' + i + '</span>' +
                '<div class="core-bar-track"><div class="core-bar-fill" style="width:' + pct + '%; background:' + usageColor(pct) + ';"></div></div>' +
                '<span class="core-bar-pct">' + pct + '%</span></div>';
        });
        barsEl.innerHTML = html;
    }

    // Memory tab donut
    const ramFill = document.getElementById('ram-donut-fill');
    const ramText = document.getElementById('ram-donut-text');
    const ramLegend = document.getElementById('ram-legend');
    if (ramFill) {
        ramFill.setAttribute('stroke-dasharray', (stats.memory_percent) + ' ' + (100 - stats.memory_percent));
        ramFill.setAttribute('stroke', usageColor(stats.memory_percent));
        ramText.textContent = stats.memory_percent + '%';
        ramLegend.innerHTML =
            '<div><span class="dot" style="background:' + usageColor(stats.memory_percent) + '"></span>Used: ' + stats.memory_used_gb + ' GB</div>' +
            '<div><span class="dot" style="background:var(--bg-tertiary)"></span>Available: ' + stats.memory_available_gb + ' GB</div>' +
            '<div><span class="dot" style="background:var(--text-secondary)"></span>Total: ' + stats.memory_total_gb + ' GB</div>';
    }

    // Swap donut
    const swapFill = document.getElementById('swap-donut-fill');
    const swapText = document.getElementById('swap-donut-text');
    const swapLegend = document.getElementById('swap-legend');
    if (swapFill) {
        if (stats.swap_total_gb > 0) {
            swapFill.setAttribute('stroke-dasharray', stats.swap_percent + ' ' + (100 - stats.swap_percent));
            swapText.textContent = stats.swap_percent + '%';
            swapLegend.innerHTML =
                '<div><span class="dot" style="background:var(--accent-purple)"></span>Used: ' + stats.swap_used_gb + ' GB</div>' +
                '<div><span class="dot" style="background:var(--bg-tertiary)"></span>Total: ' + stats.swap_total_gb + ' GB</div>';
        } else {
            swapFill.setAttribute('stroke-dasharray', '0 100');
            swapText.textContent = 'N/A';
            swapLegend.innerHTML = '<div style="color:var(--text-secondary)">No swap configured</div>';
        }
    }
}

function updateNetwork(data) {
    // Overview network card
    document.getElementById('ov-net').textContent = formatBytes(data.total_down);
    document.getElementById('ov-net-sub').textContent = '\u2193 ' + formatBytes(data.total_down) + '  \u2191 ' + formatBytes(data.total_up);

    // Network interfaces (Network tab)
    const ifGrid = document.getElementById('net-interfaces');
    if (ifGrid && data.interfaces) {
        let html = '';
        data.interfaces.forEach(iface => {
            if (!iface.ip && !iface.is_up) return; // Skip inactive with no IP
            html += '<div class="card if-card">' +
                '<div class="if-name"><span class="if-status ' + (iface.is_up ? 'up' : 'down') + '"></span>' + iface.name + '</div>' +
                '<div class="if-detail"><span>IP</span><span>' + (iface.ip || 'N/A') +
                (iface.ip ? ' <button class="btn btn-small" onclick="copyIP(\'' + iface.ip + '\')">Copy</button>' : '') +
                '</span></div>' +
                '<div class="if-detail"><span>MAC</span><span>' + (iface.mac || 'N/A') + '</span></div>' +
                '</div>';
        });
        ifGrid.innerHTML = html;
    }

    // Network speed chart
    if (chartNetSpeed && data.total_down !== undefined) {
        // We get history from stats, not network — but we also update live
    }
}

function updateProcesses(data) {
    const tbody = document.getElementById('process-table');
    if (!tbody || !data.top) return;
    let html = '';
    data.top.forEach(proc => {
        html += '<tr>' +
            '<td>' + proc.name + '</td>' +
            '<td style="font-family:monospace; color:var(--text-secondary);">' + proc.pid + '</td>' +
            '<td style="color:' + usageColor(proc.cpu) + '">' + proc.cpu + '%</td>' +
            '<td>' + proc.memory + '</td>' +
            '<td style="color:var(--text-secondary)">' + proc.status + '</td>' +
            '<td><button class="btn btn-danger btn-small" onclick="showKillDialog(' + proc.pid + ', \'' + proc.name.replace(/'/g, "\\'") + '\')">Kill</button></td>' +
            '</tr>';
    });
    tbody.innerHTML = html;
}

// ========================================================================
// Network speed chart from stats history
// ========================================================================
function updateNetChartFromStats(stats) {
    if (!chartNetSpeed) return;
    if (stats.net_down_history) {
        chartNetSpeed.data.labels = stats.net_down_history.map((_, i) => i);
        chartNetSpeed.data.datasets[0].data = stats.net_down_history;
    }
    if (stats.net_up_history) {
        chartNetSpeed.data.datasets[1].data = stats.net_up_history;
    }
    chartNetSpeed.update('none');
}

// ========================================================================
// On-Demand Data Loading
// ========================================================================
async function loadDiskPartitions() {
    try {
        const partitions = await Pytonium.system.getDiskPartitions();
        const grid = document.getElementById('disk-partitions');
        if (!grid) return;
        let html = '';
        partitions.forEach(p => {
            html += '<div class="card partition-card">' +
                '<div class="partition-header">' +
                '<span class="partition-device">' + p.device + '</span>' +
                '<button class="btn btn-small" onclick="openFolder(\'' + p.mountpoint.replace(/\\/g, '\\\\') + '\')">Open</button>' +
                '</div>' +
                '<div class="partition-details">' +
                '<span>' + p.fstype + '</span>' +
                '<span>' + p.used_gb + ' / ' + p.total_gb + ' GB (' + p.percent + '%)</span>' +
                '</div>' +
                '<div class="usage-bar-track"><div class="usage-bar-fill" style="width:' + p.percent + '%; background:' + usageColor(p.percent) + ';"></div></div>' +
                '</div>';
        });
        grid.innerHTML = html;
    } catch (e) { console.error('Failed to load partitions:', e); }
}

async function loadSystemInfo() {
    try {
        const info = await Pytonium.system.getSystemInfo();
        const grid = document.getElementById('system-info-grid');
        if (!grid) return;

        let html = '';
        // OS card
        html += '<div class="card info-card"><h3>Operating System</h3>';
        html += infoRow('OS', info.os_name);
        html += infoRow('Version', info.os_version);
        html += infoRow('Architecture', info.architecture);
        html += infoRow('Hostname', info.hostname);
        html += infoRow('Username', info.username);
        html += '</div>';

        // Hardware card
        html += '<div class="card info-card"><h3>Hardware</h3>';
        html += infoRow('CPU', info.cpu_model);
        html += infoRow('Physical Cores', info.cpu_cores_physical);
        html += infoRow('Logical Cores', info.cpu_cores_logical);
        html += infoRow('Max Frequency', info.cpu_freq_max + ' MHz');
        html += infoRow('Total RAM', info.ram_total_gb + ' GB');
        html += '</div>';

        // Runtime card
        html += '<div class="card info-card"><h3>Runtime</h3>';
        html += infoRow('Boot Time', info.boot_time);
        html += infoRow('Python', info.python_version);
        html += '</div>';

        // Battery card (if present)
        if (info.battery_percent !== null) {
            html += '<div class="card info-card"><h3>Battery</h3>';
            html += infoRow('Charge', info.battery_percent + '%');
            html += infoRow('Plugged In', info.battery_plugged ? 'Yes' : 'No');
            if (info.battery_secs_left > 0) {
                html += infoRow('Time Left', formatUptime(info.battery_secs_left));
            }
            html += '</div>';
        }

        grid.innerHTML = html;
    } catch (e) { console.error('Failed to load system info:', e); }
}

function infoRow(label, value) {
    return '<div class="info-row"><span class="info-label">' + label + '</span><span class="info-value">' + value + '</span></div>';
}

async function refreshConnections() {
    try {
        const conns = await Pytonium.network.getConnections();
        const tbody = document.getElementById('connections-table');
        if (!tbody) return;
        if (conns.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--text-secondary);">No connections found (may require admin)</td></tr>';
            return;
        }
        let html = '';
        conns.forEach(c => {
            html += '<tr>' +
                '<td style="font-family:monospace; font-size:12px;">' + c.local + '</td>' +
                '<td style="font-family:monospace; font-size:12px;">' + (c.remote || '-') + '</td>' +
                '<td style="color:' + (c.status === 'ESTABLISHED' ? 'var(--accent-green)' : 'var(--text-secondary)') + '">' + c.status + '</td>' +
                '<td>' + c.process + '</td>' +
                '</tr>';
        });
        tbody.innerHTML = html;
    } catch (e) { console.error('Failed to load connections:', e); }
}

// ========================================================================
// Actions
// ========================================================================
function copyIP(ip) {
    navigator.clipboard.writeText(ip).catch(() => {});
}

async function openFolder(path) {
    await Pytonium.system.openFolder(path);
}

// Kill process dialog
let killTargetPid = null;

function showKillDialog(pid, name) {
    killTargetPid = pid;
    document.getElementById('kill-dialog-msg').textContent = 'Kill "' + name + '" (PID ' + pid + ')?';
    document.getElementById('kill-dialog').classList.add('show');
}

function closeKillDialog() {
    killTargetPid = null;
    document.getElementById('kill-dialog').classList.remove('show');
}

async function confirmKill() {
    if (killTargetPid === null) return;
    const result = await Pytonium.system.killProcess(killTargetPid);
    closeKillDialog();
    if (!result.success) {
        alert('Failed: ' + result.error);
    }
}

// ========================================================================
// Window Resize Handles (standard pattern)
// ========================================================================
document.querySelectorAll('.resize-handle').forEach(handle => {
    handle.addEventListener('mousedown', async (e) => {
        e.preventDefault();
        const edge = handle.dataset.edge;
        const corner = handle.dataset.corner;
        const isMaximized = await Pytonium.window.isMaximized();
        if (isMaximized) return;
        const startSize = await Pytonium.window.getSize();
        const startPos = await Pytonium.window.getPosition();
        const startX = e.screenX, startY = e.screenY;
        const minW = 900, minH = 600;

        function onMove(ev) {
            const dx = ev.screenX - startX, dy = ev.screenY - startY;
            let w = startSize.width, h = startSize.height;
            let anchor = 0;

            if (edge === 'e' || corner === 'ne' || corner === 'se') { w = Math.max(minW, startSize.width + dx); }
            if (edge === 'w' || corner === 'nw' || corner === 'sw') { w = Math.max(minW, startSize.width - dx); anchor = (anchor === 0) ? 1 : anchor; }
            if (edge === 's' || corner === 'sw' || corner === 'se') { h = Math.max(minH, startSize.height + dy); }
            if (edge === 'n' || corner === 'nw' || corner === 'ne') { h = Math.max(minH, startSize.height - dy); anchor = (corner === 'ne') ? 1 : (corner === 'nw') ? 1 : 0; }

            if (corner === 'nw') anchor = 3;
            else if (corner === 'ne') anchor = 2;
            else if (corner === 'sw') anchor = 1;
            else if (corner === 'se') anchor = 0;
            else if (edge === 'n') anchor = 2;
            else if (edge === 'w') anchor = 1;
            else anchor = 0;

            Pytonium.window.resize(w, h, anchor);
        }
        function onUp() {
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
        }
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    });
});

// Titlebar drag
document.getElementById('titlebar').addEventListener('mousedown', (e) => {
    if (e.target.tagName === 'BUTTON' || e.target.closest('.titlebar-controls')) return;
    Pytonium.window.startDrag();
});

// ========================================================================
// Initialization
// ========================================================================
function Init() {
    // Register state listeners
    Pytonium.appState.registerForStateUpdates('StatsUpdate', ['stats'], true, true);
    Pytonium.appState.registerForStateUpdates('NetworkUpdate', ['network'], true, true);
    Pytonium.appState.registerForStateUpdates('ProcessUpdate', ['processes'], true, true);

    document.addEventListener('StatsUpdate', (e) => {
        if (e.detail.key === 'stats') {
            updateStats(e.detail.value);
            updateNetChartFromStats(e.detail.value);
        }
    });

    document.addEventListener('NetworkUpdate', (e) => {
        if (e.detail.key === 'stats') updateNetwork(e.detail.value);
    });

    document.addEventListener('ProcessUpdate', (e) => {
        if (e.detail.key === 'list') updateProcesses(e.detail.value);
    });

    // Create charts
    chartOvCpu = makeLineChart('chart-ov-cpu', 'CPU %', '#4a9eff', 100);
    chartOvMem = makeLineChart('chart-ov-mem', 'Memory %', '#34d399', 100);
    chartCpuHistory = makeLineChart('chart-cpu-history', 'CPU %', '#4a9eff', 100);
    chartMemHistory = makeLineChart('chart-mem-history', 'Memory %', '#34d399', 100);
    chartNetSpeed = makeDualLineChart('chart-net-speed', 'Download', '#4a9eff', 'Upload', '#34d399');

    // Load initial data for default tab (overview is auto-updated via state)
    // System info loads on tab switch
}

if (window.PytoniumReady) { Init(); }
else { window.addEventListener('PytoniumReady', Init); }
</script>
</body>
</html>
```

**Step 2: Verify file is well-formed HTML**

Open the file in a text editor and check that all tags are closed properly. The file should be approximately 500-600 lines.

**Step 3: Commit**

```bash
git add pytonium_examples/pytonium_example_control_center/index.html
git commit -m "feat(control-center): rewrite UI as tab-based system dashboard

5 tabs: Overview, CPU & Processes, Memory & Storage, Network, System.
Chart.js for real-time charts. Clean dark minimal design (no glassmorphism).
Kill process with confirmation, open folder, copy IP actions."
```

---

### Task 4: Smoke test

**Step 1: Verify Python imports and syntax**

Run:
```bash
cd pytonium_examples/pytonium_example_control_center
python -c "import ast; ast.parse(open('main.py').read()); print('Syntax OK')"
```
Expected: `Syntax OK`

**Step 2: Verify psutil functions work standalone**

Run:
```bash
python -c "
import psutil, platform, os
print('CPU:', psutil.cpu_percent(interval=0.1))
print('Cores:', psutil.cpu_count())
print('Memory:', round(psutil.virtual_memory().percent, 1), '%')
print('Disk:', [p.mountpoint for p in psutil.disk_partitions(all=False)])
print('Net interfaces:', len(psutil.net_if_addrs()))
print('OS:', platform.uname().system, platform.uname().release)
print('All OK')
"
```
Expected: System stats printed, ending with `All OK`

**Step 3: Run the full application (manual)**

Run:
```bash
cd pytonium_examples/pytonium_example_control_center
python main.py
```

Verify:
- [ ] Window opens with "System Control Center" title
- [ ] Overview tab shows CPU, Memory, Network, Uptime cards
- [ ] CPU and Memory history charts update in real-time
- [ ] Click "CPU & Processes" tab — per-core bars visible, process table populated
- [ ] Kill button shows confirmation dialog
- [ ] Click "Memory & Storage" tab — RAM/Swap donut charts, disk partitions with Open button
- [ ] Click "Network" tab — interface cards with Copy IP, speed chart, connections table
- [ ] Click "System" tab — OS, Hardware, Runtime info cards
- [ ] Window drag works from titlebar
- [ ] Window resize works from edges/corners
- [ ] Minimize/maximize/close buttons work

**Step 4: Final commit if any fixes needed**

```bash
git add -u pytonium_examples/pytonium_example_control_center/
git commit -m "fix(control-center): post-smoke-test fixes"
```

---

### Task 5: Final cleanup commit

**Step 1: Verify `data_analyzer.py` is gone and no references remain**

Run:
```bash
grep -r "data_analyzer" pytonium_examples/pytonium_example_control_center/
```
Expected: No output (no references)

Run:
```bash
grep -r "pandas\|matplotlib\|openpyxl" pytonium_examples/pytonium_example_control_center/
```
Expected: No output (no data analysis dependencies)

**Step 2: Verify only 2 files remain**

Run:
```bash
ls pytonium_examples/pytonium_example_control_center/
```
Expected: `main.py  index.html`

**Step 3: Commit any remaining cleanup**

If everything is clean from previous commits, no additional commit needed.
