-- Attributions initiales (modification_id = 0) : une ligne par marché × titulaire.
-- On garde les données telles que publiées ; les règles de nettoyage sont appliquées en intermediate.
with src as (
    select * from {{ source('raw', 'decp') }}
    where modification_id = 0
)

select
    uid                                                    as marche_uid,
    id                                                     as marche_id_acheteur,
    upper(trim(nature))                                    as nature_brute,
    acheteur_id,
    acheteur_nom,
    acheteur_categorie,
    acheteur_departement_code,
    acheteur_region_code,
    nullif(trim(titulaire_id), '')                         as titulaire_id,
    case
        when upper(replace(replace(titulaire_typeIdentifiant, '-', '_'), ' ', '_')) in ('SIRET') then 'SIRET'
        when upper(titulaire_typeIdentifiant) like 'TVA%' then 'TVA'
        when upper(replace(replace(titulaire_typeIdentifiant, '-', '_'), ' ', '_')) like 'HORS_UE' then 'HORS_UE'
        when titulaire_typeIdentifiant is null then null
        else 'AUTRE'
    end                                                    as titulaire_type_id,
    titulaire_nom,
    titulaire_categorie,
    titulaire_activite_code,
    titulaire_activite_libelle,
    titulaire_departement_code,
    titulaire_region_code,
    titulaire_distance,
    objet,
    montant,
    montant_anomalie,
    type                                                   as type_marche,
    codeCPV                                                as code_cpv,
    procedure                                              as procedure_brute,
    techniques,
    dureeMois                                              as duree_mois,
    offresRecues                                           as offres_recues,
    dateNotification                                       as date_notification,
    datePublicationDonnees                                 as date_publication,
    considerationsSociales                                 as considerations_sociales,
    considerationsEnvironnementales                        as considerations_environnementales,
    marcheInnovant                                         as marche_innovant,
    sousTraitanceDeclaree                                  as sous_traitance_declaree,
    lieuExecution_code                                     as lieu_execution_code,
    lieuExecution_typeCode                                 as lieu_execution_type,
    sourceDataset                                          as source_dataset
from src
