{{ config(materialized='table') }}

-- Generic drug group memberships
-- type_generique: 0=princeps, 1=générique, 2=générique par assimilation, 4=CPP
SELECT
    TRIM(id_groupe)         AS id_groupe,
    cis::BIGINT             AS cis,
    TRIM(type_generique)    AS type_generique,
    NULLIF(TRIM(num_tri), '') AS num_tri
FROM {{ source('raw', 'cis_gener_bdpm') }}
WHERE cis IS NOT NULL
  AND cis ~ '^[0-9]+$'
  AND id_groupe IS NOT NULL
