{{ config(location=var('marts_dir') ~ '/athletes_v2.parquet') }}
-- Version 2: modelling-ready table. Same rules, in the same order, as the course notebook:
-- required columns -> outlier bounds -> 'Decline to answer|' becomes NULL -> survey columns required -> derived features.
-- athlete_id is kept as the entity key for the feature store (the notebook dropped it).
with required as (
    select * from {{ ref('stg_athletes') }}
    where region is not null and age is not null and weight is not null and height is not null
      and howlong is not null and gender is not null and eat is not null and background is not null
      and experience is not null and schedule is not null
      and deadlift is not null and candj is not null and snatch is not null and backsq is not null
),
bounded as (
    select * from required
    where weight < 1500
      and gender <> '--'
      and age >= 18
      and height < 96 and height > 48
      and deadlift > 0
      and ((gender = 'Female' and deadlift <= 636) or (gender <> 'Female' and deadlift <= 1105))
      -- second deadlift filter, kept verbatim from the notebook
      and ((weight > 0 and deadlift <= 1105) or (gender = 'Female' and deadlift < 636))
      and candj > 0 and candj <= 395
      and snatch > 0 and snatch <= 496
      and backsq > 0 and backsq <= 1069
),
declined_to_null as (
    select
        athlete_id,
        nullif(region, 'Decline to answer|')     as region,
        nullif(gender, 'Decline to answer|')     as gender,
        age, height, weight, candj, snatch, deadlift, backsq,
        nullif(eat, 'Decline to answer|')        as eat,
        nullif(background, 'Decline to answer|') as background,
        nullif(experience, 'Decline to answer|') as experience,
        nullif(schedule, 'Decline to answer|')   as schedule,
        nullif(howlong, 'Decline to answer|')    as howlong
    from bounded
)
select
    *,
    deadlift + candj + snatch + backsq as total_lift,
    height * 0.0254                    as height_m,
    weight * 0.453592                  as weight_kg,
    (weight * 0.453592) / power(height * 0.0254, 2) as bmi,
    case when age >= 18 and age < 25  then '18-24'
         when age >= 25 and age < 35  then '25-34'
         when age >= 35 and age < 45  then '35-44'
         when age >= 45 and age < 60  then '45-59'
         when age >= 60 and age < 100 then '60+' end as age_group
from declined_to_null
where background is not null and experience is not null and schedule is not null
  and howlong is not null and eat is not null
