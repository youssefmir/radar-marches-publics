-- Aucun nombre d'offres exploitable hors de l'intervalle [1, offres_max].
select * from {{ ref('fct_attributions') }}
where offres_recues is not null and (offres_recues < 1 or offres_recues > {{ var('offres_max') }})
