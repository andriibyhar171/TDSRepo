from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts')))
from data_generator import load_data_to_dwh

PROJECT_ROOT = "/mnt/d/Files/NULP/TDS/4/modern-data-stack-furniture"
DBT_PROJECT_DIR = os.path.join(PROJECT_ROOT, "furniture_dbt")
DBT_PROFILES_DIR = os.path.join(PROJECT_ROOT, "furniture_dbt")

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'furniture_elt_pipeline',
    default_args=default_args,
    description='Конвеєр ELT для магазину меблів',
    schedule='@daily', # Змінено з schedule_interval на schedule
    catchup=False
) as dag:
    # Task 1: Видобуток та завантаження "сирих" даних
    extract_load_task = PythonOperator(
        task_id='extract_and_load_raw_data',
        python_callable=load_data_to_dwh
    )

    # Task 2: Трансформація даних через dbt
    dbt_run_task = BashOperator(
        task_id='dbt_run_transformations',
        bash_command=f'cd {DBT_PROJECT_DIR} && dbt run --project-dir {DBT_PROJECT_DIR} --profiles-dir {DBT_PROFILES_DIR}'
    )

    # Task 3: Тестування якості даних через dbt
    dbt_test_task = BashOperator(
        task_id='dbt_test_data_quality',
        bash_command=f'cd {DBT_PROJECT_DIR} && dbt test --project-dir {DBT_PROJECT_DIR} --profiles-dir {DBT_PROFILES_DIR}'
    )

    # Налаштування залежностей (послідовність виконання тасків)
    extract_load_task >> dbt_run_task >> dbt_test_task