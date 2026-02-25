{{ config(materialized='table') }}

SELECT
    cis::BIGINT                             AS cis,
    TO_DATE(
        NULLIF(TRIM(date_debut), ''), 'DD/MM/YYYY'
    )                                       AS date_debut,
    TO_DATE(
        NULLIF(TRIM(date_fin), ''), 'DD/MM/YYYY'
    )                                       AS date_fin,
    NULLIF(TRIM(texte_info_importante), '') AS texte_info_importante
FROM {{ source('raw', 'cis_infoimportantes') }}
WHERE cis IS NOT NULL
  AND cis ~ '^[0-9]+$'
