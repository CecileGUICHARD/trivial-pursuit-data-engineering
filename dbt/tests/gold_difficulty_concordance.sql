with detail_attendu as (
    select model_id, prompt_id, difficulty, type,
        count(*) as response_count,
        count(*) filter (where ai_correct) as correct_count,
        avg(100.0 / len(answer_choices)) as chance_pct
    from {{ ref('obt_silver') }}
    group by model_id, prompt_id, difficulty, type
), total_attendu as (
    select model_id, prompt_id, difficulty, 'all' as type,
        sum(response_count) as response_count,
        sum(correct_count) as correct_count,
        sum(chance_pct * response_count) / sum(response_count) as chance_pct
    from {{ ref('mart_difficulty') }}
    where type in ('multiple', 'boolean')
    group by model_id, prompt_id, difficulty
), effectifs as (
    select * from detail_attendu
    union all
    select * from total_attendu
), attendu as (
    select model_id, prompt_id, difficulty, type, response_count, correct_count,
        100.0 * correct_count / response_count as success_pct,
        chance_pct,
        100.0 * correct_count / response_count - chance_pct as above_chance_pp
    from effectifs
), observe as (
    select model_id, prompt_id, difficulty, type, response_count, correct_count,
        success_pct, chance_pct, above_chance_pp
    from {{ ref('mart_difficulty') }}
)
{{ gold_ecarts('attendu', 'observe') }}
