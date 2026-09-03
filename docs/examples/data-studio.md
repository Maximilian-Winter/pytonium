---
title: Data Studio
---

# Data Studio

This example demonstrates a data analysis tool where Python handles data loading and processing while JavaScript provides an interactive UI for exploring results. It showcases the use of `@returns_value_to_javascript` for query-style interactions and state management for progress reporting.

!!! tip "Full Source"
    This page provides a conceptual walkthrough with key code snippets. The complete source code is available in the main repository at [`pytonium_examples/pytonium_example_data_studio`](https://github.com/Maximilian-Winter/pytonium/tree/master/pytonium_examples/pytonium_example_data_studio).

---

## Architecture

```
User interacts with UI (JavaScript)
    |
    v
JavaScript calls Python bindings (Promises)
    |-- data_api.load_csv(path)      --> Loads file, returns summary
    |-- data_api.query(column, op)   --> Filters/aggregates data, returns results
    |-- data_api.get_columns()       --> Returns column names and types
    |-- data_api.get_rows(start, n)  --> Returns paginated rows
    |
Python processes data (csv, json, or any library)
    |
    v
Results returned to JavaScript as JSON --> Rendered in tables/charts
```

---

## Python: Data Backend

```python title="main.py (key sections)"
import os
import csv
import json
import time
from Pytonium import Pytonium, returns_value_to_javascript

pytonium = Pytonium()

# In-memory data store
loaded_data = {"columns": [], "rows": [], "filename": ""}


@returns_value_to_javascript("any")
def load_csv(file_path):
    """Load a CSV file and return a summary."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            loaded_data["columns"] = reader.fieldnames or []
            loaded_data["rows"] = list(reader)
            loaded_data["filename"] = os.path.basename(file_path)

        return {
            "success": True,
            "filename": loaded_data["filename"],
            "columns": loaded_data["columns"],
            "row_count": len(loaded_data["rows"])
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@returns_value_to_javascript("any")
def get_columns():
    """Return column names and inferred types."""
    if not loaded_data["columns"]:
        return []

    result = []
    for col in loaded_data["columns"]:
        # Simple type inference from first non-empty value
        col_type = "string"
        for row in loaded_data["rows"]:
            val = row.get(col, "")
            if val:
                try:
                    float(val)
                    col_type = "number"
                except ValueError:
                    col_type = "string"
                break
        result.append({"name": col, "type": col_type})
    return result


@returns_value_to_javascript("any")
def get_rows(start, count):
    """Return a page of rows."""
    start = int(start)
    count = int(count)
    rows = loaded_data["rows"][start:start + count]
    return {
        "rows": rows,
        "total": len(loaded_data["rows"]),
        "start": start,
        "count": len(rows)
    }


@returns_value_to_javascript("any")
def query(column, operation):
    """Run a simple aggregation on a column."""
    values = []
    for row in loaded_data["rows"]:
        val = row.get(column, "")
        try:
            values.append(float(val))
        except ValueError:
            continue

    if not values:
        return {"error": f"No numeric values in column '{column}'"}

    results = {
        "column": column,
        "operation": operation,
        "count": len(values)
    }

    if operation == "sum":
        results["result"] = sum(values)
    elif operation == "mean":
        results["result"] = sum(values) / len(values)
    elif operation == "min":
        results["result"] = min(values)
    elif operation == "max":
        results["result"] = max(values)
    elif operation == "range":
        results["result"] = max(values) - min(values)
    else:
        results["error"] = f"Unknown operation: {operation}"

    return results


# Bind all functions under the data_api namespace
pytonium.bind_function_to_javascript(load_csv, javascript_object="data_api")
pytonium.bind_function_to_javascript(get_columns, javascript_object="data_api")
pytonium.bind_function_to_javascript(get_rows, javascript_object="data_api")
pytonium.bind_function_to_javascript(query, javascript_object="data_api")

pytonium.add_custom_scheme("app", os.path.dirname(os.path.abspath(__file__)) + "/")
pytonium.initialize("app://index.html", 1100, 700)

while pytonium.is_running():
    time.sleep(0.01)
    pytonium.update_message_loop()
```

---

## JavaScript: Interactive Data Explorer

```javascript title="app.js (key sections)"
document.addEventListener("PytoniumReady", function () {

    let currentPage = 0;
    const pageSize = 50;

    // -- File Loading --
    document.getElementById("btn-load").addEventListener("click", async function () {
        const path = document.getElementById("file-path").value;
        if (!path) return;

        document.getElementById("status").textContent = "Loading...";
        const result = await data_api.load_csv(path);

        if (result.success) {
            document.getElementById("status").textContent =
                "Loaded " + result.filename +
                " (" + result.row_count + " rows, " +
                result.columns.length + " columns)";
            currentPage = 0;
            await renderColumns();
            await renderPage();
        } else {
            document.getElementById("status").textContent = "Error: " + result.error;
        }
    });

    // -- Column Info --
    async function renderColumns() {
        const columns = await data_api.get_columns();
        const container = document.getElementById("columns");
        container.innerHTML = "";

        columns.forEach(function (col) {
            const tag = document.createElement("span");
            tag.className = "column-tag column-" + col.type;
            tag.textContent = col.name + " (" + col.type + ")";
            container.appendChild(tag);
        });

        // Populate the query column dropdown
        const select = document.getElementById("query-column");
        select.innerHTML = "";
        columns.filter(c => c.type === "number").forEach(function (col) {
            const opt = document.createElement("option");
            opt.value = col.name;
            opt.textContent = col.name;
            select.appendChild(opt);
        });
    }

    // -- Data Table with Pagination --
    async function renderPage() {
        const result = await data_api.get_rows(currentPage * pageSize, pageSize);
        const table = document.getElementById("data-table");

        if (result.rows.length === 0) {
            table.innerHTML = "<p>No data</p>";
            return;
        }

        const keys = Object.keys(result.rows[0]);
        let html = "<table><thead><tr>";
        keys.forEach(k => html += "<th>" + k + "</th>");
        html += "</tr></thead><tbody>";

        result.rows.forEach(function (row) {
            html += "<tr>";
            keys.forEach(k => html += "<td>" + (row[k] || "") + "</td>");
            html += "</tr>";
        });
        html += "</tbody></table>";

        html += "<div class='pagination'>" +
            "Showing " + (result.start + 1) + "-" +
            (result.start + result.count) + " of " + result.total +
            "</div>";

        table.innerHTML = html;
    }

    // -- Pagination Controls --
    document.getElementById("btn-prev").addEventListener("click", function () {
        if (currentPage > 0) { currentPage--; renderPage(); }
    });
    document.getElementById("btn-next").addEventListener("click", function () {
        currentPage++;
        renderPage();
    });

    // -- Query Execution --
    document.getElementById("btn-query").addEventListener("click", async function () {
        const column = document.getElementById("query-column").value;
        const operation = document.getElementById("query-op").value;

        if (!column) return;

        const result = await data_api.query(column, operation);
        const output = document.getElementById("query-result");

        if (result.error) {
            output.textContent = "Error: " + result.error;
        } else {
            output.textContent =
                operation.toUpperCase() + "(" + column + ") = " +
                result.result.toFixed(4) +
                " (over " + result.count + " values)";
        }
    });
});
```

---

## Key Patterns

### Promise-Based Data Queries

Every `@returns_value_to_javascript` function returns a JavaScript `Promise`. This makes the code naturally asynchronous:

```javascript
const result = await data_api.load_csv(path);
if (result.success) {
    // proceed with data
}
```

The JavaScript UI remains responsive while Python processes the request. For large files, you can combine this with state-based progress reporting (see below).

### Paginated Data Access

Rather than sending the entire dataset to JavaScript at once, the `get_rows` function supports pagination:

```python
@returns_value_to_javascript("any")
def get_rows(start, count):
    rows = loaded_data["rows"][start:start + count]
    return {"rows": rows, "total": len(loaded_data["rows"]), ...}
```

This keeps memory usage low on the JavaScript side and avoids serializing thousands of rows at once.

### Structured Return Values

All binding functions return dictionaries that are automatically converted to JavaScript objects:

```python
return {
    "success": True,
    "filename": loaded_data["filename"],
    "columns": loaded_data["columns"],
    "row_count": len(loaded_data["rows"])
}
```

!!! info "Supported Return Types"
    Pytonium automatically serializes Python `dict`, `list`, `str`, `int`, `float`, and `bool` values to their JavaScript equivalents. Nested structures work as well -- a list of dicts becomes an array of objects.

### Error Handling Pattern

Each function returns a structured result that includes error information when something goes wrong:

```python
try:
    # ... process data ...
    return {"success": True, "data": result}
except Exception as e:
    return {"success": False, "error": str(e)}
```

This allows JavaScript to handle errors gracefully without relying on exception propagation across the Python-JavaScript boundary.

---

## Extending This Example

### Adding Progress Reporting

For long-running operations, use state management to report progress while the binding function executes:

```python
@returns_value_to_javascript("any")
def process_large_file(file_path):
    total_lines = count_lines(file_path)
    processed = 0

    with open(file_path) as f:
        for line in f:
            process_line(line)
            processed += 1
            if processed % 1000 == 0:
                progress = int((processed / total_lines) * 100)
                pytonium.set_state("progress", "percent", str(progress))

    return {"success": True, "processed": processed}
```

### Using pandas or Other Libraries

The Python backend can use any library available in the environment. For example, with pandas:

```python
import pandas as pd

@returns_value_to_javascript("any")
def load_and_describe(file_path):
    df = pd.read_csv(file_path)
    return {
        "shape": list(df.shape),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "describe": df.describe().to_dict()
    }
```

### File Dialog Integration

While Pytonium does not currently include a native file dialog API, you can use an HTML `<input type="file">` element or pass file paths via a text input as shown in this example.

---

## Next Steps

- **[JavaScript Bindings Guide](../guides/javascript-bindings.md)** -- Full reference for `@returns_value_to_javascript` and binding options.
- **[Control Center](control-center.md)** -- A dashboard example with continuous state updates.
- **[Simple App](simple-app.md)** -- Start with the basics if you have not already.
