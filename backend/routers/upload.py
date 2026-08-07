"""
Upload Router — accepts CSV/Excel uploads, validates size, returns preview + metadata.
Uses an in-memory store so subsequent endpoints can reuse the loaded DataFrame.
"""

from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException

from services.data_service import load_dataset, get_metadata, get_preview

router = APIRouter()

# ── Shared in-memory store (simple single-user setup) ─────────────────────
# In production you'd use a session store or database.
_current_df = None


def get_current_df():
    """Accessor for other modules that need the loaded DataFrame."""
    return _current_df


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload a CSV or Excel file.
    Returns dataset preview (first 10 rows) and metadata.
    """
    global _current_df

    # Validate file type
    if not file.filename.lower().endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(400, "Only CSV and Excel files are supported.")

    # Read file bytes and check size (~50 MB limit)
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(413, "File too large. Maximum size is 50 MB.")

    try:
        df = load_dataset(contents, file.filename)
    except Exception as e:
        raise HTTPException(422, f"Failed to parse file: {e}")

    _current_df = df
    dataset_id = str(uuid4())

    return {
        "dataset_id": dataset_id,
        "filename": file.filename,
        "metadata": get_metadata(df),
        "preview": get_preview(df),
    }
