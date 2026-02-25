from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import pandas as pd
from sqlalchemy import create_engine

from scripts.generate_data import generate_sales
from scripts.upload_to_minio import (
    upload_file_to_minio,
    get_minio_client,
)
from scripts.process_and_load import (
    download_from_minio,
    validate_sales_file,
    load_sales_to_postgres,
)


# Configuration
RAW_PATH = "/tmp/sales_raw.csv"
RAW_LOCAL = "/scripts/data/sales_raw.csv"
VALIDATED_PATH = "/tmp/sales_validated.csv"
LOCAL_VALIDATED_PATH = "/scripts/data/sales_validated.csv"
OBJECT_NAME = "sales.csv"
BUCKET = os.getenv("MINIO_BUCKET")

default_args = {
    "owner": "data-engineering",
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}


# DAG Definition
with DAG(
    dag_id="sales_etl_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["sales", "etl"],
) as dag:


    #Generate Task
    def generate_task():
        generate_sales(
            output_path=RAW_PATH,
            random_seed=42,
        )

    generate = PythonOperator(
        task_id="generate_sales",
        python_callable=generate_task,
    )


    # Upload Task
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

    # Download Task
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


    # Validation Task
    def validate_task():
        validate_sales_file(
            input_path=RAW_PATH,
            output_path=VALIDATED_PATH,
            max_invalid_ratio=0.05
        )

    validate = PythonOperator(
        task_id="validate_sales_data",
        python_callable=validate_task,
    )

 
    #Load Task
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

        load_sales_to_postgres(df, engine)
        engine.dispose()

    load = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_task,
    )


    # Pipeline Order
    generate >> upload >> download >> validate >> load