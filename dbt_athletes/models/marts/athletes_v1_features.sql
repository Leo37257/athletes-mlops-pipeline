{{ config(location=var('marts_dir') ~ '/athletes_v1_features.parquet') }}
-- Feature-store view of version 1 (the baseline distribution for drift monitoring).
select
    athlete_id,
    cast('{{ var("v1_as_of") }}' as timestamp) as event_timestamp,
    age, height, weight, gender, region, candj, snatch, deadlift, backsq, total_lift
from {{ ref('athletes_v1') }}
where athlete_id is not null
qualify row_number() over (partition by athlete_id order by total_lift desc) = 1
