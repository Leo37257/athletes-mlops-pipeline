FROM apache/airflow:2.10.5-python3.12
# Project dependencies go in a separate virtualenv: Airflow keeps its own pinned packages untouched.
COPY requirements.txt /tmp/requirements.txt
RUN python -m venv /home/airflow/pipeline-venv \
 && /home/airflow/pipeline-venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt
