select *
from {{ source('silver_inputs', 'opentdb') }}
