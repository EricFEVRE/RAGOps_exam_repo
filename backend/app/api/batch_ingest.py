from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.pdf_processor import PDFProcessor
from app.services.ingestion import ingest_documents
from app.services.minio_client import upload_file
from app.services.db import log_document_metadata
from app.models.documents import Document
import tempfile, os, logging
from typing import List, Optional

router = APIRouter()
logger = logging.getLogger(__name__)
pdf_processor = PDFProcessor()

@router.post("/ingest-pdf-batch")
async def ingest_pdf_batch(files: List[UploadFile] = File(...), metadata: Optional[dict] = None):
    results = []

    for file in files:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"Only PDF files supported: {file.filename}")

        try:
            content = await file.read()

            # 1. Store raw PDF in MinIO
            object_name = f"pdfs/{file.filename}"
            try:
                minio_path = upload_file(object_name, content, "application/pdf")
            except Exception as e:
                logger.warning(f"MinIO upload failed for {file.filename} (non-blocking): {e}")
                minio_path = f"s3://documents/{object_name}"

            # 2. Write to temp file for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name

            # 3. Process into LangChain Documents
            documents = await pdf_processor.process_pdf(tmp_path, metadata)

            # 4. Convert and ingest
            ragops_docs = [
                Document(
                    id=doc.metadata["chunk_id"],
                    text=doc.page_content,
                    metadata=doc.metadata,
                )
                for doc in documents
            ]
            result = await ingest_documents(ragops_docs)
            os.unlink(tmp_path)

            chunk_count = len(documents)

            # 5. Log metadata in PostgreSQL
            try:
                log_document_metadata(
                    filename=file.filename,
                    minio_path=minio_path,
                    chunk_count=chunk_count,
                    embedding_model="local-embeddings",
                )
            except Exception as e:
                logger.warning(f"Metadata logging failed for {file.filename} (non-blocking): {e}")

            results.append({
                "filename": file.filename,
                "pages_processed": max(doc.metadata["page_number"] for doc in documents),
                "chunks_created": chunk_count,
                **result,
            })

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ingestion failed for {file.filename}: {str(e)}")
            results.append({"filename": file.filename, "error": str(e)})

    return results
