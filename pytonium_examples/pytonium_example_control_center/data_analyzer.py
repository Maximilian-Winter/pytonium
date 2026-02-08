"""
Data Analysis & Visualization Module

Showcases Pytonium's power by combining:
- pandas: Data manipulation and analysis
- matplotlib: Professional chart generation
- openpyxl: Excel file support

In Electron: Native modules, compilation hell, platform issues
In Pytonium: pip install pandas matplotlib openpyxl - done!
"""

import io
import base64
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server-side rendering
import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, List, Dict, Any

# Configure matplotlib style
plt.style.use('dark_background')


class DataAnalyzer:
    """Handles data loading, analysis, and visualization."""
    
    def __init__(self):
        self.current_df: Optional[pd.DataFrame] = None
        self.current_file: str = ""
        
    def load_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load CSV or Excel file into pandas DataFrame.
        
        Args:
            file_path: Path to .csv or .xlsx file
            
        Returns:
            Dictionary with columns, preview data, and statistics
        """
        try:
            if file_path.endswith('.csv'):
                self.current_df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                self.current_df = pd.read_excel(file_path)
            else:
                return {"error": "Unsupported file format. Use .csv or .xlsx"}
            
            self.current_file = file_path
            return self._get_data_summary()
            
        except Exception as e:
            return {"error": str(e)}
    
    def _get_data_summary(self) -> Dict[str, Any]:
        """Generate summary of current dataframe."""
        if self.current_df is None:
            return {"error": "No data loaded"}
        
        df = self.current_df
        
        # Column info with types
        columns = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            columns.append({
                "name": col,
                "type": dtype,
                "is_numeric": pd.api.types.is_numeric_dtype(df[col])
            })
        
        # Preview data (first 100 rows)
        preview = df.head(100).to_dict('records')
        
        # Statistics
        stats = {
            "rows": len(df),
            "columns": len(df.columns),
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            "numeric_columns": len(df.select_dtypes(include=[np.number]).columns),
            "missing_values": int(df.isnull().sum().sum())
        }
        
        # Column statistics for numeric columns
        column_stats = {}
        for col in df.select_dtypes(include=[np.number]).columns:
            column_stats[col] = {
                "min": round(df[col].min(), 2) if not df[col].isna().all() else None,
                "max": round(df[col].max(), 2) if not df[col].isna().all() else None,
                "mean": round(df[col].mean(), 2) if not df[col].isna().all() else None,
                "std": round(df[col].std(), 2) if not df[col].isna().all() else None
            }
        
        return {
            "columns": columns,
            "preview": preview,
            "stats": stats,
            "column_stats": column_stats
        }
    
    def filter_data(self, column: str, operator: str, value: str) -> Dict[str, Any]:
        """
        Filter dataframe based on condition.
        
        Args:
            column: Column name to filter on
            operator: 'eq', 'gt', 'lt', 'contains'
            value: Value to compare
        """
        if self.current_df is None:
            return {"error": "No data loaded"}
        
        try:
            df = self.current_df
            
            if operator == 'eq':
                filtered = df[df[column] == value]
            elif operator == 'gt':
                filtered = df[df[column] > float(value)]
            elif operator == 'lt':
                filtered = df[df[column] < float(value)]
            elif operator == 'contains':
                filtered = df[df[column].astype(str).str.contains(value, case=False, na=False)]
            else:
                return {"error": f"Unknown operator: {operator}"}
            
            return {
                "rows": len(filtered),
                "preview": filtered.head(100).to_dict('records')
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def generate_chart(self, chart_type: str, x_column: str, y_column: str = None,
                      color_column: str = None, title: str = None) -> Dict[str, Any]:
        """
        Generate matplotlib chart and return as base64 image.
        
        Args:
            chart_type: 'line', 'bar', 'scatter', 'histogram', 'pie', 'heatmap'
            x_column: Column for x-axis (or categories)
            y_column: Column for y-axis (optional for some chart types)
            color_column: Column for color coding (optional)
            title: Chart title
            
        Returns:
            Base64 encoded PNG image
        """
        if self.current_df is None:
            return {"error": "No data loaded"}
        
        try:
            df = self.current_df
            
            # Create figure with dark theme
            fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
            fig.patch.set_facecolor('#1a1a2e')
            ax.set_facecolor('#16213e')
            
            # Set color scheme
            colors = ['#6366f1', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b', '#3b82f6']
            
            if chart_type == 'line':
                if y_column:
                    ax.plot(df[x_column], df[y_column], color=colors[0], linewidth=2, marker='o', markersize=4)
                    ax.set_ylabel(y_column, color='white')
                else:
                    ax.plot(df[x_column], color=colors[0], linewidth=2)
                ax.set_xlabel(x_column, color='white')
                
            elif chart_type == 'bar':
                if y_column:
                    df_plot = df.groupby(x_column)[y_column].sum().sort_values(ascending=False).head(20)
                else:
                    df_plot = df[x_column].value_counts().head(20)
                df_plot.plot(kind='bar', ax=ax, color=colors[0])
                ax.set_xlabel(x_column, color='white')
                if y_column:
                    ax.set_ylabel(y_column, color='white')
                plt.xticks(rotation=45, ha='right')
                
            elif chart_type == 'scatter':
                if not y_column:
                    return {"error": "Scatter plot requires Y column"}
                if color_column and color_column in df.columns:
                    scatter = ax.scatter(df[x_column], df[y_column], 
                                       c=pd.Categorical(df[color_column]).codes, 
                                       cmap='viridis', alpha=0.6, s=50)
                    plt.colorbar(scatter, ax=ax, label=color_column)
                else:
                    ax.scatter(df[x_column], df[y_column], color=colors[0], alpha=0.6, s=50)
                ax.set_xlabel(x_column, color='white')
                ax.set_ylabel(y_column, color='white')
                
            elif chart_type == 'histogram':
                ax.hist(df[x_column].dropna(), bins=30, color=colors[0], alpha=0.7, edgecolor='white')
                ax.set_xlabel(x_column, color='white')
                ax.set_ylabel('Frequency', color='white')
                
            elif chart_type == 'pie':
                counts = df[x_column].value_counts().head(10)
                wedges, texts, autotexts = ax.pie(counts, labels=counts.index, autopct='%1.1f%%',
                                                   colors=colors, startangle=90)
                for text in texts:
                    text.set_color('white')
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(9)
                    
            elif chart_type == 'heatmap':
                # Correlation heatmap for numeric columns
                numeric_df = df.select_dtypes(include=[np.number])
                if len(numeric_df.columns) < 2:
                    return {"error": "Need at least 2 numeric columns for heatmap"}
                corr = numeric_df.corr()
                im = ax.imshow(corr, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
                ax.set_xticks(range(len(corr.columns)))
                ax.set_yticks(range(len(corr.columns)))
                ax.set_xticklabels(corr.columns, rotation=45, ha='right', color='white')
                ax.set_yticklabels(corr.columns, color='white')
                plt.colorbar(im, ax=ax, label='Correlation')
                
                # Add correlation values as text
                for i in range(len(corr.columns)):
                    for j in range(len(corr.columns)):
                        text = ax.text(j, i, f'{corr.iloc[i, j]:.2f}',
                                     ha="center", va="center", color="white", fontsize=8)
            
            # Styling
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
            
            if title:
                ax.set_title(title, color='white', fontsize=14, fontweight='bold', pad=20)
            else:
                ax.set_title(f'{chart_type.title()} Chart: {x_column}' + (f' vs {y_column}' if y_column else ''), 
                           color='white', fontsize=14, fontweight='bold', pad=20)
            
            ax.grid(True, alpha=0.3, color='white')
            
            # Save to base64
            buf = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            
            return {
                "image": f"data:image/png;base64,{img_base64}",
                "rows_used": len(df)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_sample_datasets(self) -> Dict[str, List[Dict]]:
        """Generate sample datasets for demonstration."""
        datasets = []
        
        # Sales data sample
        np.random.seed(42)
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        sales_data = pd.DataFrame({
            'Month': months,
            'Revenue': np.random.randint(50000, 150000, 12),
            'Expenses': np.random.randint(30000, 80000, 12),
            'Customers': np.random.randint(1000, 5000, 12),
            'Region': np.random.choice(['North', 'South', 'East', 'West'], 12)
        })
        datasets.append({
            "name": "Sales Performance 2024",
            "description": "Monthly sales data with revenue, expenses, and customer counts",
            "data": sales_data.to_dict('records'),
            "columns": list(sales_data.columns)
        })
        
        # Stock prices sample
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        stock_data = pd.DataFrame({
            'Date': dates.strftime('%Y-%m-%d').tolist(),
            'Open': 100 + np.cumsum(np.random.randn(100)),
            'High': 100 + np.cumsum(np.random.randn(100)) + np.random.rand(100) * 5,
            'Low': 100 + np.cumsum(np.random.randn(100)) - np.random.rand(100) * 5,
            'Close': 100 + np.cumsum(np.random.randn(100)),
            'Volume': np.random.randint(1000000, 10000000, 100)
        })
        datasets.append({
            "name": "Stock Prices",
            "description": "Daily stock prices with OHLC data",
            "data": stock_data.head(20).to_dict('records'),
            "columns": list(stock_data.columns)
        })
        
        # Employee survey data
        departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance']
        employee_data = pd.DataFrame({
            'Department': np.random.choice(departments, 200),
            'Satisfaction': np.random.randint(1, 11, 200),
            'Salary': np.random.randint(40000, 150000, 200),
            'Years_Experience': np.random.randint(0, 20, 200),
            'Remote_Work': np.random.choice(['Yes', 'No'], 200)
        })
        datasets.append({
            "name": "Employee Survey",
            "description": "Employee satisfaction and salary data by department",
            "data": employee_data.head(20).to_dict('records'),
            "columns": list(employee_data.columns)
        })
        
        return {"datasets": datasets}
    
    def load_sample_dataset(self, dataset_name: str) -> Dict[str, Any]:
        """Load one of the sample datasets."""
        samples = self.get_sample_datasets()["datasets"]
        
        for sample in samples:
            if sample["name"] == dataset_name:
                self.current_df = pd.DataFrame(sample["data"])
                self.current_file = f"sample://{dataset_name}"
                return self._get_data_summary()
        
        return {"error": f"Dataset {dataset_name} not found"}


# Global instance
data_analyzer = DataAnalyzer()
