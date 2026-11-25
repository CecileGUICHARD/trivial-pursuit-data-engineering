{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set schema = custom_schema_name -%}
    {%- if schema is none and node.resource_type == 'model' -%}
        {%- set schemas = {'staging': 'staging', 'intermediate': 'intermediate', 'marts': 'gold'} -%}
        {%- set schema = schemas.get(node.fqn[1]) -%}
    {%- endif -%}
    {%- if schema is none -%}
        {{ target.schema }}
    {%- elif target.name == 'local' -%}
        {{ schema | trim }}
    {%- else -%}
        {{ target.schema }}_{{ schema | trim }}
    {%- endif -%}
{%- endmacro %}
