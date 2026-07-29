{# Contrôle de validité d'un SIRET : 14 chiffres et clé de Luhn
   (exception La Poste, SIREN 356000000 : somme des chiffres multiple de 5). #}
{% macro siret_valide(col) -%}
(
  regexp_full_match(coalesce({{ col }}, ''), '[0-9]{14}')
  and (
    case
      when substr({{ col }}, 1, 9) = '356000000'
        then list_sum([coalesce(try_cast(substr({{ col }}, i, 1) as integer), 0) for i in range(1, 15)]) % 5 = 0
      else list_sum([
        case
          when i % 2 = 1 then
            (coalesce(try_cast(substr({{ col }}, i, 1) as integer), 0) * 2)
            - (case when coalesce(try_cast(substr({{ col }}, i, 1) as integer), 0) * 2 > 9 then 9 else 0 end)
          else coalesce(try_cast(substr({{ col }}, i, 1) as integer), 0)
        end
        for i in range(1, 15)]) % 10 = 0
    end
  )
)
{%- endmacro %}

{# Normalisation d'un libellé : minuscules, sans accents, espaces compactés. #}
{% macro normalise(col) -%}
trim(regexp_replace(lower(strip_accents(coalesce({{ col }}, ''))), '[^a-z0-9]+', ' ', 'g'))
{%- endmacro %}
