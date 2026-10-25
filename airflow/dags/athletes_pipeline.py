"""One DAG, five tasks: prepare -> dbt_run -> feast_materialize -> train -> monitor.

Each task runs exactly the command of the matching stage in dvc.yaml, so Airflow (scheduling, retries, UI)
and DVC (reproducibility, caching) describe the same pipeline. The project dependencies live in their own
virtualenv so they cannot conflict with Airflow's pinned packages.
"""
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

ROOT = os.environ.get("PIPELINE_ROOT", "/opt/airflow/project")
VENV = os.environ.get("PIPELINE_VENV", "/home/airflow/pipeline-venv")
RUN = f"cd {ROOT} && export PATH={VENV}/bin:$PATH && "

default_args = {"owner": "jiawei", "retries": 1, "retry_delay": timedelta(minutes=2)}

with DAG(
    dag_id="athletes_mlops_pipeline",
    description="raw CSV -> dbt -> Feast -> train (MLflow lineage) -> drift monitor",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule=None,             # trigger manually; switch to "@weekly" for a refresh cadence
    catchup=False,
    max_active_runs=1,
    tags=["mlops", "dbt", "feast", "mlflow", "evidently"],
) as dag:
    prepare = BashOperator(task_id="prepare", bash_command=RUN + "python src/prepare_check.py")
    dbt_run = BashOperator(task_id="dbt_run",
                           bash_command=RUN + "mkdir -p data/marts && cd dbt_athletes && dbt build --profiles-dir .")
    feast_materialize = BashOperator(task_id="feast_materialize", bash_command=RUN + "python src/feast_materialize.py")
    train = BashOperator(task_id="train", bash_command=RUN + "python src/train.py")
    monitor = BashOperator(task_id="monitor", bash_command=RUN + "python src/monitor.py")

    prepare >> dbt_run >> feast_materialize >> train >> monitor
