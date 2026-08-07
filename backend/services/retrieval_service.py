"""
Retrieval service — create embeddings for dataset rows, build FAISS index,
and provide search functionality for RAG.

This is a minimal, interview-ready implementation:
- Uses `sentence-transformers` for embeddings
- Uses `faiss` for a local vector index
- Persists the FAISS index and metadata under `backend/.vector_store/`
"""
from __future__ import annotations

import json
import os
import pickle
from pathlib import Path
from typing import List, Dict, Any

import numpy as np

from services.data_service import build_llm_summary

_MODEL = None
_FAISS = None


class _TfidfFallback:
    """A tiny wrapper around sklearn's TfidfVectorizer providing an `encode` API."""
    def __init__(self, vec=None):
        self._vec = vec
        self._fitted = bool(vec)

    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
        if not self._fitted:
            # fit on provided texts
            self._vec = __import__("sklearn.feature_extraction.text", fromlist=["TfidfVectorizer"]).TfidfVectorizer(max_features=4096)
            self._vec.fit(texts)
            self._fitted = True
        mat = self._vec.transform(texts)
        return mat.toarray()

VSTORE_DIR = Path(__file__).resolve().parents[1] / ".vector_store"
VSTORE_DIR.mkdir(exist_ok=True)
INDEX_PATH = VSTORE_DIR / "index.faiss"
META_PATH = VSTORE_DIR / "metadata.pkl"


def _get_embedding_model(name: str = "all-MiniLM-L6-v2"):
    global _MODEL
    if name and name.lower() in ("tfidf", "tfidf-fallback"):
        # force TF-IDF fallback
        return _TfidfFallback()

    if _MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer

            _MODEL = SentenceTransformer(name)
        except Exception as e:
            # Fall back to a lightweight TF-IDF based encoder if SentenceTransformer
            # cannot be loaded (common on Windows when huggingface_hub mismatches).
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer

                class _TfidfFallback:
                    def __init__(self):
                        self._vec = TfidfVectorizer(max_features=4096)
                        self._fitted = False

                    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
                        # fit vectorizer on provided texts the first time
                        if not self._fitted:
                            self._vec.fit(texts)
                            self._fitted = True
                        mat = self._vec.transform(texts)
                        arr = mat.toarray()
                        return arr

                _MODEL = _TfidfFallback()
            except Exception:
                raise RuntimeError(
                    "Failed to load embedding model. Install compatible `huggingface_hub`/`sentence-transformers` or `scikit-learn` for fallback."
                )
    return _MODEL


def _ensure_faiss():
    global _FAISS
    if _FAISS is None:
        try:
            import faiss

            _FAISS = faiss
        except Exception as e:
            raise RuntimeError(
                "faiss is required for retrieval. Install faiss-cpu or use an alternative."
            )
    return _FAISS


def row_to_text(idx: int, row: Dict[str, Any]) -> str:
    parts = [f"row {idx}"]
    for k, v in row.items():
        parts.append(f"{k}: {v}")
    return " — ".join(parts)


def build_index(df, embedding_model: str = "all-MiniLM-L6-v2") -> Dict[str, Any]:
    """Build and persist a FAISS index for the given dataframe.

    Returns metadata including number of vectors indexed.
    """
    faiss = _ensure_faiss()
    model = _get_embedding_model(embedding_model)

    records = df.fillna("").to_dict(orient="records")
    texts = [row_to_text(i, rec) for i, rec in enumerate(records)]

    # compute embeddings
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    if embeddings.ndim == 1:
        embeddings = np.expand_dims(embeddings, 0)

    dim = embeddings.shape[1]

    # create index
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # persist
    faiss.write_index(index, str(INDEX_PATH))
    metadata = {
        "texts": texts,
        "rows": records,
        "embedding_model": embedding_model,
    }
    # If using TF-IDF fallback, persist the fitted vectorizer so searches survive restarts
    try:
        if hasattr(model, "_vec") and model._vec is not None:
            metadata["tfidf_vectorizer"] = model._vec
    except Exception:
        pass
    with open(META_PATH, "wb") as f:
        pickle.dump(metadata, f)

    return {"vectors_indexed": len(texts), "path": str(VSTORE_DIR)}


def _load_index_and_meta():
    faiss = _ensure_faiss()
    if not INDEX_PATH.exists() or not META_PATH.exists():
        raise RuntimeError("Vector store not found. Build the index first.")

    index = faiss.read_index(str(INDEX_PATH))
    with open(META_PATH, "rb") as f:
        metadata = pickle.load(f)
    # If metadata contains a persisted TF-IDF vectorizer, restore a local fallback model
    try:
        if "tfidf_vectorizer" in metadata:
            vec = metadata.get("tfidf_vectorizer")
            global _MODEL
            _MODEL = _TfidfFallback(vec=vec)
    except Exception:
        pass
    return index, metadata


def search(query: str, top_k: int = 5, embedding_model: str = "all-MiniLM-L6-v2") -> List[Dict[str, Any]]:
    """Return top_k matching rows for the query.

    Each result contains: `row_index`, `text`, `row`, `score`.
    """
    index, metadata = _load_index_and_meta()
    model = _get_embedding_model(embedding_model)

    q_emb = model.encode([query], convert_to_numpy=True)
    faiss = _ensure_faiss()

    D, I = index.search(np.asarray(q_emb, dtype=np.float32), top_k)
    results = []
    for score, idx in zip(D[0], I[0]):
        if idx < 0:
            continue
        results.append(
            {
                "row_index": int(idx),
                "text": metadata["texts"][idx],
                "row": metadata["rows"][idx],
                "score": float(score),
            }
        )
    return results
