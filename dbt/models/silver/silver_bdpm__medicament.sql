{{ config(materialized='table') }}

SELECT
    cis::BIGINT                                     AS cis,
    TRIM(denomination)                              AS denomination,
    TRIM(forme_pharma)                              AS forme_pharma,
    TRIM(voies_admin)                               AS voies_admin,
    {{ clean_text('statut_amm') }}                  AS statut_amm,
    {{ clean_text('type_amm') }}                    AS type_amm,
    {{ clean_text('etat_commercialisation') }}       AS etat_commercialisation,
    {{ parse_bdpm_date('date_amm') }}               AS date_amm,
    {{ clean_text('statut_bdm') }}                  AS statut_bdm,
    {{ clean_text('num_autorisation_eu') }}          AS num_autorisation_eu,
    {{ clean_text('titulaire') }}                   AS titulaire,
    UPPER(TRIM(surveillance_renforcee)) = 'OUI'     AS surveillance_renforcee
FROM {{ source('raw', 'cis_bdpm') }}
WHERE {{ is_valid_cis('cis') }}
