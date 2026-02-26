{{ config(materialized='table') }}

-- Unique active substances extracted from compositions.
-- DISTINCT ON (code_substance) picks one denomination per code,
-- since the same code can appear with minor label variations across CIS entries.
SELECT DISTINCT ON (TRIM(code_substance))
    TRIM(code_substance)         AS code_substance,
    TRIM(denomination_substance) AS denomination_substance
FROM {{ source('raw', 'cis_compo_bdpm') }}
WHERE code_substance IS NOT NULL
  AND TRIM(code_substance) != ''
  AND nature_composant = 'SA'
ORDER BY TRIM(code_substance)
