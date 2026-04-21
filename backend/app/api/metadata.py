import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.db import log_document_metadata, get_document_metadata
from app.services.minio_client import upload_file

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Store a raw file in MinIO, log metadata in PostgreSQL,
    and return the generated document_id.
    """
    content = await file.read()
    filename = file.filename or "unknown"

    # Build a unique object key to avoid collisions
    ext = os.path.splitext(filename)[1]
    object_name = f"{uuid.uuid4().hex}{ext}"

    # Detect content type
    content_type = file.content_type or "application/octet-stream"

    try:
        minio_path = upload_file(object_name, content, content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MinIO upload failed: {e}")

    try:
        document_id = log_document_metadata(
            filename=filename,
            minio_path=minio_path,
            chunk_count=0,
            embedding_model="local-embeddings",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metadata logging failed: {e}")

    return {"document_id": document_id, "minio_path": minio_path, "filename": filename}


@router.get("/metadata/{document_id}")
async def get_metadata(document_id: int):
    """Retrieve metadata for a previously uploaded document."""
    meta = get_document_metadata(document_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return meta