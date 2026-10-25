"""Train total_lift regression from the Feast feature store and record full lineage in MLflow."""
import json
import os
import sys
from pathlib import Path

import joblib
import mlflow
import numpy as np
import pandas as pd
import yaml
from feast import FeatureStore
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import lineage  # noqa: E402

NUMERIC = ["age", "height_m", "weight_kg", "bmi"]
CATEGORICAL = ["age_group", "gender", "region", "howlong", "eat", "background", "experience", "schedule"]


def load_training_frame(as_of: str) -> pd.DataFrame:
    store = FeatureStore(repo_path=str(ROOT / "feature_repo"))
    labels = pd.read_parquet(ROOT / "data/marts/athletes_v2_features.parquet", columns=["athlete_id", "total_lift"])
    entity_df = labels.assign(event_timestamp=pd.Timestamp(as_of, tz="UTC"))
    feats = store.get_historical_features(entity_df=entity_df,
                                          features=store.get_feature_service("total_lift_v2")).to_df()
    return feats


def main() -> None:
    params = yaml.safe_load((ROOT / "params.yaml").read_text())["train"]
    df = load_training_frame(params["training_as_of"])
    X, y = df[NUMERIC + CATEGORICAL], df["total_lift"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=params["test_size"], random_state=params["random_state"])

    pre = ColumnTransformer([
        ("num", "passthrough", NUMERIC),
        ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1,
                               encoded_missing_value=-1), CATEGORICAL),
    ])
    mask = [False] * len(NUMERIC) + [True] * len(CATEGORICAL)
    model = Pipeline([("pre", pre), ("gbm", HistGradientBoostingRegressor(
        max_iter=params["model"]["max_iter"], learning_rate=params["model"]["learning_rate"],
        max_leaf_nodes=params["model"]["max_leaf_nodes"], categorical_features=mask,
        random_state=params["random_state"]))])
    baseline = DummyRegressor(strategy="mean").fit(X_tr[NUMERIC], y_tr)
    model.fit(X_tr, y_tr)

    pred = model.predict(X_te)
    metrics = {
        "rmse": float(root_mean_squared_error(y_te, pred)),
        "mae": float(mean_absolute_error(y_te, pred)),
        "r2": float(r2_score(y_te, pred)),
        "baseline_rmse": float(root_mean_squared_error(y_te, baseline.predict(X_te[NUMERIC]))),
        "n_train": int(len(X_tr)), "n_test": int(len(X_te)),
    }
    metrics["rmse_gain_vs_baseline_pct"] = 100 * (1 - metrics["rmse"] / metrics["baseline_rmse"])

    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", f"sqlite:///{ROOT / 'mlflow.db'}"))
    mlflow.set_experiment("athletes_total_lift")
    lin = lineage.collect()
    with mlflow.start_run(run_name="gbm_from_feast") as run:
        mlflow.log_params({f"train.{k}": v for k, v in params.items() if k != "model"})
        mlflow.log_params({f"model.{k}": v for k, v in params["model"].items()})
        mlflow.log_params({f"lineage.{k}": v for k, v in lin.items()})
        mlflow.set_tags({"data.versions": "raw(DVC) -> dbt -> Feast -> model", "lineage.complete": "true"})
        mlflow.log_metrics(metrics)
        # skops refuses unknown types by default. These three come from the HistGradientBoosting model we just
        # trained ourselves, so they are trusted explicitly (and only these) for this run's own artifact.
        mlflow.sklearn.log_model(model, name="model", input_example=X_te.head(3), skops_trusted_types=[
            "functools.partial",
            "sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor",
            "sklearn.utils.validation.check_array"])
        metrics["mlflow_run_id"] = run.info.run_id

    (ROOT / "models").mkdir(exist_ok=True)
    joblib.dump(model, ROOT / "models/model.joblib")
    (ROOT / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    print("lineage:", json.dumps(lin, indent=2))


if __name__ == "__main__":
    main()
