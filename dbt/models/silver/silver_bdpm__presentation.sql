{{ config(materialized='table') }}

SELECT
    cis::BIGINT                                                             AS cis,
    NULLIF(TRIM(cip7), '')                                                  AS cip7,
    NULLIF(TRIM(libelle_presentation), '')                                  AS libelle_presentation,
    NULLIF(TRIM(statut_admin), '')                                          AS statut_admin,
    NULLIF(TRIM(etat_commercialisation), '')                                AS etat_commercialisation,
    TO_DATE(
        NULLIF(TRIM(date_declaration_commercialisation), ''), 'DD/MM/YYYY'
    )                                                                       AS date_declaration_commercialisation,
    NULLIF(TRIM(cip13), '')                                                 AS cip13,
    NULLIF(TRIM(agrement_collectivites), '')                                AS agrement_collectivites,
    NULLIF(TRIM(taux_remboursement), '')                                    AS taux_remboursement,
    NULLIF(TRIM(prix_medicament), '')                                       AS prix_medicament
FROM {{ source('raw', 'cis_cip_bdpm') }}
WHERE cis IS NOT NULL
  AND cis ~ '^[0-9]+$'
