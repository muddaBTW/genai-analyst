"""
Data service for dataset loading, metadata extraction, and statistical analysis.
"""

import math
from io import BytesIO

import numpy as np
import pandas as pd


def _nan_safe(obj):
    """Recursively replace NaN and Inf with None so JSON serialization works."""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _nan_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_nan_safe(v) for v in obj]
    return obj


def _format_summary_value(value):
    """Format values for human-readable summary text."""
    if value is None:
        return "N/A"
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    if isinstance(value, (float, np.floating)):
        num = float(value)
        if math.isnan(num) or math.isinf(num):
            return "N/A"
        if num.is_integer():
            return f"{int(num):,}"
        return f"{num:,.2f}"
    return str(value)


def _is_artifact_unnamed_column(df: pd.DataFrame, column_name: str) -> bool:
    """Detect CSV index columns like 'Unnamed: 0' that should be hidden."""
    normalized = str(column_name).strip().lower()
    if not (normalized == "unnamed" or normalized.startswith("unnamed:")):
        return False

    series = df[column_name]
    non_null = series.dropna()
    if non_null.empty:
        return True

    numeric = pd.to_numeric(non_null, errors="coerce")
    if numeric.isna().any():
        return False

    expected = pd.Series(range(len(df)), index=df.index, dtype="int64")
    return numeric.astype("int64").reset_index(drop=True).equals(
        expected.reset_index(drop=True)
    )


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Remove import artifacts that should not appear as real columns."""
    artifact_columns = [
        col for col in df.columns if _is_artifact_unnamed_column(df, col)
    ]
    if artifact_columns:
        return df.drop(columns=artifact_columns)
    return df


def load_dataset(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Read CSV or Excel bytes into a DataFrame."""
    buf = BytesIO(file_bytes)
    if filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(buf, engine="openpyxl")
    else:
        df = pd.read_csv(buf)
    return _clean_dataframe(df)


def get_metadata(df: pd.DataFrame) -> dict:
    """Return column names, dtypes, missing-value counts, and shape."""
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": df.columns.tolist(),
        "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": {k: int(v) for k, v in df.isnull().sum().to_dict().items()},
        "total_missing": int(df.isnull().sum().sum()),
    }


def get_preview(df: pd.DataFrame, n: int = 10) -> list[dict]:
    """Return the first n rows as a list of dicts."""
    preview = df.head(n).fillna("").to_dict(orient="records")
    return _nan_safe(preview)


def get_summary_stats(df: pd.DataFrame) -> dict:
    """Descriptive statistics for numeric and categorical columns."""
    numeric = df.select_dtypes(include="number")
    categorical = df.select_dtypes(exclude="number")

    result = {}
    if not numeric.empty:
        desc = numeric.describe().round(2)
        result["numeric"] = _nan_safe(desc.to_dict())
    if not categorical.empty:
        desc = categorical.describe()
        result["categorical"] = _nan_safe(desc.to_dict())
    return result


def get_correlations(df: pd.DataFrame) -> dict | None:
    """Pearson correlation for numeric columns. Returns None when fewer than two exist."""
    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        return None
    corr = numeric.corr().round(3)
    return {
        "columns": corr.columns.tolist(),
        "values": _nan_safe(corr.values.tolist()),
    }


def get_distributions(df: pd.DataFrame) -> dict:
    """Value counts for categoricals and basic histogram bins for numerics."""
    distributions = {"numeric": {}, "categorical": {}}

    for col in df.select_dtypes(include="number").columns:
        clean = df[col].dropna()
        if clean.empty:
            continue
        counts, bin_edges = np.histogram(clean, bins=min(20, len(clean)))
        distributions["numeric"][col] = {
            "counts": counts.tolist(),
            "bin_edges": [round(float(b), 4) for b in bin_edges],
        }

    for col in df.select_dtypes(exclude="number").columns:
        vc = df[col].value_counts().head(15)
        distributions["categorical"][col] = {
            "labels": vc.index.astype(str).tolist(),
            "counts": vc.values.tolist(),
        }

    return distributions


def get_missing_analysis(df: pd.DataFrame) -> list[dict]:
    """Per-column missing counts and percentages."""
    total = len(df)
    analysis = []
    for col in df.columns:
        missing = int(df[col].isnull().sum())
        analysis.append(
            {
                "column": col,
                "missing_count": missing,
                "missing_percent": round(missing / total * 100, 2) if total else 0,
            }
        )
    return analysis


def build_llm_summary(df: pd.DataFrame) -> str:
    """Create a concise, human-readable dataset summary for the LLM."""
    meta = get_metadata(df)
    stats = get_summary_stats(df)
    missing = get_missing_analysis(df)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

    parts = [
        "Dataset overview:",
        f"- Size: {meta['rows']:,} rows x {meta['columns']:,} columns",
        f"- Columns: {', '.join(meta['column_names'])}",
        f"- Numeric columns ({len(numeric_cols)}): {', '.join(numeric_cols) if numeric_cols else 'None'}",
        f"- Categorical columns ({len(categorical_cols)}): {', '.join(categorical_cols) if categorical_cols else 'None'}",
        f"- Total missing values: {meta['total_missing']:,}",
    ]

    if "numeric" in stats:
        parts.append("\nNumeric highlights:")
        for col, values in stats["numeric"].items():
            parts.append(
                "  "
                f"{col}: average {_format_summary_value(values.get('mean'))}, "
                f"median {_format_summary_value(values.get('50%'))}, "
                f"range {_format_summary_value(values.get('min'))} to {_format_summary_value(values.get('max'))}"
            )

    if "categorical" in stats:
        parts.append("\nCategorical highlights:")
        for col, values in stats["categorical"].items():
            parts.append(
                "  "
                f"{col}: {_format_summary_value(values.get('unique'))} unique values, "
                f"most common '{_format_summary_value(values.get('top'))}', "
                f"appearing {_format_summary_value(values.get('freq'))} times"
            )

    cols_with_missing = [item for item in missing if item["missing_count"] > 0]
    if cols_with_missing:
        parts.append("\nMissing data:")
        for item in cols_with_missing:
            parts.append(
                f"  {item['column']}: {_format_summary_value(item['missing_count'])} "
                f"missing ({_format_summary_value(item['missing_percent'])}%)"
            )

    corr = get_correlations(df)
    if corr:
        parts.append("\nTop correlations:")
        cols = corr["columns"]
        vals = corr["values"]
        pairs = []
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                value = vals[i][j]
                if value is not None:
                    pairs.append((cols[i], cols[j], value))
        pairs.sort(key=lambda item: abs(item[2]), reverse=True)
        for left, right, value in pairs[:5]:
            parts.append(
                f"  {left} and {right}: correlation {_format_summary_value(value)}"
            )

    return "\n".join(parts)
