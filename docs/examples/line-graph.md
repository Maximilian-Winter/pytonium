---
title: Real-Time Line Graph
---

# Real-Time Line Graph

This example demonstrates real-time data visualization by pushing data points from Python via state management and rendering a live-updating line chart in JavaScript using the HTML Canvas API.

!!! tip "Full Source"
    The complete source code is available in the main repository at [`pytonium_examples/pytonium_example_line_graph`](https://github.com/Maximilian-Winter/pytonium/tree/master/pytonium_examples/pytonium_example_line_graph).

---

## Python Entry Point

```python title="main.py"
import os
import time
import math
import json
import random
from Pytonium import Pytonium

pytonium = Pytonium()
pytonium.add_custom_scheme("app", os.path.dirname(os.path.abspath(__file__)) + "/")
pytonium.initialize("app://index.html", 900, 500)

t = 0.0
while pytonium.is_running():
    time.sleep(0.05)  # 20 updates per second
    pytonium.update_message_loop()

    # Generate data: a sine wave with noise
    value = math.sin(t) * 50 + random.gauss(0, 5)
    t += 0.1

    # Push the new data point as a JSON object
    pytonium.set_state("graph", "point", json.dumps({
        "time": round(t, 2),
        "value": round(value, 2)
    }))
```

---

## HTML Page

```html title="index.html"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Real-Time Line Graph</title>
    <style>
        body {
            margin: 0;
            background: #0f0f23;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            font-family: system-ui, -apple-system, sans-serif;
            color: #e0e0e0;
        }
        h2 { color: #bb86fc; margin-bottom: 12px; }
        canvas {
            background: #1a1a2e;
            border-radius: 8px;
            border: 1px solid #333;
        }
        #stats {
            margin-top: 12px;
            font-size: 14px;
            color: #888;
        }
    </style>
</head>
<body>
    <h2>Live Data from Python</h2>
    <canvas id="chart" width="800" height="350"></canvas>
    <div id="stats">Waiting for data...</div>

    <script>
        const canvas = document.getElementById("chart");
        const ctx = canvas.getContext("2d");
        const statsEl = document.getElementById("stats");
        const maxPoints = 200;
        const dataPoints = [];

        function drawChart() {
            const w = canvas.width;
            const h = canvas.height;
            ctx.clearRect(0, 0, w, h);

            if (dataPoints.length < 2) return;

            // Determine Y range
            const values = dataPoints.map(p => p.value);
            const minVal = Math.min(...values) - 10;
            const maxVal = Math.max(...values) + 10;
            const range = maxVal - minVal || 1;

            // Draw grid lines
            ctx.strokeStyle = "#333";
            ctx.lineWidth = 0.5;
            for (let i = 0; i <= 4; i++) {
                const y = (i / 4) * h;
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(w, y);
                ctx.stroke();
            }

            // Draw zero line
            const zeroY = h - ((0 - minVal) / range) * h;
            ctx.strokeStyle = "#555";
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 4]);
            ctx.beginPath();
            ctx.moveTo(0, zeroY);
            ctx.lineTo(w, zeroY);
            ctx.stroke();
            ctx.setLineDash([]);

            // Draw the data line
            ctx.strokeStyle = "#03dac6";
            ctx.lineWidth = 2;
            ctx.beginPath();
            for (let i = 0; i < dataPoints.length; i++) {
                const x = (i / (maxPoints - 1)) * w;
                const y = h - ((dataPoints[i].value - minVal) / range) * h;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();

            // Draw the latest point
            const lastX = ((dataPoints.length - 1) / (maxPoints - 1)) * w;
            const lastY = h - ((dataPoints[dataPoints.length - 1].value - minVal) / range) * h;
            ctx.fillStyle = "#bb86fc";
            ctx.beginPath();
            ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
            ctx.fill();
        }

        document.addEventListener("PytoniumReady", function () {
            Pytonium.registerForStateUpdates("graph", "point", function (raw) {
                const point = JSON.parse(raw);
                dataPoints.push(point);

                // Keep only the last N points
                if (dataPoints.length > maxPoints) {
                    dataPoints.shift();
                }

                drawChart();

                // Update stats display
                statsEl.textContent =
                    "Points: " + dataPoints.length +
                    " | Latest: " + point.value +
                    " | Time: " + point.time;
            });
        });
    </script>
</body>
</html>
```

---

## How It Works

### Python Data Push Pattern

The core pattern is straightforward: in the main message loop, Python generates data and pushes it to JavaScript via `set_state()`:

```python
while pytonium.is_running():
    time.sleep(0.05)
    pytonium.update_message_loop()

    value = math.sin(t) * 50 + random.gauss(0, 5)
    pytonium.set_state("graph", "point", json.dumps({
        "time": round(t, 2),
        "value": round(value, 2)
    }))
```

Key points:

- **Update frequency**: `time.sleep(0.05)` gives approximately 20 updates per second, which is smooth for a line chart without excessive CPU usage.
- **JSON encoding**: State values are strings. For structured data, use `json.dumps()` on the Python side and `JSON.parse()` on the JavaScript side.
- **Namespace separation**: The `"graph"` namespace keeps this state separate from any other state your application might use.

### JavaScript State Subscription

```javascript
Pytonium.registerForStateUpdates("graph", "point", function (raw) {
    const point = JSON.parse(raw);
    dataPoints.push(point);
    if (dataPoints.length > maxPoints) {
        dataPoints.shift();
    }
    drawChart();
});
```

The callback fires each time Python calls `set_state("graph", "point", ...)`. The JavaScript side maintains a sliding window of the most recent 200 data points and redraws the canvas on every update.

### Canvas Rendering

This example uses the raw Canvas 2D API for rendering. This approach has zero dependencies and performs well for moderate data rates. The chart draws:

1. **Grid lines** for visual reference
2. **A dashed zero line** to show the baseline
3. **The data line** connecting all points
4. **A dot** on the latest point

!!! info "Alternative: Chart Libraries"
    For production applications, you can use a charting library such as [Chart.js](https://www.chartjs.org/), [ECharts](https://echarts.apache.org/), or [Plotly.js](https://plotly.com/javascript/). Load them via a custom scheme just like the Babylon.js example. The state management pattern remains the same -- only the rendering code changes.

---

## Performance Considerations

| Factor | Recommendation |
|---|---|
| Update rate | 10-60 Hz is typical. Above 60 Hz provides no visual benefit. |
| Data window | Keep 100-500 points. Larger windows cost more to render. |
| JSON size | Keep payloads small. For bulk data, batch multiple points per update. |
| Canvas vs DOM | Canvas is faster for frequent redraws. DOM updates are fine at lower rates. |

### Batching Multiple Points

If your data source produces faster than your desired render rate, batch points:

```python
batch = []
for _ in range(10):
    batch.append({"time": round(t, 2), "value": round(generate_value(), 2)})
    t += 0.01

pytonium.set_state("graph", "batch", json.dumps(batch))
```

```javascript
Pytonium.registerForStateUpdates("graph", "batch", function (raw) {
    const points = JSON.parse(raw);
    points.forEach(p => dataPoints.push(p));
    while (dataPoints.length > maxPoints) dataPoints.shift();
    drawChart();
});
```

---

## Use Cases

This pattern applies to any scenario where Python produces data that needs live visualization:

- **System monitoring** -- CPU, memory, network throughput
- **Sensor data** -- Temperature, pressure, accelerometer readings
- **Financial data** -- Stock prices, trading volume
- **Scientific instruments** -- Oscilloscope traces, spectrum analyzers
- **Machine learning** -- Training loss curves, metric dashboards

---

## Next Steps

- **[State Management Guide](../guides/state-management.md)** -- Full reference for state namespaces, subscriptions, and patterns.
- **[Control Center](control-center.md)** -- A multi-panel dashboard example.
- **[Simple App](simple-app.md)** -- Start with the basics if you have not already.
