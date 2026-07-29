select code_departement, nom_departement, code_region, nom_region
from {{ ref('stg_ref__geo') }}
union all
select 'NR', 'Non renseigné / hors COG', 'NR', 'Non renseignée'
