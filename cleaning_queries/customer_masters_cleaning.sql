/*customer_masters_cleaning*/

SELECT*
FROM customer_masters;


SELECT 
    customer_id, 
    COUNT(*) AS duplicate_count
FROM customer_masters
GROUP BY customer_id
HAVING COUNT(*) > 1;



SELECT 
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(customer_id) AS missing_customer_id,
    COUNT(*) - COUNT(full_name) AS missing_full_name,
    COUNT(*) - COUNT(email) AS missing_email,
    COUNT(*) - COUNT(phone) AS missing_phone,
    COUNT(*) - COUNT(city) AS missing_city,
    COUNT(*) - COUNT(signup_date) AS missing_signup_date,
    COUNT(*) - COUNT(notes) AS missing_notes
FROM customer_masters;


SELECT DISTINCT city
FROM customer_masters
ORDER BY city;



UPDATE customer_masters
SET city = INITCAP(TRIM(city));


UPDATE customer_masters
SET city = CASE 
    WHEN INITCAP(TRIM(city)) IN ('Toronto, On', 'Trnto') THEN 'Toronto'
    
    WHEN INITCAP(TRIM(city)) IN ('Vancouver, Bc', 'Vancouvr') THEN 'Vancouver'
    
    WHEN INITCAP(TRIM(city)) = 'Calgary, Ab' THEN 'Calgary'
    
    WHEN INITCAP(TRIM(city)) IN ('Montreal, Qc', 'Montréal') THEN 'Montreal'
    
    WHEN INITCAP(TRIM(city)) = 'Edmonton, Ab' THEN 'Edmonton'
    
    WHEN INITCAP(TRIM(city)) = 'Ottawa, On' THEN 'Ottawa'
    
    WHEN INITCAP(TRIM(city)) = 'Winnipeg, Mb' THEN 'Winnipeg'
    
    WHEN INITCAP(TRIM(city)) IN ('Quebec', 'Qc City') THEN 'Quebec City'
    
    WHEN INITCAP(TRIM(city)) = 'Regina, Sk' THEN 'Regina'
    
    WHEN INITCAP(TRIM(city)) = 'Moncton, Nb' THEN 'Moncton'
    
    WHEN INITCAP(TRIM(city)) = 'Halifax, Ns' THEN 'Halifax'
    
    WHEN INITCAP(TRIM(city)) = 'Waterloo, On' THEN 'Waterloo'
    
    ELSE INITCAP(TRIM(city))
END;




SELECT DISTINCT * 
FROM dim_customers;

SELECT 
    notes AS original_note,
    CASE 
        WHEN notes LIKE 'Platinum member%'              THEN 'Platinum'
        WHEN notes LIKE 'Gold member%'                  THEN 'Gold'
        WHEN notes LIKE 'Silver member%'                THEN 'Silver'
        WHEN notes = 'Prefers pickup, not delivery'     THEN 'Prefers pickup, not delivery'
        WHEN notes = 'Prefers text reminders'           THEN 'Prefers text reminders'
        WHEN notes = 'Requested large-print labels'     THEN 'Requested large-print labels'
        WHEN notes = 'Opted out of email marketing'     THEN 'Opted out of email marketing'
        ELSE 'Others'
    END AS customer_segment
FROM dim_customers;


SELECT COUNT(*) AS null_count
FROM dim_customers
WHERE notes IS NULL;


SELECT 
    CASE 
        WHEN notes LIKE 'Platinum member%'              THEN 'Platinum'
        WHEN notes LIKE 'Gold member%'                  THEN 'Gold'
        WHEN notes LIKE 'Silver member%'                THEN 'Silver'
        WHEN notes = 'Prefers pickup, not delivery'     THEN 'Prefers pickup, not delivery'
        WHEN notes = 'Prefers text reminders'           THEN 'Prefers text reminders'
        WHEN notes = 'Requested large-print labels'     THEN 'Requested large-print labels'
        WHEN notes = 'Opted out of email marketing'     THEN 'Opted out of email marketing'
        ELSE 'Others'
    END AS customer_segment,
    COUNT(*) AS total_customers
FROM dim_customers
GROUP BY 1
ORDER BY total_customers DESC;

ALTER TABLE dim_customers
ADD COLUMN customer_segment VARCHAR(50);

UPDATE dim_customers
SET customer_segment = CASE 
    WHEN notes IS NULL OR TRIM(notes) = ''        THEN 'Others'
    WHEN notes LIKE 'Platinum member%'              THEN 'Platinum'
    WHEN notes LIKE 'Gold member%'                  THEN 'Gold'
    WHEN notes LIKE 'Silver member%'                THEN 'Silver'
    WHEN notes = 'Prefers pickup, not delivery'     THEN 'Prefers pickup, not delivery'
    WHEN notes = 'Prefers text reminders'           THEN 'Prefers text reminders'
    WHEN notes = 'Requested large-print labels'     THEN 'Requested large-print labels'
    WHEN notes = 'Opted out of email marketing'     THEN 'Opted out of email marketing'
    ELSE 'Others'
END;


