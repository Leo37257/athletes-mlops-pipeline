{% snapshot athletes_v2_snapshot %}
{{ config(target_schema='snapshots', unique_key='athlete_id', strategy='check',
          check_cols=['age', 'height_m', 'weight_kg', 'bmi', 'total_lift']) }}
-- History of the modelling table: when an athlete's measured values change between data refreshes,
-- dbt closes the old row and opens a new one (slowly changing dimension, type 2).
select athlete_id, age, height_m, weight_kg, bmi, total_lift from {{ ref('athletes_v2_features') }}
{% endsnapshot %}
