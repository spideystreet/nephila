{{ config(materialized='table') }}

-- type_generique: 0=princeps, 1=générique, 2=générique par assimilation, 4=CPP
SELECT
    TRIM(id_groupe)             AS id_groupe,
    cis::BIGINT                 AS cis,
    TRIM(type_generique)        AS type_generique,
    {{ clean_text('num_tri') }} AS num_tri
FROM {{ source('raw', 'cis_gener_bdpm') }}
WHERE {{ is_valid_cis('cis') }}
  AND id_groupe IS NOT NULL
