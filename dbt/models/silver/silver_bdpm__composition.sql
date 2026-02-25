{{ config(materialized='table') }}

SELECT
    cis::BIGINT                                 AS cis,
    {{ clean_text('designation_element') }}     AS designation_element,
    {{ clean_text('code_substance') }}          AS code_substance,
    {{ clean_text('denomination_substance') }}  AS denomination_substance,
    {{ clean_text('dosage') }}                  AS dosage,
    {{ clean_text('reference_dosage') }}        AS reference_dosage,
    {{ clean_text('nature_composant') }}        AS nature_composant,
    {{ clean_text('num_liaison_sa_ft') }}       AS num_liaison_sa_ft
FROM {{ source('raw', 'cis_compo_bdpm') }}
WHERE {{ is_valid_cis('cis') }}
