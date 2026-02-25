{{ config(materialized='table') }}

SELECT
    cis::BIGINT                                                     AS cis,
    TRIM(denomination)                                              AS denomination,
    TRIM(forme_pharma)                                              AS forme_pharma,
    TRIM(voies_admin)                                               AS voies_admin,
    NULLIF(TRIM(statut_amm), '')                                    AS statut_amm,
    NULLIF(TRIM(type_amm), '')                                      AS type_amm,
    NULLIF(TRIM(etat_commercialisation), '')                        AS etat_commercialisation,
    TO_DATE(NULLIF(TRIM(date_amm), ''), 'DD/MM/YYYY')               AS date_amm,
    NULLIF(TRIM(statut_bdm), '')                                    AS statut_bdm,
    NULLIF(TRIM(num_autorisation_eu), '')                           AS num_autorisation_eu,
    NULLIF(TRIM(titulaire), '')                                     AS titulaire,
    UPPER(TRIM(surveillance_renforcee)) = 'OUI'                     AS surveillance_renforcee
FROM {{ source('raw', 'cis_bdpm') }}
WHERE cis IS NOT NULL
  AND cis ~ '^[0-9]+$'
