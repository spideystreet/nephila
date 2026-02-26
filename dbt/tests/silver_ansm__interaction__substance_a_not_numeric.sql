-- substance_a must never be a bare page number (e.g. "2", "183").
-- These are parsing artefacts from the ANSM PDF layout.
-- Fails if any row has a purely numeric substance_a.
SELECT substance_a
FROM {{ ref('silver_ansm__interaction') }}
WHERE substance_a ~ '^[0-9]+$'
