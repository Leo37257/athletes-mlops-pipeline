-- Every outlier rule must hold on the final v2 table. Any returned row is a failure.
select * from {{ ref('athletes_v2') }}
where weight >= 1500 or age < 18 or height <= 48 or height >= 96 or gender = '--'
   or candj <= 0 or candj > 395 or snatch <= 0 or snatch > 496 or backsq <= 0 or backsq > 1069
   or deadlift <= 0 or (gender = 'Female' and deadlift > 636) or (gender <> 'Female' and deadlift > 1105)
