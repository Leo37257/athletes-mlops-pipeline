"""feast apply + materialize: register the definitions, then load the dbt output into the online store."""
import sys
from datetime import datetime, timezone
from pathlib import Path

from feast import FeatureStore

REPO = Path(__file__).resolve().parents[1] / "feature_repo"


def main() -> None:
    sys.path.insert(0, str(REPO))
    import definitions as d
    store = FeatureStore(repo_path=str(REPO))
    store.apply([d.athlete, d.v1_source, d.v2_source, d.athlete_features_v1, d.athlete_features_v2, d.total_lift_v2])
    # only v2 is served online; v1 is the offline baseline for drift monitoring
    store.materialize(start_date=datetime(2025, 12, 1, tzinfo=timezone.utc),
                      end_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
                      feature_views=["athlete_features_v2"])
    views = [v.name for v in store.list_feature_views()]
    print("feature views:", views)
    # smoke test: read one athlete back from the online store
    import pandas as pd
    ids = pd.read_parquet(REPO.parent / "data/marts/athletes_v2_features.parquet", columns=["athlete_id"]).athlete_id.head(1).tolist()
    row = store.get_online_features(features=store.get_feature_service("total_lift_v2"),
                                    entity_rows=[{"athlete_id": int(ids[0])}]).to_dict()
    print("online sample:", {k: v[0] for k, v in row.items()})


if __name__ == "__main__":
    main()
