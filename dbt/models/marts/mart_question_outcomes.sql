select
    question_id,
    question,
    type,
    difficulty,
    category_id,
    category,
    correct_answer,
    incorrect_answers,
    answer_choices,
    expected_answer,
    count(distinct (model_id, prompt_id)) as configuration_count,
    case
        when bool_and(ai_correct) then 'all_correct'
        when not bool_or(ai_correct) then 'all_incorrect'
        else 'mixed'
    end as outcome
from {{ ref('obt_silver') }}
group by all
