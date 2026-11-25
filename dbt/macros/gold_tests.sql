{% macro gold_ecarts(attendu, observe) %}
select 'manquant_ou_modifie' as ecart, *
from (select * from {{ attendu }} except all select * from {{ observe }})
union all
select 'ajoute_ou_modifie' as ecart, *
from (select * from {{ observe }} except all select * from {{ attendu }})
{% endmacro %}

{% test gold_grain(model, keys, row_count) %}
with grains_invalides as (
    select {{ keys | join(', ') }}
    from {{ model }}
    group by {{ keys | join(', ') }}
    having count(*) <> 1
        {% for key in keys %} or {{ key }} is null {% endfor %}
)
select 'grain_invalide' as controle, count(*) as effectif
from grains_invalides
having count(*) > 0
union all
select 'volume_inattendu', count(*)
from {{ model }}
having count(*) <> {{ row_count }}
{% endtest %}

{% test gold_dimension_concordance(model, dimensions) %}
with attendu as (
    select model_id, prompt_id, {{ dimensions | join(', ') }},
        count(*) as response_count,
        count(*) filter (where ai_correct) as correct_count,
        100.0 * count(*) filter (where ai_correct) / count(*) as success_pct
    from {{ ref('obt_silver') }}
    group by model_id, prompt_id, {{ dimensions | join(', ') }}
), observe as (
    select model_id, prompt_id, {{ dimensions | join(', ') }}, response_count, correct_count, success_pct
    from {{ model }}
)
{{ gold_ecarts('attendu', 'observe') }}
{% endtest %}
