import pytest
from sqlalchemy import create_engine, text
import os

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT', 5432)}/{os.getenv('POSTGRES_DB')}"
    )
    # Create tables if not exist
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS etl_monitoring (
                run_id SERIAL PRIMARY KEY,
                run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_rows INT,
                valid_rows INT,
                invalid_rows INT,
                invalid_ratio FLOAT,
                load_duration_seconds FLOAT,
                status VARCHAR(20)
            )
        """))
    yield engine
    engine.dispose()