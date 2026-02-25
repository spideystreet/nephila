{{ config(materialized='table') }}

SELECT
    cis::BIGINT                             AS cis,
    NULLIF(TRIM(date_debut), '')::DATE      AS date_debut,
    NULLIF(TRIM(date_fin), '')::DATE        AS date_fin,
    {{ clean_text('texte_info_importante') }} AS texte_info_importante
FROM {{ source('raw', 'cis_infoimportantes') }}
WHERE {{ is_valid_cis('cis') }}
