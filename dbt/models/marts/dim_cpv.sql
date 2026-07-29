-- Nomenclature CPV avec ses niveaux hiérarchiques ; libellés de division/groupe repris des codes racine.
with c as (select * from {{ ref('stg_ref__cpv') }}),
divisions as (select division_code, libelle as division_libelle from c where code_cpv = division_code || '000000'),
groupes as (select groupe_code, libelle as groupe_libelle from c where code_cpv = groupe_code || '00000')

select
    c.code_cpv,
    c.libelle,
    c.division_code,
    d.division_libelle,
    c.groupe_code,
    g.groupe_libelle,
    c.classe_code,
    c.profondeur,
    case
        when c.division_code = '45' then 'Travaux'
        when c.division_code::integer >= 50 then 'Services'
        else 'Fournitures'
    end as type_cpv
from c
left join divisions d using (division_code)
left join groupes g using (groupe_code)
union all
select '00000000', 'Code CPV absent ou hors nomenclature', '00', 'Non classé', '000', 'Non classé', '0000', 0, 'Non classé'
