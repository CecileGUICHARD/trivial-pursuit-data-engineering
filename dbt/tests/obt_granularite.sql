with obt as (
    select * from {{ ref('obt_silver') }}
),
modeles(model_id) as (
    values ('google/gemma-4-e2b'), ('mistralai/ministral-3-3b')
),
prompts(prompt_id) as (
    values ('P1_choices'), ('P2_expert'), ('P3_expert_advanced')
),
combinaisons_attendues as (
    select model_id, prompt_id from modeles cross join prompts
),
effectifs as (
    select model_id, prompt_id, count(*) as observe
    from obt
    group by model_id, prompt_id
),
controles as (
    select 'lignes' as controle, 'ensemble' as groupe, count(*) as observe, 31740 as attendu
    from obt

    union all

    select 'questions_distinctes', 'ensemble', count(distinct question_id), 5290
    from obt

    union all

    select 'modele_prompt', concat_ws(' / ', model_id, prompt_id), coalesce(effectifs.observe, 0), 5290
    from combinaisons_attendues
    left join effectifs using (model_id, prompt_id)

    union all

    select 'resultats_par_question', corpus.question_id, count(obt.inference_id), 6
    from {{ ref('stg_opentdb') }} as corpus
    left join obt using (question_id)
    group by corpus.question_id
)
select * from controles where observe <> attendu
