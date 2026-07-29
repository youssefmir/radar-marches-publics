{# Regroupe les libellés de procédure hétérogènes (casse, apostrophes, versions de schéma)
   en 7 familles stables, documentées dans dim_procedure. #}
{% macro code_procedure(col) -%}
case
  when {{ col }} is null then 'NR'
  when {{ normalise(col) }} like '%sans publicite%' or {{ normalise(col) }} like '%sans mise en concurrence%' then 'SANS_PUB'
  when {{ normalise(col) }} like '%adapte%' then 'MAPA'
  when {{ normalise(col) }} like '%appel d offres ouvert%' then 'AOO'
  when {{ normalise(col) }} like '%appel d offres restreint%' then 'AOR'
  when {{ normalise(col) }} like '%dialogue%' then 'DIALOGUE'
  when {{ normalise(col) }} like '%negoci%' then 'NEGOCIEE'
  when {{ normalise(col) }} like '%concours%' then 'AUTRE'
  else 'AUTRE'
end
{%- endmacro %}
