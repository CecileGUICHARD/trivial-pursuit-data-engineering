with totals as (
    select
        model_id,
        prompt_id,
        difficulty,
        case when grouping(type) = 1 then 'all' else type end as type,
        count(*) as response_count,
        count(*) filter (where ai_correct) as correct_count,
        100.0 * count(*) filter (where ai_correct) / count(*) as success_pct,
        avg(case type when 'multiple' then 25.0 when 'boolean' then 50.0 end) as chance_pct
    from {{ ref('obt_silver') }}
    group by grouping sets (
        (model_id, prompt_id, difficulty, type),
        (model_id, prompt_id, difficulty)
    )
)
select totals.*, success_pct - chance_pct as above_chance_pp
from totals
