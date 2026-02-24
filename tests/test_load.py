import pandas as pd
from sqlalchemy import create_engine
from scripts.process_and_load import load_sales_to_postgres
from sqlalchemy import text


def test_load_is_idempotent(tmp_path):
    engine = create_engine("sqlite:///:memory:")

    # create test table
    with engine.begin() as conn:
        conn.execute("""
        CREATE TABLE sales (
            order_id TEXT PRIMARY KEY,
            product TEXT,
            category TEXT,
            sale_amount REAL,
            sale_date TEXT,
            region TEXT
        )
        """)

    df = pd.DataFrame({
        "order_id": ["1"],
        "product": ["Laptop"],
        "category": ["Electronics"],
        "sale_amount": [100],
        "sale_date": ["2024-01-01"],
        "region": ["North"]
    })

    load_sales_to_postgres(df, engine)
    load_sales_to_postgres(df, engine)

    with engine.connect() as conn:
        result = conn.execute("SELECT COUNT(*) FROM sales")
        count = result.fetchone()[0]

    assert count == 1