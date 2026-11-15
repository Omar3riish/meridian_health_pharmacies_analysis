SELECT *
FROM stock_log;

SELECT 
    CASE 
        WHEN received_date IS NULL OR last_restocked IS NULL THEN 'Missing Date'
        WHEN received_date < last_restocked THEN 'Invalid (Expired before creation)'
        WHEN received_date = last_restocked THEN 'Same Day'
        ELSE 'Valid'
    END AS date_status,
    COUNT(*) AS condition_count
FROM stock_log
GROUP BY date_status
ORDER BY condition_count DESC;



SELECT 
    CASE 
        WHEN expiry_date IS NULL OR received_date IS NULL THEN 'Missing Date'
        WHEN expiry_date <= received_date THEN 'recevied as expired'
        WHEN expiry_date > received_date THEN 'ok'
        ELSE 'Valid'
    END AS date_status,
    COUNT(*) AS condition_count
FROM stock_log
GROUP BY date_status
ORDER BY condition_count DESC;



ALTER TABLE stock_log
ADD COLUMN shelf_life_status TEXT GENERATED ALWAYS AS (
    CASE 
        WHEN expiry_date IS NULL OR received_date IS NULL THEN 'Missing Date'
        WHEN (expiry_date - received_date) <= 0 THEN 'Expired on Receipt'
        WHEN (expiry_date - received_date) <= 30 THEN 'Critical Danger'
        WHEN (expiry_date - received_date) <= 90 THEN 'High Risk - Monitor'
        WHEN (expiry_date - received_date) <= 180 THEN 'Short Shelf Life'
        ELSE 'Safe'
    END
) STORED;


SELECT 
    shelf_life_status,
    COUNT(*) AS condition_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM stock_log
GROUP BY shelf_life_status
ORDER BY condition_count DESC;


SELECT DISTINCT condition_notes
FROM stock_log;


UPDATE stock_log
SET condition_notes = NULL
WHERE condition_notes LIKE 'Expiring in%';


ALTER TABLE stock_log
ADD COLUMN is_below_reorder_level BOOLEAN;

UPDATE stock_log
SET is_below_reorder_level = (condition_notes LIKE '%Below reorder level%');