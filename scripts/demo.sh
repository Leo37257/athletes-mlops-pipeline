#!/usr/bin/env bash
# Run the whole pipeline on the 5,300-row sample, in a throw-away workspace (.demo/) so the real data,
# DVC state and MLflow history are never touched. No dataset needed.
#   make demo
set -euo pipefail
cd "$(dirname "$0")/.."
SRC="$PWD"; DEMO="$SRC/.demo"
mkdir -p "$DEMO/data/raw" "$DEMO/data/marts" "$DEMO/feature_repo/data" "$DEMO/reports"
rsync -a --delete --exclude target --exclude logs --exclude '__pycache__' "$SRC/src/" "$DEMO/src/"
rsync -a --delete --exclude target --exclude logs "$SRC/dbt_athletes/" "$DEMO/dbt_athletes/"
rsync -a --exclude 'data/*.db' --exclude '__pycache__' "$SRC/feature_repo/" "$DEMO/feature_repo/"
cp "$SRC/params.yaml" "$DEMO/params.yaml"
cp "$SRC/data/sample/athletes_sample.csv" "$DEMO/data/raw/athletes.csv"
cd "$DEMO"
export PYTHONPATH="$DEMO"
# the regression guard: dbt must reproduce the pandas reference counts on the sample too
read V1 V2 < <(python - <<'PY'
import pandas as pd
from src.reference_clean import build_v1, build_v2
raw = pd.read_csv("data/raw/athletes.csv")
print(len(build_v1(raw)), len(build_v2(raw)))
PY
)
echo "== dbt build (expected v1=$V1 v2=$V2 rows)"
(cd dbt_athletes && dbt build --profiles-dir . --vars "{expected_v1_rows: $V1, expected_v2_rows: $V2}" | grep -E "Done\.|WARN|ERROR" )
echo "== Feast"; python src/feast_materialize.py 2>&1 | grep -E "feature views"
echo "== train"; python src/train.py 2>&1 | grep -E '"(rmse|r2|baseline_rmse|n_train|n_test)"'
echo "== monitor"; python src/monitor.py 2>&1 | grep -E "^distribution|^max weight"
echo "Demo outputs: $DEMO/metrics.json, $DEMO/reports/drift_v1_v2.html (MLflow db: $DEMO/mlflow.db)"
