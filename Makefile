.PHONY: setup all test dbt-docs mlflow airflow clean-airflow
setup:            ## python env + dependencies
	uv venv --python 3.12 .venv && . .venv/bin/activate && uv pip install -r requirements.txt
all:              ## one command: raw data check -> dbt -> Feast -> train -> drift monitor
	. .venv/bin/activate && dvc repro
test:             ## dbt tests + pandas-vs-SQL parity tests
	. .venv/bin/activate && cd dbt_athletes && dbt test --profiles-dir . && cd .. && python -m pytest -q
mlflow:           ## browse runs and lineage at http://localhost:5000
	. .venv/bin/activate && mlflow ui --backend-store-uri sqlite:///mlflow.db
airflow:          ## local Airflow at http://localhost:8080
	docker compose -f airflow/docker-compose.yml up --build
