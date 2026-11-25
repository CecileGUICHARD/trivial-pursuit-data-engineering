select *
from {{ source('silver_inputs', 'ministral_p1_choices') }}
