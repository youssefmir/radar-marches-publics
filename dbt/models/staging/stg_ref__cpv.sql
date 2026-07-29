select
    code_cpv,
    libelle,
    substr(code_cpv, 1, 2) as division_code,
    substr(code_cpv, 1, 3) as groupe_code,
    substr(code_cpv, 1, 4) as classe_code,
    -- niveau hiérarchique : nombre de chiffres significatifs (hors zéros finaux)
    length(rtrim(code_cpv, '0')) as profondeur
from {{ source('raw', 'cpv') }}
where regexp_full_match(code_cpv, '[0-9]{8}')
