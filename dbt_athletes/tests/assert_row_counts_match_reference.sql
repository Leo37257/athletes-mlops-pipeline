-- Regression guard: the SQL models must reproduce the pandas notebook row counts exactly.
select 'v1' as dataset, (select count(*) from {{ ref('athletes_v1') }}) as actual, {{ var('expected_v1_rows') }} as expected
where (select count(*) from {{ ref('athletes_v1') }}) <> {{ var('expected_v1_rows') }}
union all
select 'v2', (select count(*) from {{ ref('athletes_v2') }}), {{ var('expected_v2_rows') }}
where (select count(*) from {{ ref('athletes_v2') }}) <> {{ var('expected_v2_rows') }}
