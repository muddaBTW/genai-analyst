"""
Visualizations Router — generates Plotly chart specs for the frontend.
"""

from fastapi import APIRouter, HTTPException

from routers.upload import get_current_df
from services.viz_service import generate_all_charts

router = APIRouter()


@router.get("/visualizations")
def get_visualizations():
    """Return Plotly JSON chart definitions for the current dataset."""
    df = get_current_df()
    if df is None:
        raise HTTPException(400, "No dataset uploaded yet.")

    charts = generate_all_charts(df)
    return charts
