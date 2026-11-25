{% set corpus = ref('stg_opentdb') %}
{% set benchmark = ref('int_benchmark_results') %}
{% set obt = ref('obt_silver') %}

with colonnes as (
    select table_name, column_name, data_type
    from duckdb_columns()
    where database_name = '{{ obt.database }}' and schema_name = '{{ obt.schema }}'
),
attendues as (
    select column_name, data_type from colonnes where table_name = '{{ benchmark.identifier }}'
    union all
    select column_name, data_type from colonnes
    where table_name = '{{ corpus.identifier }}' and column_name <> 'question_id'
),
observees as (
    select column_name, data_type from colonnes where table_name = '{{ obt.identifier }}'
),
manquantes as (
    select * from attendues
    except all
    select * from observees
),
en_trop as (
    select * from observees
    except all
    select * from attendues
)
select 'colonne_ou_type_manquant' as ecart, * from manquantes
union all
select 'colonne_ou_type_en_trop' as ecart, * from en_trop
