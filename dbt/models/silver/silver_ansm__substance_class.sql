{{ config(materialized='table') }}

-- Deduplicate substance-class mappings: prefer "parenthetical" over "voir_aussi"
-- when the same (substance_dci, classe_ansm) pair exists in both sources.
SELECT DISTINCT ON (LOWER(TRIM(substance_dci)), UPPER(TRIM(classe_ansm)))
    LOWER(TRIM(substance_dci))              AS substance_dci,
    UPPER(TRIM(classe_ansm))                AS classe_ansm,
    TRIM(source)                            AS source
FROM {{ source('raw', 'ansm_substance_class') }}
WHERE substance_dci IS NOT NULL
  AND classe_ansm IS NOT NULL
  AND source IS NOT NULL
ORDER BY
    LOWER(TRIM(substance_dci)),
    UPPER(TRIM(classe_ansm)),
    CASE source WHEN 'parenthetical' THEN 1 ELSE 2 END
