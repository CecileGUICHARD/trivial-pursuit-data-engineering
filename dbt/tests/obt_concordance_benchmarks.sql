with attendues as (
    select * from {{ source('silver_inputs', 'gemma_p1_choices') }}
    union all by name
    select * from {{ source('silver_inputs', 'gemma_p2_expert') }}
    union all by name
    select * from {{ source('silver_inputs', 'gemma_p3_expert_advanced') }}
    union all by name
    select * from {{ source('silver_inputs', 'ministral_p1_choices') }}
    union all by name
    select * from {{ source('silver_inputs', 'ministral_p2_expert') }}
    union all by name
    select * from {{ source('silver_inputs', 'ministral_p3_expert_advanced') }}
),
observees as (
    select * exclude (
        type, difficulty, category, question, correct_answer, incorrect_answers,
        answer_choices, expected_answer, category_id
    )
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
