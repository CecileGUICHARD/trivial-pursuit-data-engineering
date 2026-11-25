with effectifs as (
    select question_id,
        count(distinct (model_id, prompt_id)) as configuration_count,
        count(*) filter (where ai_correct) as correct_count
    from {{ ref('obt_silver') }}
    group by question_id
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
        end as outcome
    from questions join effectifs using (question_id)
), observe as (
    select question_id, question, type, difficulty, category_id, category,
        correct_answer, incorrect_answers, answer_choices, expected_answer, configuration_count, outcome
    from {{ ref('mart_question_outcomes') }}
), ecarts as (
    {{ gold_ecarts('attendu', 'observe') }}
)
select ecart, question_id from ecarts
union all
select 'nombre_de_configurations', question_id from observe where configuration_count is distinct from 6
