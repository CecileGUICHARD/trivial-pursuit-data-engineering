select *
from {{ source('silver_inputs', 'gemma_p3_expert_advanced') }}
