import os
import logging
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv

# Setup
load_dotenv()

# Console logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Environment variables
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
LOCAL_FILE_PATH = "data/sales.csv"
OBJECT_NAME = "sales.csv"

# Validate environment variables
for var_name, value in {
    "MINIO_ENDPOINT": MINIO_ENDPOINT,
    "MINIO_ACCESS_KEY": MINIO_ACCESS_KEY,
    "MINIO_SECRET_KEY": MINIO_SECRET_KEY,
    "MINIO_BUCKET": MINIO_BUCKET,
}.items():
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {var_name}")


# MinIO client
client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False  # Set True if using HTTPS
)

# Ensure bucket exists
if not client.bucket_exists(MINIO_BUCKET):
    logger.info(f"Bucket '{MINIO_BUCKET}' does not exist. Creating it...")
    client.make_bucket(MINIO_BUCKET)
else:
    logger.info(f"Bucket '{MINIO_BUCKET}' already exists.")


# Upload file
try:
    client.fput_object(
        bucket_name=MINIO_BUCKET,
        object_name=OBJECT_NAME,
        file_path=LOCAL_FILE_PATH
    )
    logger.info(f"Successfully uploaded '{LOCAL_FILE_PATH}' → '{MINIO_BUCKET}/{OBJECT_NAME}'")
except FileNotFoundError:
    logger.error(f"Local file '{LOCAL_FILE_PATH}' not found.")
except S3Error as e:
    logger.error(f"Failed to upload '{LOCAL_FILE_PATH}' to MinIO: {e}")