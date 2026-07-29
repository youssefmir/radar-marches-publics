select
    code_departement,
    nom_departement,
    code_region,
    nom_region
from {{ source('raw', 'geo_departements') }}
