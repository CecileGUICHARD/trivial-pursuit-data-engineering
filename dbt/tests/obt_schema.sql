{% set corpus = ref('stg_opentdb') %}
{% set benchmark = ref('int_benchmark_results') %}
{% set obt = ref('obt_silver') %}

with colonnes as (
    select schema_name, table_name, column_name, data_type
    from duckdb_columns()
    where database_name = '{{ obt.database }}'
),
attendues as (
    select column_name, data_type from colonnes
    where schema_name = '{{ benchmark.schema }}' and table_name = '{{ benchmark.identifier }}'
    union all
    select column_name, data_type from colonnes
    where schema_name = '{{ corpus.schema }}' and table_name = '{{ corpus.identifier }}'
        and column_name <> 'question_id'
),
observees as (
    select column_name, data_type from colonnes
    where schema_name = '{{ obt.schema }}' and table_name = '{{ obt.identifier }}'
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
