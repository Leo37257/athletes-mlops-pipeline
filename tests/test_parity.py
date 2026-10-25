"""The dbt marts must equal the notebook's pandas output, value for value (not just row counts)."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.reference_clean import build_v1, build_v2

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/athletes.csv"
MARTS = ROOT / "data/marts"

pytestmark = pytest.mark.skipif(not (RAW.exists() and (MARTS / "athletes_v2.parquet").exists()),
                                reason="needs the raw CSV (dvc pull) and the dbt marts (dvc repro)")


@pytest.fixture(scope="module")
def raw():
    return pd.read_csv(RAW)


def _canon(df, cols):
    out = df[cols].copy()
    for c in cols:
        if out[c].dtype == object:
            out[c] = out[c].astype("string").fillna("<NA>")
    return out.sort_values(cols, kind="stable").reset_index(drop=True)


def _same(a, b, cols):
    a, b = _canon(a, cols), _canon(b, cols)
    assert len(a) == len(b)
    for c in cols:
        if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c]):
            np.testing.assert_allclose(a[c].to_numpy(float), b[c].to_numpy(float), rtol=1e-9, equal_nan=True, err_msg=c)
        else:
            assert (a[c].astype(str) == b[c].astype(str)).all(), c


def test_v1_matches_notebook(raw):
    ref, got = build_v1(raw), pd.read_parquet(MARTS / "athletes_v1.parquet")
    assert ref.shape == (85191, 28) and got.shape == (85191, 28)
    cols = [c for c in ref.columns if c != "athlete_id"]  # ids contain NaN in the raw file
    _same(ref, got, cols)


def test_v2_matches_notebook(raw):
    ref, got = build_v2(raw), pd.read_parquet(MARTS / "athletes_v2.parquet")
    assert ref.shape == (30147, 19) and got.shape == (30147, 20)  # dbt keeps athlete_id as the entity key
    _same(ref, got, list(ref.columns))
