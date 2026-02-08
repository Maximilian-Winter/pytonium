"""
Pytonium Data Studio - Data Analysis & Visualization Demo

This example showcases Pytonium's data analysis capabilities using:
- pandas: Data manipulation and analysis  
- matplotlib: Professional chart generation

Features:
- Load CSV/Excel files via drag & drop or file picker
- Auto-analysis: instant overview with smart visualizations
- Data handle pattern: efficient handling of large files
- Color-coded column types with detailed statistics

Install dependencies:
    pip install pandas matplotlib openpyxl
"""

import os
import sys
import time
from pathlib import Path
from threading import Thread

from Pytonium import Pytonium, returns_value_to_javascript
from data_manager import data_manager


# ============================================================================
# Window Control Functions
# ============================================================================

@returns_value_to_javascript("boolean")
def window_is_maximized() -> bool:
    return pytonium.is_maximized()


def window_minimize():
    pytonium.minimize_window()


def window_maximize():
    if pytonium.is_maximized():
        pytonium.restore_window()
    else:
        pytonium.maximize_window()


def window_close():
    pytonium.close_window()


def window_drag(delta_x: int, delta_y: int):
    pytonium.drag_window(delta_x, delta_y)


def window_resize(new_width: int, new_height: int, anchor: int):
    pytonium.resize_window(new_width, new_height, anchor)


# ============================================================================
# Data Management API (Using Data Handle Pattern)
# ============================================================================

@returns_value_to_javascript("object")
def load_file(file_path: str) -> dict:
    """
    Load a CSV or Excel file and return a data handle.
    The actual data stays in Python - only the ID and summaries go to JS.
    """
    # Handle relative paths
    if not os.path.isabs(file_path):
        file_path = os.path.join(os.path.dirname(__file__), file_path)
    
    result = data_manager.load_file(file_path)
    
    if "error" not in result:
        print(f"[Data Studio] Loaded: {file_path}")
        print(f"              ID: {result['data_id']}")
        print(f"              Rows: {result['info']['rows']:,}")
        print(f"              Cols: {result['info']['columns']}")
    
    return result


@returns_value_to_javascript("object")
def get_data_preview(data_id: str, start_row: int = 0, rows: int = 100) -> dict:
    """Get paginated preview of data by ID."""
    return data_manager.get_preview(data_id, start_row, rows)


@returns_value_to_javascript("object")
def get_column_stats(data_id: str, column: str) -> dict:
    """Get detailed statistics for a column."""
    return data_manager.get_column_stats(data_id, column)


@returns_value_to_javascript("object")
def generate_chart(data_id: str, chart_type: str, x_column: str, 
                   y_column: str = None, title: str = None) -> dict:
    """Generate a chart for the dataset."""
    return data_manager.generate_chart(data_id, chart_type, x_column, y_column, title)


@returns_value_to_javascript("object")
def generate_auto_charts(data_id: str) -> dict:
    """Generate automatic visualizations based on data types."""
    return data_manager.generate_auto_charts(data_id)


@returns_value_to_javascript("object")
def unload_data(data_id: str) -> dict:
    """Unload dataset from memory."""
    success = data_manager.unload(data_id)
    return {"success": success}


# ============================================================================
# Main Application
# ============================================================================

def main():
    global pytonium
    
    pytonium = Pytonium()
    pytonium.set_frameless_window(True)
    
    # Window controls
    pytonium.bind_function_to_javascript(window_is_maximized, "isMaximized", "window")
    pytonium.bind_function_to_javascript(window_minimize, "minimize", "window")
    pytonium.bind_function_to_javascript(window_maximize, "maximize", "window")
    pytonium.bind_function_to_javascript(window_close, "close", "window")
    pytonium.bind_function_to_javascript(window_drag, "drag", "window")
    pytonium.bind_function_to_javascript(window_resize, "resize", "window")
    
    # Data API (using data handle pattern)
    pytonium.bind_function_to_javascript(load_file, "loadFile", "data")
    pytonium.bind_function_to_javascript(get_data_preview, "getDataPreview", "data")
    pytonium.bind_function_to_javascript(get_column_stats, "getColumnStats", "data")
    pytonium.bind_function_to_javascript(generate_chart, "generateChart", "data")
    pytonium.bind_function_to_javascript(generate_auto_charts, "generateAutoCharts", "data")
    pytonium.bind_function_to_javascript(unload_data, "unloadData", "data")
    
    # Initialize
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "index.html")
    
    pytonium.initialize(f"file://{html_path}", 1400, 900)
    
    print("=" * 60)
    print("Pytonium Data Studio Started!")
    print("=" * 60)
    print("Features:")
    print("  📁 Load CSV/Excel via drag & drop or file picker")
    print("  🔍 Auto-analysis with smart visualizations")
    print("  📊 Efficient data handling (large files stay in Python)")
    print("  🎨 Color-coded column types with statistics")
    print("=" * 60)
    
    while pytonium.is_running():
        time.sleep(0.01)
        pytonium.update_message_loop()


if __name__ == "__main__":
    try:
        import pandas as pd
        import numpy as np
        main()
    except ImportError as e:
        print("=" * 60)
        print("ERROR: Missing required dependencies!")
        print("=" * 60)
        print(f"{e}")
        print("\nPlease install required packages:")
        print("  pip install pandas matplotlib openpyxl numpy")
        print("=" * 60)
        input("\nPress Enter to exit...")
