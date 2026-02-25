{{ config(materialized='table') }}

-- Unique generic groups
SELECT DISTINCT
    TRIM(id_groupe)     AS id_groupe,
    TRIM(libelle_groupe) AS libelle_groupe
FROM {{ source('raw', 'cis_gener_bdpm') }}
WHERE id_groupe IS NOT NULL
  AND TRIM(id_groupe) != ''
