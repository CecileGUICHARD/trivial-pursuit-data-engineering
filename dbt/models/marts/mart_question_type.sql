with totals as (
    select
        model_id,
        prompt_id,
        type,
        count(*) as response_count,
        count(*) filter (where ai_correct) as correct_count,
        100.0 * count(*) filter (where ai_correct) / count(*) as success_pct,
        100.0 / case type when 'multiple' then 4 when 'boolean' then 2 end as chance_pct,
        100.0 * count(*) filter (where format_valid) / count(*) as compliance_pct
    from {{ ref('obt_silver') }}
    group by model_id, prompt_id, type
)
select totals.*, success_pct - chance_pct as above_chance_pp
from totals
