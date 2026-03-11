"""
Insights Router — sends dataset summary to Groq LLM and returns AI insights.
"""

from fastapi import APIRouter, HTTPException

from routers.upload import get_current_df
from services.data_service import build_llm_summary
from services.ai_service import generate_insights

router = APIRouter()


@router.get("/insights")
def get_insights():
    """Generate AI insights for the current dataset."""
    df = get_current_df()
    if df is None:
        raise HTTPException(400, "No dataset uploaded yet.")

    summary = build_llm_summary(df)

    try:
        insights = generate_insights(summary)
    except Exception as e:
        raise HTTPException(502, f"AI service error: {e}")

    return {"insights": insights}
