"""
Analysis Router — runs automatic data analysis on the uploaded dataset.
"""

from fastapi import APIRouter, HTTPException

from routers.upload import get_current_df
from services.data_service import (
    get_summary_stats,
    get_correlations,
    get_distributions,
    get_missing_analysis,
    get_metadata,
)

router = APIRouter()


@router.get("/analyze")
def analyze_dataset():
    """Return full automated analysis of the current dataset."""
    df = get_current_df()
    if df is None:
        raise HTTPException(400, "No dataset uploaded yet.")

    return {
        "metadata": get_metadata(df),
        "summary_stats": get_summary_stats(df),
        "correlations": get_correlations(df),
        "distributions": get_distributions(df),
        "missing_analysis": get_missing_analysis(df),
    }
