{{ config(severity="warn") }}
-- Warn, not fail: the course notebook (and the reference row counts) keep these rows. dbt surfaces them so they can be reviewed.
select * from {{ ref('athletes_v2') }} where bmi < 10 or bmi > 80
