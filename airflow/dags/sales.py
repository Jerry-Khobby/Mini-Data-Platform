from airflow import DAG 
from airflow.operators.python import PythonOperator 
from datetime import datetime,timedelta 

from scripts.upload_to_minio import get_minio_client,upload_file_to_minio


from scripts.generate_data import generate_sales
from process_and_load import load_sales_to_postgres,get_minio_client,ensure_bucket_exists




#So first, I will generate the dummy data ,
#I will move them to the minio 
# Pick the data from the minio , process it to postgres 
# Build a dashboard around it 
