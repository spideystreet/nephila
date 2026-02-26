-- substance_a must never start with "+".
-- Lines starting with "+" are substance B markers in the ANSM PDF layout.
-- Fails if any row has a substance_a misclassified from a substance B line.
SELECT substance_a
FROM {{ ref('silver_ansm__interaction') }}
WHERE substance_a LIKE '+%'
