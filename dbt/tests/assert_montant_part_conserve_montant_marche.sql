-- La somme des parts des co-titulaires doit redonner le montant du marché (tolérance d'arrondi).
select marche_uid, sum(montant_part) as somme_parts, any_value(montant_marche) as montant_marche
from {{ ref('fct_attributions') }}
where montant_marche is not null
group by marche_uid
having abs(sum(montant_part) - any_value(montant_marche)) > 0.01
