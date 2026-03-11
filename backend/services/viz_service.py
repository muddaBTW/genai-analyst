"""
Visualization Service — generates Plotly chart JSON specs for the frontend.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json


def _fig_to_json(fig) -> dict:
    """Convert a Plotly figure to a JSON-serialisable dict."""
    return json.loads(fig.to_json())


def generate_histograms(df: pd.DataFrame) -> list[dict]:
    """Histogram for every numeric column."""
    charts = []
    for col in df.select_dtypes(include="number").columns:
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
    """Bar chart for every categorical column (top 10 values)."""
    charts = []
    for col in df.select_dtypes(exclude="number").columns:
        vc = df[col].value_counts().head(10)
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
    if numeric.shape[1] < 2:
        return None
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
    """Scatter plots for the most-correlated numeric pairs."""
    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        return []
    corr = numeric.corr()
    pairs = []
    cols = corr.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            pairs.append((cols[i], cols[j], abs(corr.iloc[i, j])))
    pairs.sort(key=lambda x: x[2], reverse=True)

    charts = []
    for a, b, _ in pairs[:max_plots]:
        fig = px.scatter(
            df, x=a, y=b, title=f"{a} vs {b}",
            template="plotly_dark",
            color_discrete_sequence=["#f472b6"],
            opacity=0.7,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
            margin=dict(l=40, r=20, t=50, b=40),
        )
        charts.append({"type": "scatter", "columns": [a, b], "figure": _fig_to_json(fig)})
    return charts


def generate_all_charts(df: pd.DataFrame) -> dict:
    """Generate every chart type and return them grouped."""
    return {
        "histograms": generate_histograms(df),
        "bar_charts": generate_bar_charts(df),
        "heatmap": generate_correlation_heatmap(df),
        "scatter_plots": generate_scatter_plots(df),
    }
