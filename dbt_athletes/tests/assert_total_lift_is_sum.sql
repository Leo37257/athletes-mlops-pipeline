select * from {{ ref('athletes_v2') }}
where abs(total_lift - (deadlift + candj + snatch + backsq)) > 1e-9
