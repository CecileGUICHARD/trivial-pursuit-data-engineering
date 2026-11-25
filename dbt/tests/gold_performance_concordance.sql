with attendu as (
    select model_id, prompt_id,
        count(*) as response_count,
        count(*) filter (where ai_correct) as correct_count,
        100.0 * count(*) filter (where ai_correct) / count(*) as correct_pct,
        count(*) filter (where not ai_correct and format_valid) as incorrect_conforming_count,
        100.0 * count(*) filter (where not ai_correct and format_valid) / count(*) as incorrect_conforming_pct,
        count(*) filter (where not format_valid) as out_of_format_count,
        100.0 * count(*) filter (where not format_valid) / count(*) as out_of_format_pct,
        100.0 * count(*) filter (where format_valid) / count(*) as compliance_pct
    from {{ ref('obt_silver') }}
    group by model_id, prompt_id
), observe as (
    select * exclude (avg_response_time_s)
    from {{ ref('mart_performance') }}
), ecarts as (
    {{ gold_ecarts('attendu', 'observe') }}
), latences as (
    select model_id, prompt_id, sum(response_time) / count(response_time) as moyenne_s
    from {{ ref('obt_silver') }}
    group by model_id, prompt_id
)
select ecart, model_id, prompt_id from ecarts
union all
select 'latence', model_id, prompt_id
from {{ ref('mart_performance') }} as mart
join latences using (model_id, prompt_id)
where not coalesce(abs(mart.avg_response_time_s - latences.moyenne_s) <= 1e-10, false)
union all
select 'decomposition', model_id, prompt_id
from {{ ref('mart_performance') }}
where response_count is distinct from correct_count + incorrect_conforming_count + out_of_format_count
