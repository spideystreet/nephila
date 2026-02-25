{{ config(materialized='table') }}

SELECT
    TRIM(substance_a)           AS substance_a,
    TRIM(substance_b)           AS substance_b,
    TRIM(niveau_contrainte)     AS niveau_contrainte,
    NULLIF(TRIM(nature_risque), '')     AS nature_risque,
    NULLIF(TRIM(conduite_a_tenir), '')  AS conduite_a_tenir
FROM {{ source('raw', 'ansm_interaction') }}
WHERE substance_a IS NOT NULL
  AND substance_b IS NOT NULL
  AND niveau_contrainte IS NOT NULL
