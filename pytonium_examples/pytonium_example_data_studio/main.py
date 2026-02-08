"""
Pytonium Data Studio - Data Analysis & Visualization Demo

This example showcases Pytonium's data analysis capabilities using:
- pandas: Data manipulation and analysis
- matplotlib: Professional chart generation
- openpyxl: Excel file support

In Electron: Native module compilation nightmare
In Pytonium: pip install pandas matplotlib - done!

Install dependencies:
    pip install pandas matplotlib openpyxl
"""

import os
import sys
import time
from threading import Thread
from pathlib import Path

# Add parent directory to path to import data_analyzer
sys.path.insert(0, str(Path(__file__).parent.parent / 'pytonium_example_control_center'))
from data_analyzer import DataAnalyzer

from Pytonium import Pytonium, returns_value_to_javascript


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
# Data Analysis API
# ============================================================================

data_analyzer = DataAnalyzer()

@returns_value_to_javascript("object")
def get_sample_datasets():
    """Get available sample datasets."""
    return data_analyzer.get_sample_datasets()


@returns_value_to_javascript("object")
def load_sample_dataset(dataset_name: str):
    """Load a sample dataset."""
    return data_analyzer.load_sample_dataset(dataset_name)


@returns_value_to_javascript("object")
def load_data_file(file_path: str):
    """Load CSV or Excel file."""
    # Handle relative paths
    if not os.path.isabs(file_path):
        file_path = os.path.join(os.path.dirname(__file__), file_path)
    return data_analyzer.load_file(file_path)


@returns_value_to_javascript("object")
def generate_chart(chart_type: str, x_column: str, y_column: str = None, title: str = None):
    """Generate matplotlib chart."""
    return data_analyzer.generate_chart(chart_type, x_column, y_column or None, None, title)


@returns_value_to_javascript("object")
def get_column_stats(column: str):
    """Get statistics for a specific column."""
    if data_analyzer.current_df is None:
        return {"error": "No data loaded"}
    
    df = data_analyzer.current_df
    if column not in df.columns:
        return {"error": f"Column {column} not found"}
    
    col_data = df[column]
    result = {
        "name": column,
        "type": str(col_data.dtype),
        "count": int(col_data.count()),
        "null_count": int(col_data.isnull().sum()),
        "unique_count": int(col_data.nunique())
    }
    
    # Add numeric stats if applicable
    if pd.api.types.is_numeric_dtype(col_data):
        result.update({
            "min": float(col_data.min()) if not col_data.isna().all() else None,
            "max": float(col_data.max()) if not col_data.isna().all() else None,
            "mean": float(col_data.mean()) if not col_data.isna().all() else None,
            "median": float(col_data.median()) if not col_data.isna().all() else None,
            "std": float(col_data.std()) if not col_data.isna().all() else None
        })
    
    return result


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
    
    # Data API
    pytonium.bind_function_to_javascript(get_sample_datasets, "getSampleDatasets", "data")
    pytonium.bind_function_to_javascript(load_sample_dataset, "loadSampleDataset", "data")
    pytonium.bind_function_to_javascript(load_data_file, "loadDataFile", "data")
    pytonium.bind_function_to_javascript(generate_chart, "generateChart", "data")
    pytonium.bind_function_to_javascript(get_column_stats, "getColumnStats", "data")
    
    # Initialize
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "index.html")
    
    pytonium.initialize(f"file://{html_path}", 1400, 900)
    
    print("=" * 60)
    print("Pytonium Data Studio Started!")
    print("=" * 60)
    print("Features:")
    print("  - Load CSV/Excel files with pandas")
    print("  - Interactive data table with statistics")
    print("  - Generate charts with matplotlib")
    print("  - All rendered server-side, displayed in UI")
    print("=" * 60)
    
    while pytonium.is_running():
        time.sleep(0.01)
        pytonium.update_message_loop()


if __name__ == "__main__":
    # Import pandas here to ensure it's available
    try:
        import pandas as pd
        main()
    except ImportError as e:
        print("=" * 60)
        print("ERROR: Missing required dependencies!")
        print("=" * 60)
        print(f"{e}")
        print("\nPlease install required packages:")
        print("  pip install pandas matplotlib openpyxl")
        print("=" * 60)
        input("\nPress Enter to exit...")
