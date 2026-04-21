import os

class Settings:
    APP_NAME: str = "RAGOPS API"
    APP_VERSION: str = "2.0.0"

    MEILI_URL: str = os.getenv("MEILI_URL", "")
    MEILI_KEY: str = os.getenv("MEILI_KEY", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    PROXY_URL: str = os.getenv("PROXY_URL", "")
    PROXY_KEY: str = os.getenv("PROXY_KEY", "")

    MEILI_INDEX: str = os.getenv("MEILI_INDEX", "documents")
    CHUNKS_INDEX: str = "chunks"
    EMBED_DIM: int = int(os.getenv("EMBED_DIM", "384"))

    # LLM and Embeddings
    LITELLM_MODEL: str = os.environ["LITELLM_MODEL"]
    LITELLM_URL: str = os.getenv("PROXY_URL", "http://litellm:4000") + "/v1"
    EMBEDDING_MODEL_NAME: str = os.environ["EMBEDDING_MODEL_NAME"]
    TEI_EMBEDDINGS_URL: str = os.getenv("PROXY_URL", "http://litellm:4000") + "/v1"
    TEI_URL: str = os.getenv("TEI_URL", "http://tei-embeddings:80")

    # PostgreSQL
    POSTGRES_URI: str = os.getenv("POSTGRES_URI", "postgresql://ragops:ragops@postgres:5432/metadata")

    # MinIO
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "documents")

settings = Settings()
