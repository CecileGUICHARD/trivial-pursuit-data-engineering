select *
from {{ source('silver_inputs', 'ministral_p3_expert_advanced') }}
