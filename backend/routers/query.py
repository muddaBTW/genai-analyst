"""
Query Router — natural language Q&A about the dataset.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import os

from routers.upload import get_current_df
from services.data_service import build_llm_summary
from services.ai_service import answer_question, answer_with_rag
from services.retrieval_service import search

router = APIRouter()


class QuestionRequest(BaseModel):
    question: str
    history: list[dict[str, str]] = Field(default_factory=list, max_length=8)


@router.post("/query")
def query_dataset(body: QuestionRequest):
    """Answer a natural language question about the dataset."""
    df = get_current_df()
    if df is None:
        raise HTTPException(400, "No dataset uploaded yet.")

    if not body.question.strip():
        raise HTTPException(400, "Question cannot be empty.")

    # If RAG is enabled and an index exists, use retrieval first
    rag_enabled = os.getenv("RAG_ENABLED", "false").lower() in ("1", "true", "yes")
    if rag_enabled:
        try:
            retrieved = search(body.question, top_k=5)
            answer = answer_with_rag(body.question, retrieved, body.history)
            return {"question": body.question, "answer": answer, "retrieved": retrieved}
        except Exception:
            # Fall back to non-RAG behavior if retrieval fails
            pass

    summary = build_llm_summary(df)
    try:
        answer = answer_question(body.question, summary, body.history)
    except Exception as e:
        raise HTTPException(502, f"AI service error: {e}")

    return {"question": body.question, "answer": answer}
