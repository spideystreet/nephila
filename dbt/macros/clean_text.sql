{% macro clean_text(col) %}
    NULLIF(TRIM({{ col }}), '')
{% endmacro %}
