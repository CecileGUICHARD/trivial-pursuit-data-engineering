select *
from {{ source('silver_inputs', 'gemma_p1_choices') }}
