CREATE TABLE IF NOT EXISTS documents (
  document_id SERIAL PRIMARY KEY,
  filename TEXT NOT NULL,
  upload_time TIMESTAMP DEFAULT NOW(),
  chunk_count INTEGER,
  embedding_model TEXT,
  minio_path TEXT NOT NULL
);