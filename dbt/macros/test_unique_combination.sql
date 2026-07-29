{# Test générique : unicité d'une combinaison de colonnes (sans dépendance à dbt_utils). #}
{% test unique_combination(model, columns) %}
select {{ columns | join(', ') }}, count(*) as n
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1
{% endtest %}
