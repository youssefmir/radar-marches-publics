with jours as (
    select unnest(generate_series(date '{{ var("periode_debut") }}', current_date, interval 1 day))::date as d
)
select
    cast(strftime(d, '%Y%m%d') as integer) as date_key,
    d                                      as date,
    year(d)                                as annee,
    quarter(d)                             as trimestre,
    month(d)                               as mois,
    strftime(d, '%Y-%m')                   as annee_mois,
    isodow(d)                              as jour_semaine
from jours
