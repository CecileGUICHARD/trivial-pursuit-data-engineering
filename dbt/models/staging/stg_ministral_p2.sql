select *
from {{ source('silver_inputs', 'ministral_p2_expert') }}
