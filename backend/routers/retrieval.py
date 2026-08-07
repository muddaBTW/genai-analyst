"""Retrieval router — endpoints to build and inspect the vector index."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from routers.upload import get_current_df
from services.retrieval_service import build_index

router = APIRouter()


class IndexRequest(BaseModel):
    dataset_id: str | None = None


@router.post("/index")
def build_vector_index(body: IndexRequest | None = None):
    df = get_current_df()
    if df is None:
        raise HTTPException(400, "No dataset uploaded yet.")

    try:
        info = build_index(df, body.dataset_id if body else None)
    except Exception as e:
        msg = str(e)
        # If the failure looks like a Hugging Face hub import mismatch, retry with TF-IDF fallback
        if "huggingface_hub" in msg or "cached_download" in msg or "huggingface" in msg:
            try:
                info = build_index(df, body.dataset_id if body else None)
            except Exception as e2:
                raise HTTPException(500, f"Index build error (fallback failed): {e2}")
        else:
            raise HTTPException(500, f"Index build error: {e}")

    return {"status": "ok", "info": info}
