"""Drift monitoring across schema versions: baseline = v1 (before cleaning), current = v2 (after cleaning).

Two kinds of change are reported: (1) schema drift, read from the dbt model schema_diff_v1_v2, and
(2) distribution drift on the columns both versions share (Evidently), plus how null rates and extremes moved.
"""
import json
import os
import re
import sys
from pathlib import Path

import duckdb
import mlflow
import pandas as pd
import yaml
from evidently import DataDefinition, Dataset, Report
from evidently.presets import DataDriftPreset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
NUM = ["age", "height", "weight", "candj", "snatch", "deadlift", "backsq", "total_lift"]
CAT = ["gender", "region"]


def main() -> None:
    cfg = yaml.safe_load((ROOT / "params.yaml").read_text())["monitor"]
    ref = pd.read_parquet(ROOT / "data/marts/athletes_v1.parquet")[NUM + CAT]
    cur = pd.read_parquet(ROOT / "data/marts/athletes_v2.parquet")[NUM + CAT]
    dd = DataDefinition(numerical_columns=NUM, categorical_columns=CAT)

    report = Report([DataDriftPreset(drift_share=cfg["drift_share_threshold"])])
    snap = report.run(Dataset.from_pandas(cur, data_definition=dd), Dataset.from_pandas(ref, data_definition=dd))
    (ROOT / "reports").mkdir(exist_ok=True)
    snap.save_html(str(ROOT / "reports/drift_v1_v2.html"))

    columns, counted = {}, {}
    for m in snap.dict()["metrics"]:
        name, val = m["metric_name"], m["value"]
        if name.startswith("DriftedColumnsCount"):
            counted = val
        elif name.startswith("ValueDrift"):
            col = re.search(r"column=([^,]+)", name).group(1)
            thr = float(re.search(r"threshold=([0-9.]+)", name).group(1))
            method = re.search(r"method=([^,]+),", name).group(1)
            columns[col] = {"distance": round(float(val), 4), "threshold": thr, "method": method, "drifted": float(val) > thr}

    con = duckdb.connect(str(ROOT / "data/athletes.duckdb"), read_only=True)
    schema = con.execute("select column_name, change from schema_diff_v1_v2 order by change, column_name").fetchall()
    schema_summary = {}
    for col, change in schema:
        schema_summary.setdefault(change, []).append(col)

    quality = {c: {"null_rate_v1": round(float(ref[c].isna().mean()), 4), "null_rate_v2": round(float(cur[c].isna().mean()), 4),
                   **({"max_v1": float(ref[c].max()), "max_v2": float(cur[c].max())} if c in NUM else {})}
               for c in NUM + CAT}

    n_drift = sum(v["drifted"] for v in columns.values())
    summary = {
        "baseline": {"version": "v1", "rows": len(ref)}, "current": {"version": "v2", "rows": len(cur)},
        "schema": {k: v for k, v in schema_summary.items()},
        "schema_changed": bool(schema_summary.get("added in v2") or schema_summary.get("dropped in v2")),
        "distribution": {"columns_checked": len(columns), "columns_drifted": n_drift,
                         "share_drifted": n_drift / max(len(columns), 1),
                         "dataset_drift": n_drift / max(len(columns), 1) > cfg["drift_share_threshold"],
                         "evidently_count": counted, "columns": columns},
        "data_quality": quality,
    }
    (ROOT / "reports/drift_summary.json").write_text(json.dumps(summary, indent=2))

    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", f"sqlite:///{ROOT / 'mlflow.db'}"))
    mlflow.set_experiment("athletes_monitoring")
    with mlflow.start_run(run_name="drift_v1_vs_v2"):
        mlflow.log_metrics({"columns_drifted": n_drift, "share_drifted": summary["distribution"]["share_drifted"],
                            "columns_added": len(schema_summary.get("added in v2", [])),
                            "columns_dropped": len(schema_summary.get("dropped in v2", [])),
                            "max_weight_v1": quality["weight"]["max_v1"], "max_weight_v2": quality["weight"]["max_v2"]})
        mlflow.log_artifact(str(ROOT / "reports/drift_v1_v2.html"))
        mlflow.log_artifact(str(ROOT / "reports/drift_summary.json"))

    print(json.dumps({k: summary[k] for k in ("schema_changed", "schema")}, indent=2))
    print("distribution:", {k: v for k, v in summary["distribution"].items() if k != "columns"})
    print("max weight v1 -> v2:", quality["weight"]["max_v1"], "->", quality["weight"]["max_v2"],
          "| null rate candj v1/v2:", quality["candj"]["null_rate_v1"], quality["candj"]["null_rate_v2"])


if __name__ == "__main__":
    main()
