"""
Pytonium Control Center - Modern Dark UI Demo

A visually impressive showcase of Pytonium's capabilities featuring:
- Modern glassmorphism dark UI
- Real-time Python-JavaScript communication
- Interactive widgets and data visualization
- Window control integration
- State management demonstration
- Async processing with progress updates
- REAL system monitoring via psutil (5 lines vs native Node modules!)
- Data Analysis & Visualization with pandas + matplotlib!

Install dependencies:
    pip install psutil pandas matplotlib openpyxl

The Data Analysis section demonstrates Pytonium's superpower:
- Load CSV/Excel files with pandas
- Display interactive data tables
- Generate professional charts with matplotlib
- All rendered server-side, displayed in the UI

In Electron: Native module nightmare
In Pytonium: Just Python!
"""

import os
import time
import random
import psutil  # Real system stats - this is what makes Pytonium powerful!
from datetime import datetime
from threading import Thread

from Pytonium import Pytonium, returns_value_to_javascript
from data_analyzer import data_analyzer  # pandas + matplotlib - pure Python power!


# ============================================================================
# Real System Monitoring (The Pytonium Advantage!)
# ============================================================================
# In Electron, you'd need native Node modules. In Pytonium, just import psutil!


# ============================================================================
# Window Control Functions
# ============================================================================

@returns_value_to_javascript("boolean")
def window_is_maximized() -> bool:
    """Check if window is maximized."""
    return pytonium.is_maximized()


@returns_value_to_javascript("object")
def window_get_position():
    """Get window position as {x, y}."""
    x, y = pytonium.get_window_position()
    return {"x": x, "y": y}


@returns_value_to_javascript("object")
def window_get_size():
    """Get window size as {width, height}."""
    width, height = pytonium.get_window_size()
    return {"width": width, "height": height}


def window_minimize():
    """Minimize the window."""
    pytonium.minimize_window()


def window_maximize():
    """Toggle maximize/restore."""
    if pytonium.is_maximized():
        pytonium.restore_window()
    else:
        pytonium.maximize_window()


def window_close():
    """Close the application."""
    pytonium.close_window()


def window_drag(delta_x: int, delta_y: int):
    """Drag the window by delta."""
    pytonium.drag_window(delta_x, delta_y)


def window_resize(new_width: int, new_height: int, anchor: int):
    """Resize the window from an anchor point."""
    pytonium.resize_window(new_width, new_height, anchor)


# ============================================================================
# Real System Monitoring (The Pytonium Advantage!)
# ============================================================================
# In Electron: Install native Node modules, compile, deal with platform issues
# In Pytonium: Just "import psutil" - it just works!

# Cache for network stats to calculate speed
_last_net_io = psutil.net_io_counters()
_last_net_time = time.time()

@returns_value_to_javascript("object")
def get_system_stats():
    """
    Returns REAL system statistics using psutil.
    This is the Pytonium advantage - access Python's entire ecosystem!
    """
    global _last_net_io, _last_net_time
    
    # CPU percent (1 second interval for accuracy)
    cpu_percent = psutil.cpu_percent(interval=None)  # Non-blocking
    
    # Memory usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    memory_used_gb = memory.used / (1024**3)
    memory_total_gb = memory.total / (1024**3)
    
    # Disk usage
    disk = psutil.disk_usage('/')
    disk_percent = (disk.used / disk.total) * 100
    
    # Network speed calculation
    current_net_io = psutil.net_io_counters()
    current_time = time.time()
    time_delta = current_time - _last_net_time
    
    if time_delta > 0:
        download_speed = (current_net_io.bytes_recv - _last_net_io.bytes_recv) / time_delta / 1024 / 1024  # MB/s
        upload_speed = (current_net_io.bytes_sent - _last_net_io.bytes_sent) / time_delta / 1024 / 1024  # MB/s
    else:
        download_speed = 0
        upload_speed = 0
    
    _last_net_io = current_net_io
    _last_net_time = current_time
    
    # System uptime
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    
    return {
        "cpu": round(cpu_percent, 1),
        "memory": round(memory_percent, 1),
        "memory_used": round(memory_used_gb, 1),
        "memory_total": round(memory_total_gb, 1),
        "disk": round(disk_percent, 1),
        "download_speed": round(download_speed, 2),
        "upload_speed": round(upload_speed, 2),
        "uptime": int(uptime_seconds),
        "cpu_count": psutil.cpu_count(),
        "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else 0
    }


# Store CPU history for charts
_cpu_history = []

def update_cpu_history():
    """Background thread to collect CPU history for charts."""
    global _cpu_history
    while True:
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            _cpu_history.append(cpu)
            # Keep last 50 data points
            if len(_cpu_history) > 50:
                _cpu_history = _cpu_history[-50:]
        except:
            pass
        time.sleep(0.5)

# Start CPU history collector
Thread(target=update_cpu_history, daemon=True).start()

@returns_value_to_javascript("array")
def get_chart_data():
    """Returns REAL CPU usage history for charts."""
    # Return last 20 data points, or pad with zeros if not enough yet
    data = _cpu_history[-20:] if len(_cpu_history) >= 20 else [0] * (20 - len(_cpu_history)) + _cpu_history
    return [round(x, 1) for x in data]


# ============================================================================
# Async Processing Demo
# ============================================================================

@returns_value_to_javascript("object")
def start_long_task(task_name: str, duration: int):
    """Start a background task with progress updates."""
    task_id = f"task_{int(time.time() * 1000)}"
    
    def run_task():
        for i in range(duration):
            time.sleep(0.1)  # Simulate work
            progress = int((i + 1) / duration * 100)
            pytonium.set_state("tasks", task_id, {
                "name": task_name,
                "progress": progress,
                "status": "running" if progress < 100 else "completed"
            })
    
    Thread(target=run_task, daemon=True).start()
    return {"task_id": task_id, "status": "started"}


# ============================================================================
# Data Processing Demo
# ============================================================================

@returns_value_to_javascript("object")
def process_data(data_type: str, value: float):
    """Process data and return results."""
    if data_type == "temperature":
        # Celsius to Fahrenheit
        fahrenheit = (value * 9/5) + 32
        return {
            "input": f"{value}°C",
            "output": f"{fahrenheit:.1f}°F",
            "formula": "(°C × 9/5) + 32"
        }
    elif data_type == "currency":
        # EUR to USD (simulated rate)
        rate = 1.08 + random.random() * 0.04
        usd = value * rate
        return {
            "input": f"€{value:.2f}",
            "output": f"${usd:.2f}",
            "rate": round(rate, 4)
        }
    elif data_type == "distance":
        # KM to Miles
        miles = value * 0.621371
        return {
            "input": f"{value} km",
            "output": f"{miles:.2f} miles",
            "formula": "km × 0.621371"
        }
    return {"error": "Unknown data type"}


@returns_value_to_javascript("array")
def get_random_color_palette():
    """Generate a random color palette."""
    palettes = [
        {"name": "Ocean", "colors": ["#0077be", "#0099cc", "#00bbdd", "#00ddee", "#a2d9e7"]},
        {"name": "Sunset", "colors": ["#ff6b6b", "#ff8e53", "#ffcd56", "#ff9f40", "#ff6b9d"]},
        {"name": "Forest", "colors": ["#2d6a4f", "#40916c", "#52b788", "#74c69d", "#95d5b2"]},
        {"name": "Neon", "colors": ["#f72585", "#7209b7", "#3a0ca3", "#4361ee", "#4cc9f0"]},
        {"name": "Monochrome", "colors": ["#212529", "#495057", "#6c757d", "#adb5bd", "#dee2e6"]},
    ]
    return [random.choice(palettes)]


# ============================================================================
# Interactive Demo Functions
# ============================================================================

@returns_value_to_javascript("string")
def echo_message(message: str) -> str:
    """Echo a message back with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    return f"[{timestamp}] Python received: {message}"


@returns_value_to_javascript("object")
def analyze_text(text: str):
    """Analyze text and return statistics."""
    words = len(text.split())
    chars = len(text)
    chars_no_spaces = len(text.replace(" ", ""))
    sentences = text.count(".") + text.count("!") + text.count("?")
    
    return {
        "words": words,
        "characters": chars,
        "characters_no_spaces": chars_no_spaces,
        "sentences": max(1, sentences),
        "average_word_length": round(chars_no_spaces / max(1, words), 2)
    }


@returns_value_to_javascript("object")
def get_current_time():
    """Get current time info."""
    now = datetime.now()
    return {
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%A, %B %d, %Y"),
        "timestamp": int(now.timestamp())
    }


# ============================================================================
# Data Analysis & Visualization (pandas + matplotlib)
# ============================================================================
# In Electron: Native modules, compilation, platform-specific binaries
# In Pytonium: pip install pandas matplotlib - pure Python power!

@returns_value_to_javascript("object")
def get_sample_datasets():
    """Get available sample datasets for demonstration."""
    return data_analyzer.get_sample_datasets()


@returns_value_to_javascript("object")
def load_sample_dataset(dataset_name: str):
    """Load a sample dataset into the analyzer."""
    return data_analyzer.load_sample_dataset(dataset_name)


@returns_value_to_javascript("object")
def load_data_file(file_path: str):
    """Load CSV or Excel file."""
    return data_analyzer.load_file(file_path)


@returns_value_to_javascript("object")
def filter_data(column: str, operator: str, value: str):
    """Filter current dataset."""
    return data_analyzer.filter_data(column, operator, value)


@returns_value_to_javascript("object")
def generate_chart(chart_type: str, x_column: str, y_column: str = None,
                   color_column: str = None, title: str = None):
    """
    Generate matplotlib chart and return as base64 image.
    
    This is the killer feature - rendering professional charts server-side
    with matplotlib and displaying them in the web UI!
    """
    return data_analyzer.generate_chart(chart_type, x_column, y_column, 
                                        color_column, title)


# ============================================================================
# State Handler
# ============================================================================

class ControlCenterStateHandler:
    """Handles state updates from JavaScript."""
    
    def update_state(self, namespace: str, key: str, value):
        # State changes are logged but not printed to keep console clean
        pass


# ============================================================================
# Background Update Thread
# ============================================================================

def background_updater():
    """Continuously update system stats and charts."""
    while True:
        time.sleep(0.5)
        if pytonium.is_running():
            try:
                # Update system stats
                stats = get_system_stats()
                pytonium.set_state("system", "stats", stats)
                
                # Update chart data
                chart_data = get_chart_data()
                pytonium.set_state("charts", "cpu_history", chart_data)
                
            except:
                pass


# ============================================================================
# Main Application
# ============================================================================

def main():
    global pytonium, start_time
    start_time = time.time()
    
    # Create Pytonium instance
    pytonium = Pytonium()
    
    # Enable frameless window
    pytonium.set_frameless_window(True)
    
    # =========================================================================
    # Bind Window Control Functions
    # =========================================================================
    pytonium.bind_function_to_javascript(window_is_maximized, "isMaximized", "window")
    pytonium.bind_function_to_javascript(window_get_position, "getPosition", "window")
    pytonium.bind_function_to_javascript(window_get_size, "getSize", "window")
    pytonium.bind_function_to_javascript(window_minimize, "minimize", "window")
    pytonium.bind_function_to_javascript(window_maximize, "maximize", "window")
    pytonium.bind_function_to_javascript(window_close, "close", "window")
    pytonium.bind_function_to_javascript(window_drag, "drag", "window")
    pytonium.bind_function_to_javascript(window_resize, "resize", "window")
    
    # =========================================================================
    # Bind Demo Functions
    # =========================================================================
    pytonium.bind_function_to_javascript(get_system_stats, "getSystemStats", "api")
    pytonium.bind_function_to_javascript(get_chart_data, "getChartData", "api")
    pytonium.bind_function_to_javascript(start_long_task, "startTask", "api")
    pytonium.bind_function_to_javascript(process_data, "processData", "api")
    pytonium.bind_function_to_javascript(get_random_color_palette, "getColorPalette", "api")
    pytonium.bind_function_to_javascript(echo_message, "echo", "api")
    pytonium.bind_function_to_javascript(analyze_text, "analyzeText", "api")
    pytonium.bind_function_to_javascript(get_current_time, "getTime", "api")
    
    # =========================================================================
    # Bind Data Analysis Functions (pandas + matplotlib)
    # =========================================================================
    pytonium.bind_function_to_javascript(get_sample_datasets, "getSampleDatasets", "data")
    pytonium.bind_function_to_javascript(load_sample_dataset, "loadSampleDataset", "data")
    pytonium.bind_function_to_javascript(load_data_file, "loadDataFile", "data")
    pytonium.bind_function_to_javascript(filter_data, "filterData", "data")
    pytonium.bind_function_to_javascript(generate_chart, "generateChart", "data")
    
    # =========================================================================
    # Add State Handler
    # =========================================================================
    state_handler = ControlCenterStateHandler()
    pytonium.add_state_handler(state_handler, ["system", "charts", "tasks", "settings"])
    
    # =========================================================================
    # Initialize and Start
    # =========================================================================
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "index.html")
    
    pytonium.initialize(f"file://{html_path}", 1400, 900)
    
    # Start background updater thread
    updater_thread = Thread(target=background_updater, daemon=True)
    updater_thread.start()
    
    print("=" * 60)
    print("Pytonium Control Center Started!")
    print("=" * 60)
    
    # Main message loop
    while pytonium.is_running():
        time.sleep(0.01)
        pytonium.update_message_loop()


if __name__ == "__main__":
    main()
