from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import pandas as pd
import time
from sqlalchemy import create_engine

from scripts.generate_data import generate_sales
from scripts.upload_to_minio import upload_file_to_minio, get_minio_client
from scripts.process_and_load import (
    download_from_minio,
    validate_sales_file,
    load_sales_to_postgres,
)
from scripts.monitoring import record_pipeline_run


RAW_PATH = "/tmp/sales_raw.csv"
VALIDATED_PATH = "/tmp/sales_validated.csv"
OBJECT_NAME = "sales.csv"
BUCKET = os.getenv("MINIO_BUCKET")


default_args = {
    "owner": "data-engineering",
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}


with DAG(
    dag_id="sales_etl_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["sales", "etl"],
) as dag:


    # Generate
    def generate_task():
        generate_sales(output_path=RAW_PATH, random_seed=42)

    generate = PythonOperator(
        task_id="generate_sales",
        python_callable=generate_task,
    )


    #Upload
    def upload_task():
        client = get_minio_client()
        upload_file_to_minio(
            local_path=RAW_PATH,
            object_name=OBJECT_NAME,
            client=client,
        )

    upload = PythonOperator(
        task_id="upload_to_minio",
        python_callable=upload_task,
    )

    # Download
    def download_task():
        client = get_minio_client()
        download_from_minio(
            client=client,
            bucket=BUCKET,
            object_name=OBJECT_NAME,
            local_path=RAW_PATH,
        )

    download = PythonOperator(
        task_id="download_from_minio",
        python_callable=download_task,
    )


    #  Validate (returns metrics → XCom)
    def validate_task():
        return validate_sales_file(
            input_path=RAW_PATH,
            output_path=VALIDATED_PATH,
            max_invalid_ratio=0.05,
        )

    validate = PythonOperator(
        task_id="validate_sales_data",
        python_callable=validate_task,
    )

    # Load (returns duration → XCom)
    def load_task():
        df = pd.read_csv(VALIDATED_PATH)

        engine = create_engine(
            f"postgresql+psycopg2://"
            f"{os.getenv('POSTGRES_USER')}:"
            f"{os.getenv('POSTGRES_PASSWORD')}@"
            f"{os.getenv('POSTGRES_HOST')}:"
            f"{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB')}"
        )

        start = time.time()
        load_sales_to_postgres(df, engine)
        duration = time.time() - start

        engine.dispose()

        return {"load_duration": duration}

    load = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_task,
    )




    def monitor_task(ti):
        validation_metrics = ti.xcom_pull(
            task_ids="validate_sales_data"
        )

        load_metrics = ti.xcom_pull(
            task_ids="load_to_postgres"
        )

        engine = create_engine(
            f"postgresql+psycopg2://"
            f"{os.getenv('POSTGRES_USER')}:"
            f"{os.getenv('POSTGRES_PASSWORD')}@"
            f"{os.getenv('POSTGRES_HOST')}:"
            f"{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB')}"
        )

        record_pipeline_run(
            engine=engine,
            total_rows=validation_metrics["total_rows"],
            valid_rows=validation_metrics["valid_rows"],
            invalid_rows=validation_metrics["invalid_rows"],
            invalid_ratio=validation_metrics["invalid_ratio"],
            load_duration=load_metrics["load_duration"],
            status="SUCCESS",
        )

        engine.dispose()

    monitor = PythonOperator(
        task_id="record_metrics",
        python_callable=monitor_task,
    )


    generate >> upload >> download >> validate >> load >> monitor