{{ config(location=var('marts_dir') ~ '/athletes_v2_features.parquet') }}
-- Feature-store view of version 2: what the model trains on. total_lift is the label and is read from the
-- entity dataframe at training time, not served as a feature.
select
    athlete_id,
    cast('{{ var("v2_as_of") }}' as timestamp) as event_timestamp,
    age, height_m, weight_kg, bmi, age_group,
    gender, region, howlong, eat, background, experience, schedule,
    total_lift
from {{ ref('athletes_v2') }}
where athlete_id is not null
qualify row_number() over (partition by athlete_id order by total_lift desc) = 1
