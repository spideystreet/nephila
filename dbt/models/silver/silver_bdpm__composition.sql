{{ config(materialized='table') }}

SELECT
    cis::BIGINT                             AS cis,
    NULLIF(TRIM(designation_element), '')   AS designation_element,
    NULLIF(TRIM(code_substance), '')        AS code_substance,
    NULLIF(TRIM(denomination_substance), '') AS denomination_substance,
    NULLIF(TRIM(dosage), '')                AS dosage,
    NULLIF(TRIM(reference_dosage), '')      AS reference_dosage,
    NULLIF(TRIM(nature_composant), '')      AS nature_composant,
    NULLIF(TRIM(num_liaison_sa_ft), '')     AS num_liaison_sa_ft
FROM {{ source('raw', 'cis_compo_bdpm') }}
WHERE cis IS NOT NULL
  AND cis ~ '^[0-9]+$'
