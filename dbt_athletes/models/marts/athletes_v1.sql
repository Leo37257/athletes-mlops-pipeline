{{ config(location=var('marts_dir') ~ '/athletes_v1.parquet') }}
-- Version 1: keep every column, drop rows missing any of the four lifts, add total_lift.
select
    *,
    deadlift + candj + snatch + backsq as total_lift
from {{ ref('stg_athletes') }}
where deadlift is not null and candj is not null and snatch is not null and backsq is not null
