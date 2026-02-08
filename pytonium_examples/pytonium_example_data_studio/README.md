# Pytonium Data Studio

A clean, focused example demonstrating Pytonium's data analysis capabilities using **pandas** and **matplotlib**.

## What This Example Shows

This example showcases Pytonium's superpower: **access to Python's entire data science ecosystem** without the hassle of native modules.

### The Pytonium Advantage

| Task | Electron | Pytonium |
|------|----------|----------|
| Read CSV/Excel | Native Node modules, compilation | `pandas.read_csv()` - just works |
| Generate charts | Chart.js or native canvas | `matplotlib` - professional output |
| Data manipulation | Limited JavaScript libraries | Full pandas DataFrame API |
| Excel support | Additional native dependencies | `openpyxl` - pure Python |

## Features

- 📊 **Load sample datasets** (Sales, Stock Prices, Employee Survey)
- 📁 **Load your own CSV/Excel files**
- 🔍 **Interactive data table** with column type indicators
- 📈 **6 chart types**: Line, Bar, Scatter, Histogram, Pie, Heatmap
- 🎨 **Beautiful dark-themed matplotlib output**
- ⚡ **Server-side rendering**, displayed in the UI

## Installation

```bash
pip install pandas matplotlib openpyxl
```

That's it! No compilation, no platform-specific binaries, no headaches.

## Running

```bash
python main.py
```

## How It Works

1. **Python side** (`data_analyzer.py`):
   - `pandas` loads data from CSV/Excel
   - `matplotlib` renders charts with a custom dark theme
   - Charts are saved to a memory buffer and encoded as Base64
   - Returned to JavaScript as data URIs

2. **JavaScript side**:
   - Calls Python functions via `Pytonium.data.*`
   - Displays data in an interactive HTML table
   - Shows charts as `<img src="data:image/png;base64,...">`

## Code Example

```python
# In Electron, this would require native modules and compilation
# In Pytonium, it's just Python!

import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('data.csv')

# Create chart
plt.figure(figsize=(10, 6))
df.plot(kind='bar')

# Save to memory buffer
buf = io.BytesIO()
plt.savefig(buf, format='png')
img_base64 = base64.b64encode(buf.getvalue()).decode()

# Return to JavaScript
return {"image": f"data:image/png;base64,{img_base64}"}
```

## File Structure

```
pytonium_example_data_studio/
├── main.py          # Application entry point
├── index.html       # UI (clean, focused interface)
├── data_analyzer.py # pandas + matplotlib logic (shared with Control Center)
└── README.md        # This file
```

## Key Takeaway

Building a data analysis app in Electron requires:
- Installing native Node modules
- Dealing with compilation issues
- Platform-specific builds
- Limited library selection

In Pytonium:
- `pip install pandas matplotlib`
- Write Python code
- Done! 🎉

This is why Pytonium exists - to bring Python's unmatched ecosystem to desktop apps effortlessly.
