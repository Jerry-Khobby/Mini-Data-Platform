import os
import logging
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def get_minio_client(
    endpoint: str = None,
    access_key: str = None,
    secret_key: str = None,
    secure: bool = False
) -> Minio:
    """Create and return a MinIO client."""
    endpoint   = endpoint   or os.getenv("MINIO_ENDPOINT")
    access_key = access_key or os.getenv("MINIO_ROOT_USER")
    secret_key = secret_key or os.getenv("MINIO_ROOT_PASSWORD")

    if not all([endpoint, access_key, secret_key]):
        raise EnvironmentError("Missing MinIO connection environment variables.")

    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


def ensure_bucket_exists(client: Minio, bucket: str) -> None:
    """Create the bucket if it doesn't already exist."""
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        logger.info(f"Bucket '{bucket}' created.")
    else:
        logger.info(f"Bucket '{bucket}' already exists.")


def upload_file_to_minio(
    local_path: str,
    object_name: str,
    bucket: str = None,
    client: Minio = None
) -> None:
    """
    Upload a local file to MinIO.

    Args:
        local_path:  Path to the local file e.g. 'data/sales.csv'
        object_name: Name to store it as in MinIO e.g. 'sales.csv'
        bucket:      Target bucket (falls back to MINIO_BUCKET env var)
        client:      Existing Minio client (creates one if not provided)
    """
    bucket = bucket or os.getenv("MINIO_BUCKET")
    if not bucket:
        raise EnvironmentError("Missing MINIO_BUCKET environment variable.")

    client = client or get_minio_client()
    ensure_bucket_exists(client, bucket)

    try:
        client.fput_object(bucket_name=bucket, object_name=object_name, file_path=local_path)
        logger.info(f"Uploaded '{local_path}' → '{bucket}/{object_name}'")
    except FileNotFoundError:
        logger.error(f"Local file '{local_path}' not found.")
        raise
    except S3Error as e:
        logger.error(f"MinIO upload failed: {e}")
        raise
      
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    try:
        LOCAL_FILE = os.getenv("LOCAL_DATA_PATH", "data/sales.csv")
        OBJECT_NAME = os.path.basename(LOCAL_FILE)

        logger.info("Starting MinIO upload process...")

        upload_file_to_minio(
            local_path=LOCAL_FILE,
            object_name=OBJECT_NAME
        )

        logger.info("Upload completed successfully.")

    except Exception as e:
        logger.exception("Upload process failed.")
        raise