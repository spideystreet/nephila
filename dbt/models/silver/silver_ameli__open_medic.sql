{{ config(materialized='table') }}

-- Open Medic CIP13 — drug reimbursement data from CNAM Assurance Maladie.
-- Source: NB_{year}_cip13.CSV.gz — aggregate at CIP13 level (all demographics combined).
-- Actual columns: CIP13, l_cip13, nbc, REM, BSE, BOITES
-- Numeric values use French locale format: "228.579,71" (dot=thousands, comma=decimal).
-- Joins CIP13 → CIS via the BDPM CIP table.

SELECT
    om."CIP13"::BIGINT                                              AS cip13,
    cip.cis::BIGINT                                                 AS cis,
    {{ clean_text('om."l_cip13"') }}                                AS libelle_presentation,
    REPLACE(om."BOITES", '.', '')::BIGINT                           AS nb_boites,
    REPLACE(REPLACE(om."REM",  '.', ''), ',', '.')::NUMERIC         AS montant_rembourse,
    REPLACE(REPLACE(om."BSE",  '.', ''), ',', '.')::NUMERIC         AS montant_base_remboursement,
    REPLACE(om."nbc", '.', '')::INTEGER                             AS nb_beneficiaires

FROM {{ source('raw', 'open_medic') }} AS om
LEFT JOIN {{ source('raw', 'cis_cip_bdpm') }} AS cip
    ON om."CIP13" = cip.cip13
WHERE om."CIP13" IS NOT NULL
