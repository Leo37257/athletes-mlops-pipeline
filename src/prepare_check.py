"""Gate before any transformation: the raw file must be exactly the DVC-tracked version and look like the dataset."""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.lineage import dvc_md5  # noqa: E402

EXPECTED_ROWS = 423006
REQUIRED = ["athlete_id", "region", "gender", "age", "height", "weight", "candj", "snatch", "deadlift", "backsq",
            "eat", "background", "experience", "schedule", "howlong"]


def main() -> None:
    raw = ROOT / "data/raw/athletes.csv"
    h = hashlib.md5()
    with open(raw, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    tracked = dvc_md5(ROOT / "data/raw/athletes.csv.dvc")
    df = pd.read_csv(raw, usecols=REQUIRED)
    result = {"md5": h.hexdigest(), "dvc_md5": tracked, "rows": int(len(df)),
              "missing_columns": [c for c in REQUIRED if c not in df.columns]}
    result["ok"] = result["md5"] == tracked and result["rows"] == EXPECTED_ROWS and not result["missing_columns"]
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports/raw_check.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))
    if not result["ok"]:
        raise SystemExit("raw data does not match the DVC-tracked version")


if __name__ == "__main__":
    main()
