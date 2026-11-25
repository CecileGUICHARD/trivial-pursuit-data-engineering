with taux as (
    select model_id, prompt_id, type,
        count(*) as response_count,
        count(*) filter (where ai_correct) as correct_count,
        avg(case when ai_correct then 100.0 else 0.0 end) as success_pct,
        avg(100.0 / len(answer_choices)) as chance_pct,
        avg(case when format_valid then 100.0 else 0.0 end) as compliance_pct
    from {{ ref('obt_silver') }}
    group by model_id, prompt_id, type
), attendu as (
    select taux.*, success_pct - chance_pct as above_chance_pp
    from taux
), observe as (
    select model_id, prompt_id, type, response_count, correct_count,
        success_pct, chance_pct, compliance_pct, above_chance_pp
    from {{ ref('mart_question_type') }}
)
{{ gold_ecarts('attendu', 'observe') }}
