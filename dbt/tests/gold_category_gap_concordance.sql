with taux as (
    select prompt_id, category_id, category,
        100.0 * count(*) filter (where ai_correct and model_id = 'google/gemma-4-e2b')
            / count(*) filter (where model_id = 'google/gemma-4-e2b') as gemma_success_pct,
        100.0 * count(*) filter (where ai_correct and model_id = 'mistralai/ministral-3-3b')
            / count(*) filter (where model_id = 'mistralai/ministral-3-3b') as ministral_success_pct
    from {{ ref('obt_silver') }}
    group by prompt_id, category_id, category
), attendu as (
    select *, gemma_success_pct - ministral_success_pct as success_gap_pp,
        gemma_success_pct = ministral_success_pct as is_tie
    from taux
), observe as (
    select prompt_id, category_id, category, gemma_success_pct, ministral_success_pct, success_gap_pp, is_tie
    from {{ ref('mart_category_gap') }}
)
{{ gold_ecarts('attendu', 'observe') }}
