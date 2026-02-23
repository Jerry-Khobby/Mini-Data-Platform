import os
import logging
from minio import Minio
from minio.error import S3Error
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

# Config
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
OBJECT_NAME = "sales.csv"

PG_USER = os.getenv("POSTGRES_USER")
PG_PASS = os.getenv("POSTGRES_PASSWORD")
PG_DB = os.getenv("POSTGRES_DB")
PG_HOST = os.getenv("POSTGRES_HOST")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")


def validate_env():
    """Ensure all required environment variables are set."""
    required_vars = {
        "MINIO_ENDPOINT": MINIO_ENDPOINT,
        "MINIO_ACCESS_KEY": MINIO_ACCESS_KEY,
        "MINIO_SECRET_KEY": MINIO_SECRET_KEY,
        "MINIO_BUCKET": MINIO_BUCKET,
        "POSTGRES_USER": PG_USER,
        "POSTGRES_PASSWORD": PG_PASS,
        "POSTGRES_DB": PG_DB,
        "POSTGRES_HOST": PG_HOST
    }
    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        logger.error(f"Missing environment variables: {missing_vars}")
        raise EnvironmentError(f"Missing environment variables: {missing_vars}")


def process_sales_from_minio(minio_client, object_name: str, local_file: str = "/tmp/sales.csv") -> pd.DataFrame:
    """Download CSV from MinIO, validate schema, clean and return a DataFrame."""
    try:
        minio_client.fget_object(MINIO_BUCKET, object_name, local_file)
        logger.info(f"Downloaded {object_name} from MinIO → {local_file}")
    except S3Error as e:
        logger.exception("Error downloading file from MinIO")
        raise
    except FileNotFoundError:
        logger.error(f"Local path {local_file} not found")
        raise

    try:
        df = pd.read_csv(local_file)
    except Exception as e:
        logger.exception("Failed to read CSV")
        raise

    expected_columns = ["order_id", "product", "category", "sale_amount", "sale_date", "region"]
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"CSV is missing required columns: {missing_columns}")

    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df["sale_amount"] = pd.to_numeric(df["sale_amount"], errors="coerce")
    critical_cols = ["order_id", "product", "sale_amount", "sale_date"]
    missing_values = df[critical_cols].isnull().sum()
    if missing_values.any():
        logger.warning(f"Rows with missing critical values will be dropped:\n{missing_values}")
    df.dropna(subset=critical_cols, inplace=True)

    invalid_amounts = df[df["sale_amount"] <= 0]
    if not invalid_amounts.empty:
        logger.warning(f"Dropping {len(invalid_amounts)} rows with invalid sale_amount <= 0")
        df = df[df["sale_amount"] > 0]

    duplicates = df.duplicated(subset=["order_id"])
    if duplicates.any():
        logger.warning(f"Dropping {duplicates.sum()} duplicate rows based on order_id")
        df = df[~duplicates]

    logger.info(f"After validation, {len(df)} rows ready for loading")
    return df


def load_sales_to_postgres(df: pd.DataFrame, engine):
    """Load a validated DataFrame into PostgreSQL using raw SQL INSERT."""
    try:
        with engine.begin() as conn:
            insert_query = text("""
                INSERT INTO sales (order_id, product, category, sale_amount, sale_date, region)
                VALUES (:order_id, :product, :category, :sale_amount, :sale_date, :region)
                ON CONFLICT (order_id) DO NOTHING
            """)
            
            records = df.to_dict('records')
            conn.execute(insert_query, records)
            
        logger.info(f"Successfully loaded {len(df)} rows into PostgreSQL table 'sales'")
    except Exception as e:
        logger.exception("Failed to load data into PostgreSQL")
        raise


def verify_load(engine, limit=5):
    """Verify data was loaded correctly."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM sales LIMIT {limit}"))
            rows = result.fetchall()
            logger.info(f"Verified {len(rows)} sample rows from sales table:")
            for row in rows:
                logger.info(f"  {row}")
    except Exception as e:
        logger.exception("Failed to verify data load")


if __name__ == "__main__":
    validate_env()

    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

    df_sales = process_sales_from_minio(minio_client, OBJECT_NAME)

    pg_engine = create_engine(
        f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    )

    load_sales_to_postgres(df_sales, pg_engine)
    verify_load(pg_engine)
    
    pg_engine.dispose()
