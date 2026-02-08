"""
Data Manager - Efficient handling of large datasets

Uses a data handle pattern:
1. Load file → returns data_id (file stays in Python memory)
2. Use data_id to get info, stats, previews, charts
3. No need to send all data to JavaScript - just summaries and handles
"""

import io
import base64
import uuid
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional
from datetime import datetime


class DataManager:
    """Manages loaded datasets with unique IDs."""
    
    def __init__(self):
        self._datasets: Dict[str, 'DatasetHandle'] = {}
    
    def load_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load CSV or Excel file and return a data handle ID.
        The actual data stays in Python memory - only the ID goes to JavaScript.
        """
        try:
            # Generate unique ID
            data_id = str(uuid.uuid4())[:8]
            
            # Load based on file type
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                return {"error": "Unsupported file format. Use .csv or .xlsx"}
            
            # Create handle
            handle = DatasetHandle(data_id, df, file_path)
            self._datasets[data_id] = handle
            
            # Return ID and basic info (not the full data!)
            return {
                "data_id": data_id,
                "info": handle.get_info(),
                "columns": handle.get_column_info(),
                "stats": handle.get_stats(),
                "preview": handle.get_preview(rows=20),
                "auto_charts": handle.suggest_charts()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_dataset(self, data_id: str) -> Optional['DatasetHandle']:
        """Get dataset handle by ID."""
        return self._datasets.get(data_id)
    
    def get_preview(self, data_id: str, start_row: int = 0, rows: int = 100) -> Dict[str, Any]:
        """Get paginated preview of data."""
        handle = self.get_dataset(data_id)
        if not handle:
            return {"error": "Dataset not found"}
        return handle.get_preview(start_row, rows)
    
    def get_column_stats(self, data_id: str, column: str) -> Dict[str, Any]:
        """Get detailed statistics for a column."""
        handle = self.get_dataset(data_id)
        if not handle:
            return {"error": "Dataset not found"}
        return handle.get_column_stats(column)
    
    def generate_chart(self, data_id: str, chart_type: str, x_column: str, 
                       y_column: str = None, title: str = None) -> Dict[str, Any]:
        """Generate chart for a dataset."""
        handle = self.get_dataset(data_id)
        if not handle:
            return {"error": "Dataset not found"}
        return handle.generate_chart(chart_type, x_column, y_column, title)
    
    def generate_auto_charts(self, data_id: str) -> Dict[str, Any]:
        """Generate automatic visualizations based on column types."""
        handle = self.get_dataset(data_id)
        if not handle:
            return {"error": "Dataset not found"}
        return handle.generate_auto_charts()
    
    def unload(self, data_id: str) -> bool:
        """Remove dataset from memory."""
        if data_id in self._datasets:
            del self._datasets[data_id]
            return True
        return False


class DatasetHandle:
    """Handle for a loaded dataset - keeps data in Python memory."""
    
    def __init__(self, data_id: str, df: pd.DataFrame, source_path: str):
        self.data_id = data_id
        self.df = df
        self.source_path = source_path
        self.loaded_at = datetime.now()
        
        # Detect column types
        self.column_types = self._detect_column_types()
    
    def _detect_column_types(self) -> Dict[str, str]:
        """Detect and categorize column types."""
        types = {}
        for col in self.df.columns:
            dtype = self.df[col].dtype
            if pd.api.types.is_datetime64_any_dtype(dtype):
                types[col] = "datetime"
            elif pd.api.types.is_numeric_dtype(dtype):
                types[col] = "numeric"
            else:
                # Check if it might be a categorical
                if self.df[col].nunique() / len(self.df) < 0.1:  # Less than 10% unique
                    types[col] = "categorical"
                else:
                    types[col] = "string"
        return types
    
    def get_info(self) -> Dict[str, Any]:
        """Get basic dataset info."""
        return {
            "data_id": self.data_id,
            "rows": len(self.df),
            "columns": len(self.df.columns),
            "memory_mb": round(self.df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            "missing_values": int(self.df.isnull().sum().sum()),
            "duplicate_rows": int(self.df.duplicated().sum()),
            "loaded_at": self.loaded_at.isoformat()
        }
    
    def get_column_info(self) -> list:
        """Get column information with type badges."""
        columns = []
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            col_type = self.column_types.get(col, "unknown")
            
            columns.append({
                "name": col,
                "dtype": dtype,
                "type_category": col_type,
                "null_count": int(self.df[col].isnull().sum()),
                "unique_count": int(self.df[col].nunique())
            })
        return columns
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        stats = {
            "numeric_summary": {},
            "categorical_summary": {},
            "datetime_summary": {}
        }
        
        # Numeric columns
        numeric_cols = [c for c, t in self.column_types.items() if t == "numeric"]
        if numeric_cols:
            desc = self.df[numeric_cols].describe()
            for col in numeric_cols:
                stats["numeric_summary"][col] = {
                    "count": int(desc.loc['count', col]) if 'count' in desc.index else None,
                    "mean": round(desc.loc['mean', col], 2) if 'mean' in desc.index else None,
                    "std": round(desc.loc['std', col], 2) if 'std' in desc.index else None,
                    "min": round(desc.loc['min', col], 2) if 'min' in desc.index else None,
                    "25%": round(desc.loc['25%', col], 2) if '25%' in desc.index else None,
                    "50%": round(desc.loc['50%', col], 2) if '50%' in desc.index else None,
                    "75%": round(desc.loc['75%', col], 2) if '75%' in desc.index else None,
                    "max": round(desc.loc['max', col], 2) if 'max' in desc.index else None
                }
        
        # Categorical columns
        cat_cols = [c for c, t in self.column_types.items() if t in ["categorical", "string"]]
        for col in cat_cols:
            value_counts = self.df[col].value_counts().head(10)
            stats["categorical_summary"][col] = {
                "top_values": value_counts.to_dict(),
                "unique_count": int(self.df[col].nunique())
            }
        
        # Datetime columns
        dt_cols = [c for c, t in self.column_types.items() if t == "datetime"]
        for col in dt_cols:
            stats["datetime_summary"][col] = {
                "min": str(self.df[col].min()),
                "max": str(self.df[col].max()),
                "range_days": (self.df[col].max() - self.df[col].min()).days
            }
        
        return stats
    
    def get_preview(self, start_row: int = 0, rows: int = 100) -> Dict[str, Any]:
        """Get paginated data preview."""
        end_row = min(start_row + rows, len(self.df))
        slice_df = self.df.iloc[start_row:end_row]
        
        return {
            "start_row": start_row,
            "end_row": end_row,
            "total_rows": len(self.df),
            "data": slice_df.to_dict('records'),
            "has_more": end_row < len(self.df)
        }
    
    def get_column_stats(self, column: str) -> Dict[str, Any]:
        """Get detailed stats for a single column."""
        if column not in self.df.columns:
            return {"error": f"Column '{column}' not found"}
        
        col = self.df[column]
        col_type = self.column_types.get(column, "unknown")
        
        result = {
            "name": column,
            "type": col_type,
            "dtype": str(col.dtype),
            "count": int(col.count()),
            "null_count": int(col.isnull().sum()),
            "null_percent": round(col.isnull().sum() / len(col) * 100, 1),
            "unique_count": int(col.nunique())
        }
        
        if col_type == "numeric":
            result.update({
                "min": float(col.min()),
                "max": float(col.max()),
                "mean": round(float(col.mean()), 2),
                "median": round(float(col.median()), 2),
                "std": round(float(col.std()), 2),
                "sum": round(float(col.sum()), 2)
            })
        
        return result
    
    def suggest_charts(self) -> list:
        """Suggest appropriate charts based on data types."""
        suggestions = []
        
        numeric_cols = [c for c, t in self.column_types.items() if t == "numeric"]
        cat_cols = [c for c, t in self.column_types.items() if t in ["categorical", "string"]]
        dt_cols = [c for c, t in self.column_types.items() if t == "datetime"]
        
        # Time series (datetime + numeric)
        if dt_cols and numeric_cols:
            suggestions.append({
                "type": "line",
                "title": f"Time Series: {numeric_cols[0]} over {dt_cols[0]}",
                "x": dt_cols[0],
                "y": numeric_cols[0],
                "reason": "Datetime + Numeric = Time series line chart"
            })
        
        # Scatter plot (two numerics)
        if len(numeric_cols) >= 2:
            suggestions.append({
                "type": "scatter",
                "title": f"Correlation: {numeric_cols[0]} vs {numeric_cols[1]}",
                "x": numeric_cols[0],
                "y": numeric_cols[1],
                "reason": "Two numeric columns = Scatter plot"
            })
        
        # Bar chart (categorical + numeric)
        if cat_cols and numeric_cols:
            suggestions.append({
                "type": "bar",
                "title": f"{numeric_cols[0]} by {cat_cols[0]}",
                "x": cat_cols[0],
                "y": numeric_cols[0],
                "reason": "Categorical + Numeric = Bar chart"
            })
        
        # Distribution (single numeric)
        if numeric_cols:
            suggestions.append({
                "type": "histogram",
                "title": f"Distribution of {numeric_cols[0]}",
                "x": numeric_cols[0],
                "y": None,
                "reason": "Single numeric = Histogram"
            })
        
        # Pie chart (categorical with few unique values)
        for col in cat_cols:
            if self.df[col].nunique() <= 10:
                suggestions.append({
                    "type": "pie",
                    "title": f"Distribution of {col}",
                    "x": col,
                    "y": None,
                    "reason": f"Categorical with {self.df[col].nunique()} categories = Pie chart"
                })
                break
        
        return suggestions
    
    def generate_chart(self, chart_type: str, x_column: str, 
                       y_column: str = None, title: str = None) -> Dict[str, Any]:
        """Generate matplotlib chart."""
        try:
            fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
            fig.patch.set_facecolor('#1e293b')
            ax.set_facecolor('#0f172a')
            
            colors = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#ec4899']
            
            df_plot = self.df.dropna(subset=[x_column])
            if y_column:
                df_plot = df_plot.dropna(subset=[y_column])
            
            if chart_type == 'line':
                if y_column:
                    ax.plot(df_plot[x_column], df_plot[y_column], 
                           color=colors[0], linewidth=2, marker='o', markersize=4)
                    ax.set_ylabel(y_column, color='white')
                else:
                    ax.plot(df_plot[x_column], color=colors[0], linewidth=2)
                ax.set_xlabel(x_column, color='white')
                
            elif chart_type == 'bar':
                if y_column:
                    grouped = df_plot.groupby(x_column)[y_column].sum().sort_values(ascending=False).head(20)
                else:
                    grouped = df_plot[x_column].value_counts().head(20)
                grouped.plot(kind='bar', ax=ax, color=colors[0])
                ax.set_xlabel(x_column, color='white')
                plt.xticks(rotation=45, ha='right')
                
            elif chart_type == 'scatter':
                if not y_column:
                    return {"error": "Scatter plot requires Y column"}
                ax.scatter(df_plot[x_column], df_plot[y_column], 
                          color=colors[0], alpha=0.6, s=50)
                ax.set_xlabel(x_column, color='white')
                ax.set_ylabel(y_column, color='white')
                
            elif chart_type == 'histogram':
                ax.hist(df_plot[x_column].dropna(), bins=30, 
                       color=colors[0], alpha=0.7, edgecolor='white')
                ax.set_xlabel(x_column, color='white')
                ax.set_ylabel('Frequency', color='white')
                
            elif chart_type == 'pie':
                counts = df_plot[x_column].value_counts().head(10)
                wedges, texts, autotexts = ax.pie(counts, labels=counts.index, 
                                                   autopct='%1.1f%%', colors=colors,
                                                   startangle=90)
                for text in texts:
                    text.set_color('white')
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(9)
                    
            elif chart_type == 'heatmap':
                numeric_df = self.df.select_dtypes(include=[np.number])
                if len(numeric_df.columns) < 2:
                    return {"error": "Need at least 2 numeric columns"}
                corr = numeric_df.corr()
                im = ax.imshow(corr, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
                ax.set_xticks(range(len(corr.columns)))
                ax.set_yticks(range(len(corr.columns)))
                ax.set_xticklabels(corr.columns, rotation=45, ha='right', color='white')
                ax.set_yticklabels(corr.columns, color='white')
                plt.colorbar(im, ax=ax, label='Correlation')
                for i in range(len(corr.columns)):
                    for j in range(len(corr.columns)):
                        ax.text(j, i, f'{corr.iloc[i, j]:.2f}',
                               ha="center", va="center", color="white", fontsize=8)
            
            # Styling
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('white')
            
            chart_title = title or f'{chart_type.title()}: {x_column}'
            ax.set_title(chart_title, color='white', fontsize=14, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3, color='white')
            
            # Save to base64
            buf = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', facecolor=fig.get_facecolor())
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            
            return {
                "image": f"data:image/png;base64,{img_base64}",
                "type": chart_type,
                "rows_used": len(df_plot)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def generate_auto_charts(self) -> Dict[str, list]:
        """Generate all suggested auto-charts."""
        suggestions = self.suggest_charts()
        charts = []
        
        for suggestion in suggestions[:3]:  # Generate top 3
            result = self.generate_chart(
                suggestion['type'],
                suggestion['x'],
                suggestion.get('y'),
                suggestion['title']
            )
            if 'error' not in result:
                result['suggestion'] = suggestion
                charts.append(result)
        
        return {"charts": charts}


# Global instance
data_manager = DataManager()
