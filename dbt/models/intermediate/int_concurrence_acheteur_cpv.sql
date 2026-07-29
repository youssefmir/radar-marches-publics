-- Intensité concurrentielle historique par acheteur × groupe CPV (3 premiers chiffres) :
-- alimente le score « concurrence » et le signal « titulaire sortant » du radar.
with m as (
    select
        marche_uid,
        any_value(acheteur_id)            as acheteur_id,
        any_value(substr(code_cpv, 1, 3)) as groupe_cpv,
        any_value(offres_recues)          as offres_recues,
        any_value(montant_marche)         as montant_marche,
        max(date_notification)            as date_notification
    from {{ ref('int_attributions') }}
    group by 1
),

agg as (
    select
        acheteur_id,
        groupe_cpv,
        count(*)                                                          as nb_marches,
        count(offres_recues)                                              as nb_marches_offres,
        avg(offres_recues)                                                as offres_moyennes,
        avg(case when offres_recues = 1 then 1.0 when offres_recues > 1 then 0.0 end) as taux_offre_unique,
        median(montant_marche)                                            as montant_median,
        max(date_notification)                                            as derniere_attribution
    from m
    group by 1, 2
),

titulaires as (
    select
        a.acheteur_id,
        substr(a.code_cpv, 1, 3)         as groupe_cpv,
        a.titulaire_key,
        count(distinct a.marche_uid)     as nb_marches_titulaire,
        max(a.date_notification)         as derniere_date
    from {{ ref('int_attributions') }} a
    where a.titulaire_key <> 'INCONNU'
    group by 1, 2, 3
),

top_titulaire as (
    select *
    from titulaires
    qualify row_number() over (
        partition by acheteur_id, groupe_cpv
        order by nb_marches_titulaire desc, derniere_date desc, titulaire_key
    ) = 1
)

select
    agg.*,
    t.titulaire_key                                   as titulaire_principal_key,
    t.nb_marches_titulaire                            as titulaire_principal_nb_marches,
    t.nb_marches_titulaire / agg.nb_marches           as titulaire_principal_part
from agg
left join top_titulaire t using (acheteur_id, groupe_cpv)
