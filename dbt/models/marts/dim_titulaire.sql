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
    -- RGPD : le nom n'est publiable que si le titulaire est connu comme personne morale
    -- (SIRENE hors entrepreneur individuel, ETI/GE, ou forme sociale explicite dans la raison sociale).
    titulaire_key <> 'INCONNU' and not est_entrepreneur_individuel and (
        enrichi_sirene
        or categorie in ('ETI', 'GE')
        or regexp_matches(upper(coalesce(titulaire_nom, '')),
            '(^|[^A-Z])(SAS|SASU|SARL|SA|EURL|SCOP|SNC|SCI|GIE|SEM|SPL|SCA|SELARL|SELAS|ASSOCIATION|GROUPE|SOCIETE|COMPAGNIE|FONDATION|MUTUELLE|COOPERATIVE)([^A-Z]|$)')
    )                                       as nom_publiable,
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
