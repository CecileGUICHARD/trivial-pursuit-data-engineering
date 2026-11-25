select question_id, model_id, prompt_id, count(*) as effectif
from {{ ref('obt_silver') }}
group by question_id, model_id, prompt_id
having count(*) > 1
