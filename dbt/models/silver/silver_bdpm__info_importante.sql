{{ config(materialized='table') }}

SELECT
    cis::BIGINT                             AS cis,
    {{ parse_bdpm_date('date_debut') }}     AS date_debut,
    {{ parse_bdpm_date('date_fin') }}       AS date_fin,
    {{ clean_text('texte_info_importante') }} AS texte_info_importante
FROM {{ source('raw', 'cis_infoimportantes') }}
WHERE {{ is_valid_cis('cis') }}
