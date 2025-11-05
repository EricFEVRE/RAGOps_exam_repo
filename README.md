# RAGOps Exam Instructions – Metadata & Object Storage Integration

## 1. Context

The provided **RAGOps repository** includes the final state of the architecture on the course:

* A **FastAPI backend** orchestrating document ingestion, embedding, and retrieval.
* A **LiteLLM folder** that centralizes all LLM backends (OpenAI, Ollama, etc.).
* A **monitoring stack** using Prometheus + Grafana.
* Existing ingestion endpoints for plain text and PDFs (`ingest.py`, `pdf.py`, `batch_ingest.py`).

Your task is to **extend the system** so that all ingested documents are also:

1. Stored in an **Object Store (MinIO)**.
2. Logged in a **Metadata Store (PostgreSQL)** with relevant information (filename, upload time, storage path, chunk count, embedding model).

You should **not modify** the LiteLLM folder, the monitoring stack, or core RAGOps architecture beyond what is necessary to integrate metadata and MinIO.

All functionality must remain **runnable and testable** via:

```bash
docker-compose up --build
pytest tests/test_metadata.py
```

---

## 2. Integration Philosophy

* Keep **existing endpoints** functional. Do not remove or replace the text/PDF ingestion logic.
* Introduce **new services** for metadata and storage.
* Follow existing **FastAPI patterns**, including dependency injection.
* Add only the **required environment variables** for PostgreSQL and MinIO in `docker-compose.yml`.
* Ensure that **PDF ingestion** (single or batch) works with the new metadata & storage integration.

---

## 3. Repository Modifications

### 3.1 New Files to Create

| Path                                   | Purpose                                                               |
| -------------------------------------- | --------------------------------------------------------------------- |
| `backend/app/metadata.py`              | FastAPI router for handling metadata and file uploads.                |
| `backend/app/services/db.py`           | PostgreSQL connection utility with context manager.                   |
| `backend/app/services/minio_client.py` | MinIO client setup and bucket creation.                               |
| `db/`                                  | Folder containing database initialization scripts (e.g., `init.sql`). |

### 3.2 Files to Modify

| Path                                    | Purpose                                                                     |
| --------------------------------------- | --------------------------------------------------------------------------- |
| `backend/app/api/pdf.py`                | Update PDF ingestion to store files in MinIO and log metadata in Postgres.  |
| `backend/app/api/batch_ingest.py`       | Same as above, for batch PDF ingestion.                                     |
| `backend/app/main.py`                   | Register the new `metadata` router.                                         |
| `backend/app/services/ingestion.py`     | Ensure ingestion logic passes chunk info to metadata logging.               |
| `backend/app/services/pdf_processor.py` | Ensure processed PDF pages/chunks include metadata.                         |
| `backend/app/core/config.py`            | Add environment variables if needed for MinIO/PostgreSQL.                   |
| `docker-compose.yml`                    | Add `postgres` and `minio` services; set environment variables for backend. |

> **Important:** Do **not modify** `tests/test_metadata.py`. This file contains the automated tests used to validate your work.

---

## 4. Technical Requirements

### 4.1 PostgreSQL

* Use Docker service:

```yaml
postgres:
  image: postgres:15
  restart: always
  environment:
    POSTGRES_USER: ragops
    POSTGRES_PASSWORD: ragops
    POSTGRES_DB: metadata
  volumes:
    - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
  ports:
    - "5432:5432"
```

* Minimal schema for metadata:

```sql
CREATE TABLE IF NOT EXISTS documents (
  document_id SERIAL PRIMARY KEY,
  filename TEXT NOT NULL,
  upload_time TIMESTAMP DEFAULT NOW(),
  chunk_count INTEGER,
  embedding_model TEXT,
  minio_path TEXT NOT NULL
);
```

---

### 4.2 MinIO

* Use Docker service:

```yaml
minio:
  image: minio/minio
  command: server /data --console-address ":9001"
  environment:
    MINIO_ROOT_USER: minioadmin
    MINIO_ROOT_PASSWORD: minioadmin
  ports:
    - "9000:9000"
    - "9001:9001"
  volumes:
    - minio_data:/data
```

* The backend should create/use a bucket (e.g., `documents`) for file uploads.

---

### 4.3 Backend Environment Variables

Add to `docker-compose.yml`:

```yaml
POSTGRES_URI: postgresql://ragops:ragops@postgres:5432/metadata
MINIO_ENDPOINT: http://minio:9000
MINIO_ACCESS_KEY: minioadmin
MINIO_SECRET_KEY: minioadmin
MINIO_BUCKET: documents
```

---

### 4.4 Backend Functionality

1. **Upload document (text or PDF)**:

   * Store raw file in MinIO.
   * Record metadata in PostgreSQL: filename, storage path, chunk count, embedding model.

2. **Retrieve metadata** by document ID via a GET endpoint.

3. **Ensure existing ingestion endpoints** (`/ingest-pdf`, `/ingest-pdf-batch`) integrate with the new storage and metadata services.

---

### 4.5 Testing

* Automated tests exist in `tests/test_metadata.py`.
* Your implementation **must pass all tests**.
* Tests cover:

  * Health check of the metadata service.
  * Single document upload + metadata retrieval.
  * PDF ingestion (single and batch) integration with storage and metadata.

---

## 5. Evaluation Criteria

| Criterion                                     | Weight |
| --------------------------------------------- | ------ |
| Functional correctness                        | 50%    |
| Integration with existing RAGOps architecture | 20%    |
| Dockerization & environment configuration     | 20%    |
| Test passing (`test_metadata.py`)             | 10%    |

**Bonus (+10%)**: Integrate Prometheus metrics for upload events or bucket size.

---

## 6. Submission Guidelines

* Submit the **entire repository** with your additions and modifications.
* Do not delete or rename any original files outside your modifications.
* Do not modify `tests/test_metadata.py`.
* Your work will be **evaluated automatically** using the provided tests and Docker setup.

