with effectifs as (
    select question_id,
        count(*) as response_count,
        count(distinct (model_id, prompt_id)) as configuration_count,
        count(*) filter (where ai_correct) as correct_count
    from {{ ref('obt_silver') }}
    group by question_id
), consensus as (
    select question_id, ai_answer as same_wrong_answer
    from {{ ref('obt_silver') }}
    join effectifs using (question_id)
    where response_count = 6 and configuration_count = 6
        and ai_correct is false and format_valid is true and ai_answer is not null
    group by question_id, ai_answer
    having count(*) = 6
), questions as (
    select distinct question_id, question, type, difficulty, category_id, category,
        correct_answer, incorrect_answers, answer_choices, expected_answer
    from {{ ref('obt_silver') }}
), attendu as (
    select questions.*, configuration_count,
        case correct_count
            when 6 then 'all_correct'
            when 0 then 'all_incorrect'
            else 'mixed'
        end as outcome,
        same_wrong_answer is not null as unanimous_wrong,
        same_wrong_answer
    from questions
    join effectifs using (question_id)
    left join consensus using (question_id)
), observe as (
    select question_id, question, type, difficulty, category_id, category,
        correct_answer, incorrect_answers, answer_choices, expected_answer, configuration_count, outcome,
        unanimous_wrong, same_wrong_answer
    from {{ ref('mart_question_outcomes') }}
), ecarts as (
    {{ gold_ecarts('attendu', 'observe') }}
)
select ecart, question_id from ecarts
union all
select 'nombre_de_configurations', question_id from observe where configuration_count is distinct from 6
union all
select 'consensus_hors_all_incorrect', question_id
from observe where unanimous_wrong and outcome is distinct from 'all_incorrect'
