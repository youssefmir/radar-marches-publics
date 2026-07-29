select
    titulaire_key,
    titulaire_siren,
    titulaire_type_id,
    -- Nom masqué pour les entrepreneurs individuels (personnes physiques) et les titulaires non identifiés.
    case
        when est_entrepreneur_individuel then 'Entrepreneur individuel (nom masqué)'
        when titulaire_key = 'INCONNU' then 'Titulaire non identifié'
        else titulaire_nom
    end                                     as titulaire_nom_affichable,
    coalesce(categorie, 'Inconnue')         as categorie,
    tranche_effectif,
    nature_juridique,
    est_entrepreneur_individuel,
    enrichi_sirene,
    code_naf,
    libelle_naf,
    departement_code,
    region_code,
    nb_marches,
    montant_total
from {{ ref('int_titulaires') }}
