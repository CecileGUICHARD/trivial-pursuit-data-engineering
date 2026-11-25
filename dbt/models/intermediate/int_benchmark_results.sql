select * from {{ ref('stg_gemma_p1') }}
union all by name
select * from {{ ref('stg_gemma_p2') }}
union all by name
select * from {{ ref('stg_gemma_p3') }}
union all by name
select * from {{ ref('stg_ministral_p1') }}
union all by name
select * from {{ ref('stg_ministral_p2') }}
union all by name
select * from {{ ref('stg_ministral_p3') }}
