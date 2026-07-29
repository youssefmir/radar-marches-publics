select
    siren,
    nom_complet,
    categorie_entreprise,
    tranche_effectif,
    nature_juridique,
    est_entrepreneur_individuel,
    activite_principale,
    region_siege,
    etat_administratif,
    date_creation,
    retrieved_at
from {{ source('raw', 'sirene') }}
