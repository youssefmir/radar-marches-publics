-- Vue « marché » (une ligne par marché) : objet, acheteur, CPV, montant, offres et titulaire principal.
-- Sert aux fiches acheteur et au signal « titulaire sortant » du radar.
select
    f.marche_uid,
    any_value(f.acheteur_id)                                   as acheteur_id,
    any_value(f.code_cpv)                                      as code_cpv,
    any_value(f.procedure_code)                                as procedure_code,
    any_value(f.departement_code)                              as departement_code,
    min(d.date)                                                as date_notification,
    any_value(f.annee)                                         as annee,
    any_value(f.type_marche)                                   as type_marche,
    any_value(f.nature)                                        as nature,
    any_value(f.montant_marche)                                as montant_marche,
    any_value(f.offres_recues)                                 as offres_recues,
    any_value(f.duree_mois)                                    as duree_mois,
    count(*)                                                   as nb_titulaires,
    arg_min(f.titulaire_key, f.titulaire_key)                  as titulaire_principal_key,
    max(case when f.categorie_titulaire = 'PME' then 1 else 0 end) = 1 as au_moins_un_titulaire_pme,
    any_value(a.objet)                                         as objet
from {{ ref('fct_attributions') }} f
join {{ ref('dim_date') }} d using (date_key)
join {{ ref('int_attributions') }} a using (attribution_id)
group by f.marche_uid
