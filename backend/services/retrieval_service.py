"""RAG storage: Supabase pgvector in production, FAISS only for local development."""
from __future__ import annotations

import json
import os
import pickle
import tempfile
from pathlib import Path
from typing import Any

import httpx
import numpy as np

from services.data_service import build_llm_summary

EMBEDDING_DIMENSIONS = 768
VSTORE_DIR = Path(tempfile.gettempdir()) / "genai_analyst_vector_store" if os.getenv("VERCEL") else Path(__file__).resolve().parents[1] / ".vector_store"
VSTORE_DIR = Path(os.getenv("VECTOR_STORE_DIR", str(VSTORE_DIR)))
VSTORE_DIR.mkdir(exist_ok=True)
INDEX_PATH, META_PATH = VSTORE_DIR / "index.faiss", VSTORE_DIR / "metadata.pkl"
_MODEL = None
_FAISS = None


def _supabase_settings() -> tuple[str, str] | None:
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    return (url, key) if url and key else None


def _headers(key: str, prefer: str | None = None) -> dict[str, str]:
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _embed(texts: list[str], task_type: str) -> list[list[float]]:
    """Create normalized Gemini embeddings without shipping ML model weights to Vercel."""
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required for Supabase RAG embeddings")
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:batchEmbedContents"
    requests = [
        {"model": "models/gemini-embedding-2", "content": {"parts": [{"text": text[:32000]}]}, "taskType": task_type, "outputDimensionality": EMBEDDING_DIMENSIONS}
        for text in texts
    ]
    response = httpx.post(url, params={"key": api_key}, json={"requests": requests}, timeout=55)
    response.raise_for_status()
    return [item["values"] for item in response.json()["embeddings"]]


def row_to_text(idx: int, row: dict[str, Any]) -> str:
    return " — ".join([f"row {idx}"] + [f"{key}: {value}" for key, value in row.items()])


def _build_supabase_index(df, dataset_id: str) -> dict[str, Any]:
    settings = _supabase_settings()
    assert settings
    url, key = settings
    records = df.fillna("").to_dict(orient="records")
    texts = [row_to_text(index, row) for index, row in enumerate(records)]
    summary = build_llm_summary(df)
    with httpx.Client(timeout=55) as client:
        dataset = {"id": dataset_id, "summary": summary, "row_count": len(records)}
        response = client.post(f"{url}/rest/v1/rag_datasets", headers=_headers(key, "resolution=merge-duplicates"), json=dataset)
        response.raise_for_status()
        response = client.delete(f"{url}/rest/v1/rag_dataset_rows", headers=_headers(key), params={"dataset_id": f"eq.{dataset_id}"})
        response.raise_for_status()
        # Gemini accepts batches; keeping them small avoids request-size limits.
        for start in range(0, len(texts), 50):
            batch_texts, batch_rows = texts[start:start + 50], records[start:start + 50]
            embeddings = _embed(batch_texts, "RETRIEVAL_DOCUMENT")
            payload = [
                {"dataset_id": dataset_id, "row_index": start + offset, "content": text, "row_data": row, "embedding": embedding}
                for offset, (text, row, embedding) in enumerate(zip(batch_texts, batch_rows, embeddings))
            ]
            response = client.post(f"{url}/rest/v1/rag_dataset_rows", headers=_headers(key, "return=minimal"), json=payload)
            response.raise_for_status()
    return {"vectors_indexed": len(records), "storage": "supabase-pgvector", "dataset_id": dataset_id}


def _search_supabase(query: str, dataset_id: str, top_k: int) -> list[dict[str, Any]]:
    settings = _supabase_settings()
    assert settings
    url, key = settings
    embedding = _embed([query], "RETRIEVAL_QUERY")[0]
    response = httpx.post(
        f"{url}/rest/v1/rpc/match_dataset_rows", headers=_headers(key), timeout=30,
        json={"query_embedding": embedding, "match_dataset_id": dataset_id, "match_count": top_k},
    )
    response.raise_for_status()
    return [
        {
            "row_index": item["row_index"],
            "text": item["text"],
            "row": item["row_payload"],
            "score": item["score"],
        }
        for item in response.json()
    ]


def get_dataset_summary(dataset_id: str) -> str | None:
    settings = _supabase_settings()
    if not settings:
        return None
    url, key = settings
    response = httpx.get(f"{url}/rest/v1/rag_datasets", headers=_headers(key), params={"id": f"eq.{dataset_id}", "select": "summary"}, timeout=20)
    response.raise_for_status()
    rows = response.json()
    return rows[0]["summary"] if rows else None


def _get_embedding_model():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def _faiss():
    global _FAISS
    if _FAISS is None:
        import faiss
        _FAISS = faiss
    return _FAISS


def _build_local_index(df) -> dict[str, Any]:
    records = df.fillna("").to_dict(orient="records")
    texts = [row_to_text(index, row) for index, row in enumerate(records)]
    vectors = _get_embedding_model().encode(texts, convert_to_numpy=True, show_progress_bar=False)
    index = _faiss().IndexFlatL2(vectors.shape[1])
    index.add(np.asarray(vectors, dtype=np.float32))
    _faiss().write_index(index, str(INDEX_PATH))
    with open(META_PATH, "wb") as file:
        pickle.dump({"texts": texts, "rows": records}, file)
    return {"vectors_indexed": len(records), "storage": "local-faiss"}


def build_index(df, dataset_id: str | None = None) -> dict[str, Any]:
    """Index rows in Supabase when configured; retain local FAISS for development."""
    if _supabase_settings():
        if not dataset_id:
            raise RuntimeError("A dataset_id is required for Supabase RAG")
        return _build_supabase_index(df, dataset_id)
    return _build_local_index(df)


def search(query: str, top_k: int = 5, dataset_id: str | None = None) -> list[dict[str, Any]]:
    if _supabase_settings():
        if not dataset_id:
            raise RuntimeError("A dataset_id is required for Supabase RAG")
        return _search_supabase(query, dataset_id, top_k)
    if not INDEX_PATH.exists() or not META_PATH.exists():
        raise RuntimeError("Vector store not found. Build the index first.")
    index = _faiss().read_index(str(INDEX_PATH))
    with open(META_PATH, "rb") as file:
        metadata = pickle.load(file)
    vector = _get_embedding_model().encode([query], convert_to_numpy=True)
    distances, indices = index.search(np.asarray(vector, dtype=np.float32), top_k)
    return [{"row_index": int(idx), "text": metadata["texts"][idx], "row": metadata["rows"][idx], "score": float(score)} for score, idx in zip(distances[0], indices[0]) if idx >= 0]
