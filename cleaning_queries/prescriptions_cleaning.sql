SELECT *
FROM prescriptions;

SELECT 
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(prescription_id) AS missing_prescription_id,
    COUNT(*) - COUNT(store_id) AS missing_store_id,
    COUNT(*) - COUNT(product_id) AS missing_product_id,
    COUNT(*) - COUNT(customer_id) AS missing_customer_id,
    COUNT(*) - COUNT(doctor_name) AS missing_doctor_name,
    COUNT(*) - COUNT(issue_date) AS missing_issue_date,
    COUNT(*) - COUNT(dosage) AS missing_dosage
FROM prescriptions;

SELECT 
    prescription_id, 
    COUNT(*) AS duplicate_count
FROM prescriptions
GROUP BY prescription_id
HAVING COUNT(*) > 1;




UPDATE prescriptions
SET doctor_name = 'Dr. ' || INITCAP(TRIM(REGEXP_REPLACE(doctor_name, '^(dr\.?)\s*', '', 'i')));

SELECT DISTINCT doctor_name
FROM prescriptions;



SELECT DISTINCT dosage
FROM prescriptions;


UPDATE prescriptions
SET dosage = CASE 
    -- Daily / Once Daily variants
    WHEN LOWER(TRIM(dosage)) IN ('1x daily', '1 tablet daily', '1 tab/day') THEN 'Daily'
    
    -- Twice Daily variants
    WHEN LOWER(TRIM(dosage)) IN ('twice a day', '2x daily', 'bid') THEN 'Twice Daily'
    
    -- Weekly / Once Weekly variants
    WHEN LOWER(TRIM(dosage)) IN ('inject once weekly', 'inj 1x/wk', '1 injection weekly') THEN 'Weekly'
    
    -- Every 6 Hours variants
    WHEN LOWER(TRIM(dosage)) IN ('5 ml every 6 hrs', '5ml q6h', '5ml every 6 hours') THEN '5 ml Every 6 Hours'
    
    -- As Needed variants
    WHEN LOWER(TRIM(dosage)) IN ('as needed', 'prn') THEN 'As Needed'
    
    -- Fallback for any other values
    ELSE INITCAP(TRIM(dosage))
END;