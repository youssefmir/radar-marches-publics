-- Attributions nettoyées : période, dédoublonnage, contrôles de validité, montants et offres exploitables.
-- Chaque règle est tracée par un indicateur booléen, chiffré dans le rapport de qualité.
with base as (
    select *
    from {{ ref('stg_decp__attributions') }}
    where date_notification >= date '{{ var("periode_debut") }}'
      and date_notification <= current_date
      and acheteur_id is not null  -- R1b : attribution sans acheteur identifiable écartée
),

-- R2 : doublons exacts (même marché, même titulaire publiés par plusieurs sources) -> une seule ligne.
dedup as (
    select *
    from base
    qualify row_number() over (
        partition by marche_uid, coalesce(titulaire_id, '?')
        -- départage total : le résultat ne dépend jamais de l'ordre de lecture du fichier
        order by date_publication desc nulls last, source_dataset, montant nulls last, objet nulls last,
                 date_notification, offres_recues nulls last, procedure_brute nulls last,
                 titulaire_nom nulls last, titulaire_categorie nulls last, code_cpv, duree_mois nulls last
    ) = 1
),

-- R2b : quasi-doublons publiés sous des identifiants différents (souvent par deux sources) :
-- même acheteur, même objet, même montant, même date de notification, même titulaire.
-- On conserve l'identifiant le plus petit (choix déterministe, cohérent entre co-titulaires).
dedup_contenu as (
    select *
    from dedup
    qualify row_number() over (
        partition by acheteur_id, {{ normalise('objet') }}, montant, date_notification, coalesce(titulaire_id, '?')
        order by marche_uid
    ) = 1
),

-- R2c : accords-cadres multi-attributaires publiés avec un identifiant par titulaire :
-- même acheteur, même objet (non vide), même montant, même date -> un seul marché à plusieurs titulaires.
regroupe as (
    select
        * exclude (marche_uid),
        marche_uid as marche_uid_source,
        case
            when length({{ normalise('objet') }}) >= 10
                then min(marche_uid) over (
                    partition by acheteur_id, {{ normalise('objet') }}, montant, date_notification)
            else marche_uid
        end as marche_uid
    from dedup_contenu
),

enrichi as (
    select
        d.*,
        {{ siret_valide('d.acheteur_id') }}                                       as acheteur_siret_valide,
        d.titulaire_type_id = 'SIRET' and {{ siret_valide('d.titulaire_id') }}    as titulaire_siret_valide,
        -- R3 : montant exploitable (ni nul, ni négatif, ni valeur de remplissage, ni aberrant selon decp.info)
        case
            when d.montant is null then 'absent'
            when d.montant < {{ var('montant_min') }} then 'nul_ou_negatif'
            when d.montant >= {{ var('montant_max') }} then 'valeur_remplissage'
            when d.montant_anomalie = 'aberrant' then 'aberrant'
            else 'ok'
        end                                                                       as montant_statut,
        -- R4 : nombre d'offres exploitable (0 impossible pour un marché attribué, > seuil = saisie erronée)
        case
            when d.offres_recues is null then 'absent'
            when d.offres_recues < 1 then 'zero'
            when d.offres_recues > {{ var('offres_max') }} then 'hors_seuil'
            else 'ok'
        end                                                                       as offres_statut,
        count(*) over (partition by d.marche_uid)                                 as nb_titulaires
    from regroupe d
),

-- R3b : répartition du montant entre co-titulaires.
-- Montant identique sur toutes les lignes -> montant du marché partagé à parts égales ;
-- montants différents (lots publiés sous le même identifiant) -> chaque ligne porte sa propre part.
montants as (
    select
        *,
        case when montant_statut = 'ok' then montant end as montant_ok,
        min(case when montant_statut = 'ok' then montant end) over (partition by marche_uid) as m_min,
        max(case when montant_statut = 'ok' then montant end) over (partition by marche_uid) as m_max,
        count(case when montant_statut = 'ok' then 1 end) over (partition by marche_uid)    as n_ok,
        sum(case when montant_statut = 'ok' then montant end) over (partition by marche_uid) as m_sum
    from enrichi
)

select
    md5(marche_uid_source || '|' || coalesce(titulaire_id, '?'))                  as attribution_id,
    marche_uid,
    marche_uid_source,
    acheteur_id,
    acheteur_siret_valide,
    case
        when titulaire_siret_valide then 'SIRET:' || titulaire_id
        when titulaire_id is not null then coalesce(titulaire_type_id, 'AUTRE') || ':' || titulaire_id
        else 'INCONNU'
    end                                                                           as titulaire_key,
    titulaire_id,
    titulaire_type_id,
    titulaire_siret_valide,
    case when titulaire_siret_valide then substr(titulaire_id, 1, 9) end          as titulaire_siren,
    titulaire_nom,
    coalesce(titulaire_categorie, 'Inconnue')                                     as titulaire_categorie,
    titulaire_activite_code,
    titulaire_activite_libelle,
    titulaire_departement_code,
    titulaire_region_code,
    titulaire_distance,
    acheteur_nom,
    acheteur_categorie,
    acheteur_departement_code,
    acheteur_region_code,
    objet,
    code_cpv,
    {{ code_procedure('procedure_brute') }}                                       as procedure_code,
    procedure_brute,
    case
        when nature_brute like 'ACCORD%' then 'Accord-cadre'
        when nature_brute like '%PARTENARIAT%' then 'Marché de partenariat'
        when nature_brute like '%DEFENSE%' or nature_brute like '%SECURIT%' then 'Marché de défense ou de sécurité'
        when nature_brute like 'MARCH%' then 'Marché'
        else 'Non renseignée'
    end                                                                           as nature,
    coalesce(type_marche, 'Non renseigné')                                        as type_marche,
    techniques,
    duree_mois,
    date_notification,
    cast(strftime(date_notification, '%Y%m%d') as integer)                        as date_key,
    year(date_notification)                                                       as annee,
    montant                                                                       as montant_declare,
    montant_anomalie,
    montant_statut,
    case
        when montant_ok is null then null
        when m_min = m_max then montant_ok
        else m_sum
    end                                                                           as montant_marche,
    case
        when montant_ok is null then null
        when m_min = m_max then montant_ok / n_ok
        else montant_ok
    end                                                                           as montant_part,
    m_min <> m_max                                                                as montants_par_lot,
    offres_recues                                                                 as offres_declarees,
    offres_statut,
    case when offres_statut = 'ok' then offres_recues end                         as offres_recues,
    nb_titulaires,
    1.0 / nb_titulaires                                                           as poids_marche,
    considerations_sociales,
    considerations_environnementales,
    marche_innovant,
    sous_traitance_declaree,
    source_dataset
from montants
