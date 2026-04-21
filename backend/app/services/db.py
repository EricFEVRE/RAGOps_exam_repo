import psycopg2
from contextlib import contextmanager
import os

POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql://ragops:ragops@postgres:5432/metadata")


@contextmanager
def get_db():
    """Context manager for PostgreSQL connections."""
    conn = psycopg2.connect(POSTGRES_URI)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def log_document_metadata(
    filename: str,
    minio_path: str,
    chunk_count: int = 0,
    embedding_model: str = "local-embeddings",
) -> int:
    """Insert document metadata and return the generated document_id."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (filename, minio_path, chunk_count, embedding_model)
                VALUES (%s, %s, %s, %s)
                RETURNING document_id
                """,
                (filename, minio_path, chunk_count, embedding_model),
            )
            row = cur.fetchone()
            return row[0]


def get_document_metadata(document_id: int) -> dict | None:
    """Retrieve metadata for a document by ID."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT document_id, filename, upload_time, chunk_count, embedding_model, minio_path
                FROM documents
                WHERE document_id = %s
                """,
                (document_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return {
                "document_id": row[0],
                "filename": row[1],
                "upload_time": row[2].isoformat() if row[2] else None,
                "chunk_count": row[3],
                "embedding_model": row[4],
                "minio_path": row[5],
            }