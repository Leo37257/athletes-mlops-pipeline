-- One typed copy of the raw CrossFit Games athlete export. No filtering here: every rule lives in a mart.
select
    cast(athlete_id as bigint)  as athlete_id,
    name, region, team, affiliate, gender,
    age, height, weight,
    fran, helen, grace, filthy50, fgonebad, run400, run5k,
    candj, snatch, deadlift, backsq, pullups,
    eat, train, background, experience, schedule, howlong
from read_csv_auto('{{ var("raw_path") }}', sample_size = -1)
