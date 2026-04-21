import os
from minio import Minio
from minio.error import S3Error
import urllib.parse

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "documents")

# Strip scheme for the Minio client (it expects host:port)
_parsed = urllib.parse.urlparse(MINIO_ENDPOINT)
_host = _parsed.netloc or _parsed.path  # e.g. "minio:9000"
_secure = _parsed.scheme == "https"

minio_client = Minio(
    _host,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=_secure,
)


def ensure_bucket() -> None:
    """Create the bucket if it does not already exist."""
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)


def upload_file(object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """
    Upload bytes to MinIO and return the s3:// URI.
    Ensures the bucket exists before uploading.
    """
    ensure_bucket()
    import io
    minio_client.put_object(
        MINIO_BUCKET,
        object_name,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return f"s3://{MINIO_BUCKET}/{object_name}"