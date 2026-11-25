with attendues as (
    select corpus.*
    from {{ source('silver_inputs', 'opentdb') }} as corpus
    cross join range(6)
),
observees as (
    select
        type, difficulty, category, question, correct_answer, incorrect_answers,
        question_id, answer_choices, expected_answer, category_id
    from {{ ref('obt_silver') }}
),
manquantes as (
    select * from attendues
    except all
    select * from observees
),
en_trop as (
    select * from observees
    except all
    select * from attendues
)
select 'manquante_ou_modifiee' as ecart, * from manquantes
union all
select 'ajoutee_ou_modifiee' as ecart, * from en_trop
