"""
Visualizations Router — generates Plotly chart specs for the frontend.
"""

from fastapi import APIRouter, HTTPException

from routers.upload import get_current_df
from services.viz_service import generate_all_charts
from services.data_service import build_llm_summary
from services.ai_service import suggest_visualizations

router = APIRouter()


@router.get("/visualizations")
def get_visualizations():
    """Return Plotly JSON chart definitions for the current dataset, including AI-driven smart charts."""
    print("DEBUG: get_visualizations called")
    df = get_current_df()
    if df is None:
        raise HTTPException(400, "No dataset uploaded yet.")

    # 1. Build summary for the LLM
    summary = build_llm_summary(df)
    
    # 2. Get AI suggestions for "smart" charts
    # (Note: In a production app, we might cache this)
    suggestions = suggest_visualizations(summary)
    
    # Generate all charts (standard + AI)
    viz_data = generate_all_charts(df, suggestions)
    
    return viz_data
