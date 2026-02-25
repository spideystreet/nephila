{{ config(materialized='table') }}

-- Unique active substances extracted from compositions
SELECT DISTINCT
    TRIM(code_substance)        AS code_substance,
    TRIM(denomination_substance) AS denomination_substance
FROM {{ source('raw', 'cis_compo_bdpm') }}
WHERE code_substance IS NOT NULL
  AND TRIM(code_substance) != ''
  AND nature_composant = 'SA'
