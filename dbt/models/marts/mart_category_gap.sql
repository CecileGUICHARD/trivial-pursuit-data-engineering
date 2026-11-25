select
    gemma.prompt_id,
    gemma.category_id,
    gemma.category,
    gemma.success_pct as gemma_success_pct,
    ministral.success_pct as ministral_success_pct,
    gemma.success_pct - ministral.success_pct as success_gap_pp,
    gemma.correct_count * ministral.response_count = ministral.correct_count * gemma.response_count as is_tie
from {{ ref('mart_category') }} as gemma
inner join {{ ref('mart_category') }} as ministral using (prompt_id, category_id)
where gemma.model_id = 'google/gemma-4-e2b'
    and ministral.model_id = 'mistralai/ministral-3-3b'
