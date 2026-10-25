"""Reference (pandas) implementation of the v1/v2 cleaning rules, lifted from the course notebook.

The pipeline itself cleans in dbt (SQL). This module exists only so tests/test_parity.py can prove the SQL
models reproduce the original notebook value for value.
"""
import numpy as np
import pandas as pd

LIFTS = ["deadlift", "candj", "snatch", "backsq"]
V2_REQUIRED = ["region", "age", "weight", "height", "howlong", "gender", "eat",
               "background", "experience", "schedule", *LIFTS]
V2_DROP = ["affiliate", "team", "name", "athlete_id", "fran", "helen", "grace",
           "filthy50", "fgonebad", "run400", "run5k", "pullups", "train"]
SURVEY = ["background", "experience", "schedule", "howlong", "eat"]


def build_v1(raw: pd.DataFrame) -> pd.DataFrame:
    v1 = raw.dropna(subset=LIFTS).copy()
    v1["total_lift"] = v1[LIFTS].sum(axis=1)
    return v1


def build_v2(raw: pd.DataFrame) -> pd.DataFrame:
    v2 = raw.dropna(subset=V2_REQUIRED)
    v2 = v2.drop(columns=[c for c in V2_DROP if c in v2.columns])
    v2 = v2[v2["weight"] < 1500]
    v2 = v2[v2["gender"] != "--"]
    v2 = v2[v2["age"] >= 18]
    v2 = v2[(v2["height"] < 96) & (v2["height"] > 48)]
    female = v2["gender"] == "Female"
    v2 = v2[(v2["deadlift"] > 0)
            & ((female & (v2["deadlift"] <= 636)) | (~female & (v2["deadlift"] <= 1105)))]
    female = v2["gender"] == "Female"
    v2 = v2[((v2["weight"] > 0) & (v2["deadlift"] <= 1105)) | (female & (v2["deadlift"] < 636))]
    v2 = v2[(v2["candj"] > 0) & (v2["candj"] <= 395)]
    v2 = v2[(v2["snatch"] > 0) & (v2["snatch"] <= 496)]
    v2 = v2[(v2["backsq"] > 0) & (v2["backsq"] <= 1069)]
    v2 = v2.replace({"Decline to answer|": np.nan}).dropna(subset=SURVEY).copy()
    v2["total_lift"] = v2[LIFTS].sum(axis=1)
    v2["height_m"] = v2["height"] * 0.0254
    v2["weight_kg"] = v2["weight"] * 0.453592
    v2["bmi"] = v2["weight_kg"] / (v2["height_m"] ** 2)
    v2["age_group"] = pd.cut(v2["age"], bins=[18, 25, 35, 45, 60, 100],
                             labels=["18-24", "25-34", "35-44", "45-59", "60+"], right=False).astype(object)
    return v2
