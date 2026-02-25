{{ config(materialized='table') }}

SELECT
    cis::BIGINT                                         AS cis,
    TRIM(condition_prescription_delivrance)             AS condition_prescription_delivrance
FROM {{ source('raw', 'cis_cpd_bdpm') }}
WHERE cis IS NOT NULL
  AND cis ~ '^[0-9]+$'
  AND condition_prescription_delivrance IS NOT NULL
