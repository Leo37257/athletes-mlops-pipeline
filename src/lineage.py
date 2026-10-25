"""Collect the identifiers that tie one trained model to the exact data and code that produced it."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dvc_md5(dvc_file: Path) -> str:
    m = re.search(r"md5:\s*([0-9a-f]{32})", dvc_file.read_text())
    return m.group(1) if m else "unknown"


def dbt_models_hash() -> str:
    h = hashlib.sha256()
    for p in sorted((ROOT / "dbt_athletes").rglob("*.sql")) + sorted((ROOT / "dbt_athletes").rglob("*.yml")):
        if "target" in p.parts or "dbt_packages" in p.parts:
            continue
        h.update(p.name.encode()); h.update(p.read_bytes())
    return h.hexdigest()


def dbt_run_info() -> dict:
    p = ROOT / "dbt_athletes/target/run_results.json"
    if not p.exists():
        return {}
    r = json.loads(p.read_text())
    res = r.get("results", [])
    return {
        "invocation_id": r["metadata"].get("invocation_id"),
        "dbt_version": r["metadata"].get("dbt_version"),
        "tests_passed": sum(1 for x in res if x["status"] == "pass"),
        "tests_warned": sum(1 for x in res if x["status"] == "warn"),
        "tests_failed": sum(1 for x in res if x["status"] in ("fail", "error")),
    }


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "no-commit"


def collect() -> dict:
    marts = ROOT / "data/marts"
    info = dbt_run_info()
    return {
        "dvc_raw_md5": dvc_md5(ROOT / "data/raw/athletes.csv.dvc"),
        "dbt_models_sha256": dbt_models_hash()[:16],
        "dbt_invocation_id": info.get("invocation_id", "n/a"),
        "dbt_version": info.get("dbt_version", "n/a"),
        "dbt_tests_passed": info.get("tests_passed", -1),
        "dbt_tests_warned": info.get("tests_warned", -1),
        "dbt_tests_failed": info.get("tests_failed", -1),
        "features_v2_sha256": sha256_file(marts / "athletes_v2_features.parquet")[:16],
        "feast_registry_sha256": sha256_file(ROOT / "feature_repo/data/registry.db")[:16],
        "feast_feature_service": "total_lift_v2",
        "git_sha": git_sha(),
    }
