-- niveau_contrainte must be one of the four canonical constraint levels.
-- Using dollar-quoting to avoid apostrophe escaping issues.
SELECT niveau_contrainte
FROM {{ ref('silver_ansm__interaction') }}
WHERE niveau_contrainte NOT IN (
    'Contre-indication',
    'Association déconseillée',
    $$Précaution d'emploi$$,
    'A prendre en compte'
)
