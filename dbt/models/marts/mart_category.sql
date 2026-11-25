select
    model_id,
    prompt_id,
    category_id,
    category,
    count(*) as response_count,
    count(*) filter (where ai_correct) as correct_count,
    100.0 * count(*) filter (where ai_correct) / count(*) as success_pct
from {{ ref('obt_silver') }}
group by model_id, prompt_id, category_id, category
