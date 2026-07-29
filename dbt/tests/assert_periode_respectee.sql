select * from {{ ref('fct_attributions') }}
where annee < year(date '{{ var("periode_debut") }}') or annee > year(current_date)
