with reponses as (
    -- Reproduit le retrait des espaces Unicode par str.strip() dans le scoring Python.
    select *, regexp_replace(
        raw_response,
        '^[[:space:]\p{Z}\x{0085}\x{001c}-\x{001f}]+|[[:space:]\p{Z}\x{0085}\x{001c}-\x{001f}]+$',
        '', 'g'
    ) as reponse_nettoyee
    from {{ ref('obt_silver') }}
),
evaluation as (
    select *, case type
        when 'multiple' then reponse_nettoyee in ('A', 'B', 'C', 'D')
        when 'boolean' then reponse_nettoyee in ('True', 'False')
    end as conforme
    from reponses
)
select inference_id, question_id, model_id, prompt_id
from evaluation
where format_valid is distinct from conforme
    or ai_answer is distinct from case when conforme then reponse_nettoyee end
    or ai_correct is distinct from (conforme and reponse_nettoyee = expected_answer)
    or not coalesce(case type
        when 'multiple' then expected_answer in ('A', 'B', 'C', 'D')
        when 'boolean' then expected_answer in ('True', 'False')
    end, false)
