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


def validate_sales_file(
    input_path: str,
    output_path: str,
    max_invalid_ratio: float | None = None,
):
    df = pd.read_csv(input_path)

    # Fail only if file truly has no rows AND no columns
    if df.empty and len(df.columns) == 0:
        raise ValueError("Dataset is empty. Failing pipeline.")

    total_rows = len(df)
    logger.info(f"Validation started | rows={total_rows}")

    # Schema Validation (allow extra columns)
    missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Enforce column selection & order
    df = df[EXPECTED_COLUMNS].copy()

    # Type Enforcement
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df["sale_amount"] = pd.to_numeric(df["sale_amount"], errors="coerce")

    # Domain & Business Rules (deterministic only)
    validation_mask = (
        df["order_id"].notna()
        & df["sale_amount"].notna()
        & (df["sale_amount"] > 0)
        & df["sale_date"].notna()
        & df["product"].isin(VALID_PRODUCTS)
        & df["category"].isin(VALID_CATEGORIES)
        & df["region"].isin(VALID_REGIONS)
    )

    valid_df = df[validation_mask].copy()
    invalid_df = df[~validation_mask].copy()

    # Remove duplicates (idempotent logic)
    before_dedup = len(valid_df)
    valid_df = valid_df.drop_duplicates(subset=["order_id"], keep="first")
    duplicates_removed = before_dedup - len(valid_df)

    invalid_count = len(invalid_df) + duplicates_removed
    invalid_ratio = invalid_count / total_rows if total_rows > 0 else 0

    logger.info(f"Valid rows={len(valid_df)}")
    logger.info(f"Invalid rows={invalid_count}")
    logger.info(f"Invalid ratio={invalid_ratio:.2%}")

    if max_invalid_ratio is not None and invalid_ratio > max_invalid_ratio:
        raise ValueError(
            f"Validation failed. Invalid ratio {invalid_ratio:.2%} "
            f"exceeds threshold {max_invalid_ratio:.2%}"
        )

    # Save clean deterministic output
    valid_df.to_csv(output_path, index=False)
    logger.info(f"Validated dataset saved → {output_path}")
    
    return {
        "total_rows":total_rows,
        "valid_rows": len(valid_df),
        "invalid_rows": invalid_count,
        "invalid_ratio": invalid_ratio
    }



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