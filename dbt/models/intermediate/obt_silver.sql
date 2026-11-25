{{ config(materialized='table') }}

select
    benchmark.*,
    question.* exclude (question_id)
from {{ ref('int_benchmark_results') }} as benchmark
inner join {{ ref('stg_opentdb') }} as question
    using (question_id)
