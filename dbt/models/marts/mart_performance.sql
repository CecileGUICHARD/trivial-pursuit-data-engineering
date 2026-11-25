with effectifs as (
    select model_id, prompt_id,
        count(*) as response_count,
        count(*) filter (where ai_correct) as correct_count,
        count(*) filter (where format_valid and not ai_correct) as incorrect_conforming_count,
        count(*) filter (where not format_valid) as out_of_format_count,
        count(*) filter (where format_valid) as conforming_count,
        avg(response_time) as avg_response_time_s
    from {{ ref('obt_silver') }}
    group by model_id, prompt_id
)
select
    model_id, prompt_id, response_count,
    correct_count, 100.0 * correct_count / response_count as correct_pct,
    incorrect_conforming_count, 100.0 * incorrect_conforming_count / response_count as incorrect_conforming_pct,
    out_of_format_count, 100.0 * out_of_format_count / response_count as out_of_format_pct,
    100.0 * conforming_count / response_count as compliance_pct,
    avg_response_time_s
from effectifs
