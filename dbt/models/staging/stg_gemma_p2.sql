select *
from {{ source('silver_inputs', 'gemma_p2_expert') }}
