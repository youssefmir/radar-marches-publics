-- Un titulaire par clé ; attributs repris de la ligne la plus récente, complétés par SIRENE si disponible.
with dernieres as (
    select *
    from {{ ref('int_attributions') }}
    qualify row_number() over (partition by titulaire_key order by date_notification desc, attribution_id) = 1
),

volumes as (
    select titulaire_key,
           count(distinct marche_uid) as nb_marches,
           sum(montant_part)          as montant_total
    from {{ ref('int_attributions') }}
    group by 1
)

select
    d.titulaire_key,
    d.titulaire_id,
    d.titulaire_type_id,
    d.titulaire_siren,
    coalesce(s.nom_complet, d.titulaire_nom)                                  as titulaire_nom,
    case
        when s.categorie_entreprise in ('PME', 'ETI', 'GE') then s.categorie_entreprise
        else d.titulaire_categorie
    end                                                                       as categorie,
    s.tranche_effectif,
    s.nature_juridique,
    -- RGPD : un entrepreneur individuel est une personne physique ; son nom n'est jamais exporté.
    coalesce(s.est_entrepreneur_individuel, false)                            as est_entrepreneur_individuel,
    s.siren is not null                                                       as enrichi_sirene,
    coalesce(s.activite_principale, d.titulaire_activite_code)                as code_naf,
    d.titulaire_activite_libelle                                              as libelle_naf,
    d.titulaire_departement_code                                              as departement_code,
    d.titulaire_region_code                                                   as region_code,
    v.nb_marches,
    v.montant_total
from dernieres d
join volumes v using (titulaire_key)
left join {{ ref('stg_sirene__unites') }} s on s.siren = d.titulaire_siren
