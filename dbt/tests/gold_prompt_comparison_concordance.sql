with par_question as (
    select model_id, question_id,
        bool_or(ai_correct) filter (where prompt_id = 'P1_choices') as p1,
        bool_or(ai_correct) filter (where prompt_id = 'P2_expert') as p2,
        bool_or(ai_correct) filter (where prompt_id = 'P3_expert_advanced') as p3
    from {{ ref('obt_silver') }}
    group by model_id, question_id
), paires as (
    select model_id, 'P1_choices' as prompt_from, 'P2_expert' as prompt_to, p1 as avant, p2 as apres from par_question
    union all
    select model_id, 'P1_choices', 'P3_expert_advanced', p1, p3 from par_question
    union all
    select model_id, 'P2_expert', 'P3_expert_advanced', p2, p3 from par_question
), attendu as (
    select model_id, prompt_from, prompt_to, count(*) as pair_count,
        count(*) filter (where avant = false and apres = true) as gain_count,
        count(*) filter (where avant = true and apres = false) as loss_count,
        count(*) filter (where avant = true and apres = true) as both_correct_count,
        count(*) filter (where avant = false and apres = false) as both_incorrect_count
    from paires
    group by model_id, prompt_from, prompt_to
), observe as (
    select model_id, prompt_from, prompt_to, pair_count, gain_count, loss_count,
        both_correct_count, both_incorrect_count
    from {{ ref('mart_prompt_comparison') }}
), ecarts as (
    {{ gold_ecarts('attendu', 'observe') }}
)
select ecart, model_id, prompt_from, prompt_to from ecarts
union all
select 'effectifs_ou_mesures', mart.model_id, mart.prompt_from, mart.prompt_to
from {{ ref('mart_prompt_comparison') }} as mart
left join {{ ref('mart_performance') }} as avant
    on avant.model_id = mart.model_id and avant.prompt_id = mart.prompt_from
left join {{ ref('mart_performance') }} as apres
    on apres.model_id = mart.model_id and apres.prompt_id = mart.prompt_to
where mart.pair_count is distinct from 5290
    or mart.pair_count is distinct from mart.gain_count + mart.loss_count + mart.both_correct_count + mart.both_incorrect_count
    or mart.success_from_pct is distinct from avant.correct_pct
    or mart.success_to_pct is distinct from apres.correct_pct
    or mart.success_delta_pp is distinct from apres.correct_pct - avant.correct_pct
    or mart.compliance_from_pct is distinct from avant.compliance_pct
    or mart.compliance_to_pct is distinct from apres.compliance_pct
    or mart.compliance_delta_pp is distinct from apres.compliance_pct - avant.compliance_pct
    or not coalesce(abs(mart.avg_response_time_from_s - avant.avg_response_time_s) <= 1e-10, false)
    or not coalesce(abs(mart.avg_response_time_to_s - apres.avg_response_time_s) <= 1e-10, false)
    or not coalesce(abs(mart.response_time_delta_s - (apres.avg_response_time_s - avant.avg_response_time_s)) <= 1e-10, false)
