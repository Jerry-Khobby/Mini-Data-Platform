"""
ETL Pipeline Monitoring Module

This module records operational metrics for each ETL pipeline run
into the `etl_monitoring` table in PostgreSQL.

The goal is to monitor the health, quality, and performance of the
data pipeline over time.

Metrics captured per pipeline run:

1. total_rows
   Total number of records ingested by the pipeline.

2. valid_rows
   Number of records that passed validation rules.

3. invalid_rows
   Number of records rejected due to schema, type,
   domain, or business rule violations.

4. invalid_ratio
   Ratio of invalid records to total records.
   Used to detect data quality issues or upstream data problems.

5. load_duration_seconds
   Time taken to load validated records into PostgreSQL.
   Used to monitor pipeline performance and detect slowdowns.

6. status
   Final pipeline status (e.g., SUCCESS, FAILED).

7. run_timestamp
   Timestamp of when the pipeline run was recorded.

These metrics enable:

• Monitoring pipeline health
• Detecting data quality issues
• Tracking ETL performance
• Auditing historical pipeline runs
• Supporting observability dashboards
"""


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