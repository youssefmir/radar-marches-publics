with derniere as (
    select *
    from {{ ref('int_attributions') }}
    qualify row_number() over (partition by acheteur_id order by date_notification desc, attribution_id) = 1
),
vol as (
    select acheteur_id, count(distinct marche_uid) as nb_marches, sum(montant_part) as montant_total
    from {{ ref('int_attributions') }}
    group by 1
)
select
    d.acheteur_id,
    d.acheteur_nom,
    coalesce(d.acheteur_categorie, 'Non renseignée')                          as acheteur_categorie,
    coalesce(g.code_departement, 'NR')                                         as departement_code,
    d.acheteur_siret_valide                                                    as siret_valide,
    v.nb_marches,
    v.montant_total
from derniere d
join vol v using (acheteur_id)
left join {{ ref('stg_ref__geo') }} g on g.code_departement = d.acheteur_departement_code
