{% macro parse_bdpm_date(col) %}
    TO_DATE(NULLIF(TRIM({{ col }}), ''), 'DD/MM/YYYY')
{% endmacro %}
