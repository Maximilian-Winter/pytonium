# Control Center Redesign - Design Document

**Date:** 2026-03-03
**Status:** Approved
**Scope:** Redesign `pytonium_example_control_center` as a focused hardware/OS dashboard

---

## Overview

Transform the control center example from a sprawling multi-purpose showcase into a focused, clean system monitoring dashboard with safe OS interactions. Remove all data analysis features (pandas, matplotlib, CSV loading, text analysis, unit conversion) — the `data_studio` example already covers that domain.

## Architecture

### Files

```
pytonium_examples/pytonium_example_control_center/
├── main.py          # Python backend: system monitoring + actions
└── index.html       # Dashboard UI: tabs, charts, process table
```

`data_analyzer.py` is eliminated entirely.

### Dependencies

- `psutil` (already used) — the only external dependency
- Chart.js via CDN — for dashboard charts in the frontend

### Python Backend Design

**JS Binding Namespaces:**

| Namespace | Purpose |
|-----------|---------|
| `window`  | Frameless window controls (minimize, maximize, close, drag, resize) |
| `system`  | `getSystemInfo()`, `killProcess(pid)`, `openFolder(path)`, `getDiskPartitions()` |
| `network` | `getConnections()` |

**State Namespaces (pushed every 500ms by background thread):**

| Namespace   | Data |
|-------------|------|
| `stats`     | CPU total/per-core, memory, swap, disk I/O speed, uptime |
| `network`   | Per-interface speeds, IPs, MACs, total up/down |
| `processes` | Top 15 processes by CPU (pid, name, cpu%, memory MB, status) |

**Background Thread:**
- Single daemon thread, 500ms interval
- Calculates network speed from byte counter deltas between ticks
- Calculates disk I/O speed from counter deltas
- Pushes all state via `pytonium.set_state()`

### State Data Shapes

```python
# "stats" namespace, key "stats":
{
    "cpu": 45.2,
    "cpu_per_core": [32, 55, ...],
    "cpu_freq": 3600,
    "memory_percent": 62.1,
    "memory_used": 10737418240,
    "memory_total": 17179869184,
    "swap_percent": 15.0,
    "swap_used": 1073741824,
    "swap_total": 8589934592,
    "disk_read_speed": 52428800,
    "disk_write_speed": 10485760,
    "uptime_seconds": 280800
}

# "network" namespace, key "stats":
{
    "interfaces": [
        {"name": "Ethernet", "ip": "192.168.1.5", "mac": "AA:BB:CC:DD:EE:FF",
         "is_up": true, "speed_down": 1048576, "speed_up": 262144}
    ],
    "total_down": 1048576,
    "total_up": 262144
}

# "processes" namespace, key "list":
{
    "top": [
        {"pid": 1234, "name": "chrome.exe", "cpu": 12.5,
         "memory": 450.2, "status": "running"}
    ]
}
```

### On-Demand API Calls

```python
getSystemInfo() -> dict    # OS, hardware, battery, boot time (one-time)
killProcess(pid) -> dict   # {success: bool, error: str}
openFolder(path) -> bool   # Open in system file explorer
getDiskPartitions() -> list # Partitions with usage stats
getConnections() -> list   # Active network connections (top 20)
```

### Safety Guards

- `killProcess`: Refuses PID 0, PID 4 (System), and own process PID
- `openFolder`: Validates path exists and is a directory before `os.startfile()`

---

## UI Design

### Layout: Tab-Based Panels

5 tabs: **Overview** (default) | **CPU & Processes** | **Memory & Storage** | **Network** | **System**

Frameless window with custom titlebar (existing pattern), min size 900x600.

### Tab Content

**Overview:**
- 4 metric cards in a row: CPU %, RAM %, Disk %, Network speed
- Each card: large value, mini sparkline (30 data points)
- CPU History line chart (Chart.js, 60 points = 30s)
- Quick stats row: Uptime, cores, frequency, OS

**CPU & Processes:**
- Per-core horizontal usage bars (green/yellow/red color coding)
- CPU history chart (larger, total + per-core toggle)
- Top 15 processes table: Name, PID, CPU%, Mem%, Status, Kill button
- Kill button with confirmation dialog

**Memory & Storage:**
- RAM: SVG donut chart + Used/Available/Total + history chart
- Swap: Usage bar + stats (or "No swap")
- Disk partitions: Card per partition with usage bar + Open Folder button

**Network:**
- Per-interface cards: Name, IP, MAC, status, Copy IP button
- Speed chart: dual-axis download (blue) + upload (green) over time
- Active connections table (top 20)

**System:**
- OS info: Name, version, architecture, hostname, username
- Hardware: CPU model, core count, total RAM
- Battery (if present): charge %, plugged in, time remaining
- Uptime + boot time

### Visual Design: Clean Dark Minimal

```css
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
```

**Components:**
- Cards: Flat `bg-secondary`, 1px border, 8px radius, no shadow/blur
- Metric values: Large monospace font (2rem)
- Tab bar: Bottom border highlight on active, no background change
- Tables: Alternating rows, no outer border
- Buttons: Outline style default, filled for destructive (Kill)
- Charts: Dark bg, grid lines in border color, tooltips over legends
- Transitions: 150ms on hover states only
