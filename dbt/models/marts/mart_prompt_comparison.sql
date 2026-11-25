with comparaisons as (
    select
        avant.model_id,
        avant.prompt_id as prompt_from,
        apres.prompt_id as prompt_to,
        count(*) as pair_count,
        count(*) filter (where not avant.ai_correct and apres.ai_correct) as gain_count,
        count(*) filter (where avant.ai_correct and not apres.ai_correct) as loss_count,
        count(*) filter (where avant.ai_correct and apres.ai_correct) as both_correct_count,
        count(*) filter (where not avant.ai_correct and not apres.ai_correct) as both_incorrect_count,
        100.0 * count(*) filter (where avant.ai_correct) / count(*) as success_from_pct,
        100.0 * count(*) filter (where apres.ai_correct) / count(*) as success_to_pct,
        100.0 * count(*) filter (where avant.format_valid) / count(*) as compliance_from_pct,
        100.0 * count(*) filter (where apres.format_valid) / count(*) as compliance_to_pct,
        avg(avant.response_time) as avg_response_time_from_s,
        avg(apres.response_time) as avg_response_time_to_s
    from {{ ref('obt_silver') }} as avant
    inner join {{ ref('obt_silver') }} as apres
        on avant.question_id = apres.question_id and avant.model_id = apres.model_id
    where (avant.prompt_id, apres.prompt_id) in (
        ('P1_choices', 'P2_expert'),
        ('P1_choices', 'P3_expert_advanced'),
        ('P2_expert', 'P3_expert_advanced')
    )
    group by avant.model_id, avant.prompt_id, apres.prompt_id
)
select
    *,
    success_to_pct - success_from_pct as success_delta_pp,
    compliance_to_pct - compliance_from_pct as compliance_delta_pp,
    avg_response_time_to_s - avg_response_time_from_s as response_time_delta_s
from comparaisons
