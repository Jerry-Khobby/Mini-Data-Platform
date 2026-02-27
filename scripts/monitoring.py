import logging
from sqlalchemy import text
from datetime import datetime

logger = logging.getLogger(__name__)


def record_pipeline_run(
    engine,
    total_rows: int,
    valid_rows: int,
    invalid_rows: int,
    invalid_ratio: float,
    load_duration: float,
    status: str,
):
    """
    Persist ETL monitoring metrics into PostgreSQL.
    """

    with engine.begin() as conn:
        insert_query = text("""
            INSERT INTO etl_monitoring (
                run_timestamp,
                total_rows,
                valid_rows,
                invalid_rows,
                invalid_ratio,
                load_duration_seconds,
                status
            )
            VALUES (
                :run_timestamp,
                :total_rows,
                :valid_rows,
                :invalid_rows,
                :invalid_ratio,
                :load_duration_seconds,
                :status
            )
        """)

        conn.execute(insert_query, {
            "run_timestamp": datetime.utcnow(),
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "invalid_ratio": invalid_ratio,
            "load_duration_seconds": load_duration,
            "status": status,
        })

    logger.info("ETL monitoring record inserted successfully.")