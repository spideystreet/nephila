{% macro is_valid_cis(col='cis') %}
    {{ col }} IS NOT NULL AND {{ col }} ~ '^[0-9]+$'
{% endmacro %}
