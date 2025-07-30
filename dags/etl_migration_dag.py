from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'deepu',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'etl_migration_pipeline_v2',
    default_args=default_args,
    description='ETL pipeline for RDS to On-Prem DB',
    schedule_interval='0 12 * * 5',  # Every Friday at 12 PM
    catchup=False,
)

run_etl = BashOperator(
    task_id='run_etl_migration',
    bash_command='python /opt/airflow/migrate.py',
    dag=dag,
)
