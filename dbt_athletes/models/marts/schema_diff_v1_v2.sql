{{ config(materialized='table') }}
-- Which columns were added or removed between schema version 1 and version 2.
with v1 as (select column_name from information_schema.columns where table_name = 'athletes_v1'),
     v2 as (select column_name from information_schema.columns where table_name = 'athletes_v2')
select
    coalesce(v1.column_name, v2.column_name) as column_name,
    v1.column_name is not null as in_v1,
    v2.column_name is not null as in_v2,
    case when v1.column_name is null then 'added in v2'
         when v2.column_name is null then 'dropped in v2'
         else 'kept' end as change
from v1 full outer join v2 using (column_name)
order by change, column_name
