"""
Query Router — natural language Q&A about the dataset.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from routers.upload import get_current_df
from services.data_service import build_llm_summary
from services.ai_service import answer_question

router = APIRouter()


class QuestionRequest(BaseModel):
    question: str


@router.post("/query")
def query_dataset(body: QuestionRequest):
    """Answer a natural language question about the dataset."""
    df = get_current_df()
    if df is None:
        raise HTTPException(400, "No dataset uploaded yet.")

    if not body.question.strip():
        raise HTTPException(400, "Question cannot be empty.")

    summary = build_llm_summary(df)

    try:
        answer = answer_question(body.question, summary)
    except Exception as e:
        raise HTTPException(502, f"AI service error: {e}")

    return {"question": body.question, "answer": answer}
