-- Requête 1 : Structure de la table currencies
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'currencies'
ORDER BY ordinal_position;

-- Requête 2 : Exemples de données dans la table currencies
SELECT * FROM currencies LIMIT 10;

-- Requête 3 : Vérifier les devises disponibles
SELECT 
    currency_code,
    currency_ratio,
    COUNT(*) as count
FROM currencies
GROUP BY currency_code, currency_ratio
ORDER BY currency_code;
