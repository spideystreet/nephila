{{ config(materialized='table') }}

SELECT
    cis::BIGINT                                                     AS cis,
    {{ clean_text('cip7') }}                                        AS cip7,
    {{ clean_text('libelle_presentation') }}                        AS libelle_presentation,
    {{ clean_text('statut_admin') }}                                AS statut_admin,
    {{ clean_text('etat_commercialisation') }}                      AS etat_commercialisation,
    {{ parse_bdpm_date('date_declaration_commercialisation') }}     AS date_declaration_commercialisation,
    {{ clean_text('cip13') }}                                       AS cip13,
    {{ clean_text('agrement_collectivites') }}                      AS agrement_collectivites,
    {{ clean_text('taux_remboursement') }}                          AS taux_remboursement,
    {{ clean_text('prix_medicament') }}                             AS prix_medicament
FROM {{ source('raw', 'cis_cip_bdpm') }}
WHERE {{ is_valid_cis('cis') }}
