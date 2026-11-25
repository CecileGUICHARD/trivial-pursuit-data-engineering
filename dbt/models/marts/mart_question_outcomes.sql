with results as (
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
        end as outcome,
        case
            when count(*) = 6
                and configuration_count = 6
                and count(*) filter (where ai_correct is false and format_valid is true and ai_answer is not null) = 6
                and count(distinct ai_answer) = 1
            then min(ai_answer)
        end as same_wrong_answer
    from {{ ref('obt_silver') }}
    group by all
)
select results.* exclude (same_wrong_answer),
    same_wrong_answer is not null as unanimous_wrong,
    same_wrong_answer
from results
