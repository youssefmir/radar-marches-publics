-- Table de faits : grain marché × titulaire (attribution initiale).
-- Les montants additifs sont portés par montant_part (montant du marché réparti entre co-titulaires)
-- afin que la somme sur les titulaires redonne le montant du marché sans double compte.
select
    a.attribution_id,
    a.marche_uid,
    a.acheteur_id,
    a.titulaire_key,
    coalesce(c.code_cpv, '00000000')                 as code_cpv,
    a.date_key,
    coalesce(g.code_departement, 'NR')               as departement_code,
    a.procedure_code,
    a.annee,
    a.nature,
    a.type_marche,
    a.titulaire_categorie                            as categorie_titulaire_publiee,
    t.categorie                                      as categorie_titulaire,
    a.montant_marche,
    a.montant_part,
    a.montant_statut,
    a.montant_anomalie,
    a.offres_recues,
    a.offres_statut,
    case when a.offres_recues is not null then a.offres_recues = 1 end as est_offre_unique,
    a.nb_titulaires,
    a.poids_marche,
    a.duree_mois,
    a.titulaire_distance,
    a.marche_innovant,
    a.sous_traitance_declaree,
    a.source_dataset
from {{ ref('int_attributions') }} a
left join {{ ref('dim_cpv') }} c on c.code_cpv = a.code_cpv
left join {{ ref('stg_ref__geo') }} g on g.code_departement = a.acheteur_departement_code
left join {{ ref('int_titulaires') }} t on t.titulaire_key = a.titulaire_key
