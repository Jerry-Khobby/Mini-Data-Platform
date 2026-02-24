import os
import logging
import pandas as pd
from sqlalchemy import text

logger = logging.getLogger(__name__)

EXPECTED_COLUMNS = [
    "order_id", "product", "category",
    "sale_amount", "sale_date", "region"
]


VALID_PRODUCTS = {"Laptop", "Phone", "Tablet", "Monitor", "Keyboard", "Mouse"}
VALID_CATEGORIES = {"Electronics", "Accessories", "Peripherals"}
VALID_REGIONS  = {"North", "South", "East", "West", "Central"}
# Download
def download_from_minio(client, bucket: str, object_name: str, local_path: str):
    client.fget_object(bucket, object_name, local_path)
    logger.info(f"Downloaded {object_name} → {local_path}")


#  Validate
def validate_sales_file(input_path: str, output_path: str):
    df = pd.read_csv(input_path)
    total_rows = len(df)
    
    if total_rows ==0:
      raise ValueError("Dataset is empty. Failing pipeline")
    logger.info(f"Starting validation:{total_rows} rows")

    missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    extra_cols =[c for c in df.columns if c not in EXPECTED_COLUMNS]
    if missing_cols:
        raise ValueError(f"Missing columns: {missing_cols}")
    if extra_cols:
      logger.warning(f"Unexpected extra columns:{extra_cols}")

    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df["sale_amount"] = pd.to_numeric(df["sale_amount"], errors="coerce")

    df.dropna(subset=["order_id", "sale_amount", "sale_date"], inplace=True)
    df = df[df["sale_amount"] > 0]
    
    duplicate_count = df.duplicated(subset=["order_id"]).sum()
    if duplicate_count>0: 
        logger.warning(f"Dropping {duplicate_count} duplicate rows based on 'order_id'")
        df = df.drop_duplicates(subset=["order_id"])

    df.to_csv(output_path, index=False)
    logger.info(f"Validated file saved → {output_path}")



#  Load
def load_sales_to_postgres(df: pd.DataFrame, engine):
    with engine.begin() as conn:
        insert_query = text("""
            INSERT INTO sales (order_id, product, category, sale_amount, sale_date, region)
            VALUES (:order_id, :product, :category, :sale_amount, :sale_date, :region)
            ON CONFLICT (order_id) DO NOTHING
        """)
        conn.execute(insert_query, df.to_dict("records"))

    logger.info(f"Loaded {len(df)} rows into sales table")