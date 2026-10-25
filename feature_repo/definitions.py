"""Feature definitions. The offline source is the parquet that dbt writes, so the feature store never
re-cleans anything: dbt owns the cleaning rules, Feast owns point-in-time retrieval and serving."""
from datetime import timedelta

from feast import Entity, FeatureService, FeatureView, Field, FileSource
from feast.types import Float64, String

athlete = Entity(name="athlete", join_keys=["athlete_id"], description="One CrossFit Games athlete")

v2_source = FileSource(
    name="athletes_v2_source",
    path="../data/marts/athletes_v2_features.parquet",   # produced by dbt model athletes_v2_features
    timestamp_field="event_timestamp",
)
v1_source = FileSource(
    name="athletes_v1_source",
    path="../data/marts/athletes_v1_features.parquet",   # produced by dbt model athletes_v1_features
    timestamp_field="event_timestamp",
)

athlete_features_v2 = FeatureView(
    name="athlete_features_v2",
    entities=[athlete],
    ttl=timedelta(days=3650),
    schema=[
        Field(name="age", dtype=Float64),
        Field(name="height_m", dtype=Float64),
        Field(name="weight_kg", dtype=Float64),
        Field(name="bmi", dtype=Float64),
        Field(name="age_group", dtype=String),
        Field(name="gender", dtype=String),
        Field(name="region", dtype=String),
        Field(name="howlong", dtype=String),
        Field(name="eat", dtype=String),
        Field(name="background", dtype=String),
        Field(name="experience", dtype=String),
        Field(name="schedule", dtype=String),
    ],
    source=v2_source,
    tags={"schema_version": "v2", "owner": "dbt:athletes_v2_features"},
)

athlete_features_v1 = FeatureView(
    name="athlete_features_v1",
    entities=[athlete],
    ttl=timedelta(days=3650),
    schema=[
        Field(name="age", dtype=Float64),
        Field(name="height", dtype=Float64),
        Field(name="weight", dtype=Float64),
        Field(name="gender", dtype=String),
        Field(name="region", dtype=String),
        Field(name="candj", dtype=Float64),
        Field(name="snatch", dtype=Float64),
        Field(name="deadlift", dtype=Float64),
        Field(name="backsq", dtype=Float64),
    ],
    source=v1_source,
    tags={"schema_version": "v1", "owner": "dbt:athletes_v1_features"},
)

total_lift_v2 = FeatureService(name="total_lift_v2", features=[athlete_features_v2])
