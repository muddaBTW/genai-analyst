"""
Visualization Service — generates Plotly chart JSON specs for the frontend.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import numpy as np
from scipy import stats


def _fig_to_json(fig) -> dict:
    """Convert a Plotly figure to a JSON-serialisable dict."""
    return json.loads(fig.to_json())


def _is_useful_column(df: pd.DataFrame, col: str, col_type: str = "auto") -> bool:
    """
    Check if a column is likely to produce a meaningful chart.
    
    Filters out:
    - ID-like columns
    - Constant or near-constant columns
    - Columns with too many unique values (uninterpretable)
    - Columns with poor variance or distribution
    """
    # 1. Skip if only 0 or 1 unique values
    unique_count = df[col].nunique()
    if unique_count <= 1:
        return False

    # 2. Skip if it smells like an ID column
    name_low = col.lower()
    is_id_named = any(x in name_low for x in ["id", "uuid", "key", "index", "unnamed", "code", "no.", "serial"])
    
    if is_id_named:
        if unique_count > 10: 
            return False

    # 3. For numeric columns, skip if almost all values are unique (ID-like)
    if pd.api.types.is_integer_dtype(df[col]):
        ratio = unique_count / len(df)
        if ratio > 0.8 and (is_id_named or df[col].max() > 1000):
            return False

    # 4. For categorical columns: skip if cardinality is too high or too low
    if col_type == "auto":
        is_numeric = pd.api.types.is_numeric_dtype(df[col])
    else:
        is_numeric = col_type == "numeric"

    if not is_numeric:  # Categorical
        # Skip if too many unique values (can't summarize in bar chart)
        if unique_count > 50:
            return False
        # Skip if almost all values are uniform (no pattern)
        top_count = df[col].value_counts().iloc[0]
        concentration = top_count / len(df)
        if concentration > 0.95 and unique_count > 1:
            return False

    else:  # Numeric
        # Skip if variance is extremely low (constant-ish)
        valid_vals = df[col].dropna()
        if len(valid_vals) < 2:
            return False
        
        std = valid_vals.std()
        mean = valid_vals.mean()
        
        # If std is near zero, skip
        if std == 0 or (mean != 0 and std / abs(mean) < 0.01):
            return False
        
        # Skip if data is too concentrated (>90% in top bin)
        # This catches heavily skewed distributions that don't visualize well
        q75 = valid_vals.quantile(0.75)
        q25 = valid_vals.quantile(0.25)
        if q75 == q25:  # No spread in middle 50%
            return False

    return True


def generate_histograms(df: pd.DataFrame) -> list[dict]:
    """Histogram for every useful numeric column."""
    charts = []
    for col in df.select_dtypes(include="number").columns:
        if not _is_useful_column(df, col, col_type="numeric"):
            continue
        
        valid_vals = df[col].dropna()
        if len(valid_vals) < 3:
            continue
        
        # Skip if distribution is too concentrated in one area
        # Compute if 80%+ of values fall within a narrow range
        p10, p90 = valid_vals.quantile([0.1, 0.9])
        p25, p75 = valid_vals.quantile([0.25, 0.75])
        iqr = p75 - p25
        
        # If IQR is near zero or range is very small, skip
        if iqr == 0 or (p90 - p10) < (valid_vals.std() * 0.5):
            continue
        
        fig = px.histogram(
            df, x=col, title=f"Distribution of {col}",
            template="plotly_dark",
            color_discrete_sequence=["#6366f1"],
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
            margin=dict(l=40, r=20, t=50, b=40),
        )
        charts.append({"type": "histogram", "column": col, "figure": _fig_to_json(fig)})
    return charts


def generate_bar_charts(df: pd.DataFrame) -> list[dict]:
    """Bar chart for every useful categorical column (top 10 values)."""
    charts = []
    for col in df.select_dtypes(exclude="number").columns:
        if not _is_useful_column(df, col, col_type="categorical"):
            continue
        
        vc = df[col].value_counts().head(10)
        
        # Additional filter: skip if top 10 is too unbalanced
        # (e.g., one value is 80% of data, not interesting)
        top_ratio = vc.iloc[0] / len(df)
        if top_ratio > 0.8:
            continue
        
        fig = px.bar(
            x=vc.index.astype(str), y=vc.values,
            labels={"x": col, "y": "Count"},
            title=f"Top Values in {col}",
            template="plotly_dark",
            color_discrete_sequence=["#8b5cf6"],
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
            margin=dict(l=40, r=20, t=50, b=40),
        )
        charts.append({"type": "bar", "column": col, "figure": _fig_to_json(fig)})
    return charts


def generate_correlation_heatmap(df: pd.DataFrame) -> dict | None:
    """Correlation heatmap for numeric columns. Returns None if < 2 numeric cols."""
    numeric = df.select_dtypes(include="number")
    # Even in heatmap, skip ID-like columns for clarity
    useful_cols = [c for c in numeric.columns if _is_useful_column(df, c, col_type="numeric")]
    if len(useful_cols) < 2:
        return None
    
    numeric = numeric[useful_cols]
    corr = numeric.corr().round(3)
    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.columns.tolist(),
        colorscale="Viridis",
        text=corr.values.round(2),
        texttemplate="%{text}",
        textfont={"size": 10},
    ))
    fig.update_layout(
        title="Correlation Heatmap",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#e2e8f0",
        margin=dict(l=40, r=20, t=50, b=40),
        height=500,
    )
    return {"type": "heatmap", "figure": _fig_to_json(fig)}


def generate_scatter_plots(df: pd.DataFrame, max_plots: int = 3) -> list[dict]:
    """Scatter plots for the most-correlated numeric pairs (filtering useless ones)."""
    numeric = df.select_dtypes(include="number")
    useful_cols = [c for c in numeric.columns if _is_useful_column(df, c, col_type="numeric")]
    if len(useful_cols) < 2:
        return []
    
    numeric = numeric[useful_cols]
    corr = numeric.corr()
    pairs = []
    cols = corr.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = corr.iloc[i, j]
            if not pd.isna(val):
                pairs.append((cols[i], cols[j], abs(val)))
    
    # Sort by correlation strength (already absolute value)
    pairs.sort(key=lambda x: x[2], reverse=True)
    
    # Only include pairs with meaningful correlation (|r| > 0.2)
    pairs = [p for p in pairs if p[2] > 0.2]

    charts = []
    for a, b, corr_val in pairs[:max_plots]:
        fig = px.scatter(
            df, x=a, y=b, title=f"{a} vs {b} (r={corr_val:.2f})",
            template="plotly_dark",
            color_discrete_sequence=["#f472b6"],
            opacity=0.7,
            trendline="ols" if len(df) > 5 else None
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
            margin=dict(l=40, r=20, t=50, b=40),
        )
        charts.append({"type": "scatter", "columns": [a, b], "figure": _fig_to_json(fig)})
    return charts


def generate_ai_visualizations(df: pd.DataFrame, suggestions: list[dict]) -> list[dict]:
    """Convert AI suggestions into actual Plotly figure JSONs."""
    charts = []
    for sug in suggestions:
        try:
            v_type = sug.get("type", "scatter").lower()
            kwargs = sug.get("kwargs", {})
            title = sug.get("title", "Smart Insight")

            # Basic safety: ensure columns exist
            cols = [v for k, v in kwargs.items() if k in ["x", "y", "color", "facet_col", "size"]]
            if not all(c in df.columns for c in cols):
                continue

            # Route to Plotly Express
            func = getattr(px, v_type, px.scatter)
            
            # Inject dark theme and styling
            kwargs.update({
                "title": title,
                "template": "plotly_dark",
                "color_discrete_sequence": px.colors.qualitative.Pastel
            })
            
            fig = func(df, **kwargs)
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e2e8f0",
                margin=dict(l=40, r=20, t=50, b=40),
            )
            charts.append({"type": "ai_smart", "suggestion": sug, "figure": _fig_to_json(fig)})
        except Exception as e:
            print(f"Error generating AI chart: {e}")
            continue
    return charts


def generate_all_charts(df: pd.DataFrame, ai_suggestions: list[dict] | None = None) -> dict:
    """Generate every chart type and return them grouped."""
    res = {
        "smart_visualizations": generate_ai_visualizations(df, ai_suggestions or []),
        "histograms": generate_histograms(df),
        "bar_charts": generate_bar_charts(df),
        "heatmap": generate_correlation_heatmap(df),
        "scatter_plots": generate_scatter_plots(df),
    }
    
    # Debug logging
    print(f"DEBUG: Generated {len(res['smart_visualizations'])} smart charts")
    print(f"DEBUG: Generated {len(res['histograms'])} histograms")
    print(f"DEBUG: Generated {len(res['bar_charts'])} bar charts")
    
    return {
        "version": "2.1",
        "charts": res
    }
