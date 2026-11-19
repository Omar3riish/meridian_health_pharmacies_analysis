SELECT *
FROM products;

SELECT 
    product_id, 
    COUNT(*) AS duplicate_count
FROM products
GROUP BY product_id
HAVING COUNT(*) > 1;

SELECT 
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(product_id) AS missing_product_id,
    COUNT(*) - COUNT(product_name) AS missing_product_name,
    COUNT(*) - COUNT(category_id) AS missing_category_id,
    COUNT(*) - COUNT(supplier_id) AS missing_supplier_id,
    COUNT(*) - COUNT(unit_price) AS missing_unit_price,
    COUNT(*) - COUNT(cost_price) AS missing_cost_price,
    COUNT(*) - COUNT(brand) AS missing_brand,
    COUNT(*) - COUNT(expiry_date) AS missing_expiry_date,
    COUNT(*) - COUNT(storage_condition) AS missing_storage_condition,
    COUNT(*) - COUNT(created_at) AS missing_created_at,
    COUNT(*) - COUNT(pack_info) AS missing_pack_info
FROM products;


SELECT DISTINCT brand
FROM products;


SELECT DISTINCT storage_condition
FROM products;


SELECT DISTINCT pack_info
FROM products;



SELECT 
    pack_info AS original_text,
    TRIM(
        COALESCE(
            SUBSTRING(pack_info FROM 'Pack:\s*([0-9]+[a-zA-Z]+(?:\s*[a-zA-Z]+)?)'),
            SUBSTRING(pack_info FROM '([0-9]+\s*(?:tabs|caps|ml|g|units))'))
    ) AS pack,
    
    TRIM(
        SUBSTRING(pack_info FROM 'Strength:\s*([0-9]+(?:mg|ml|mg/5ml)?(?:\s*/\s*[0-9]+(?:mg|ml)?)?)')
    ) AS strength,
    
    TRIM(
        COALESCE(
            SUBSTRING(pack_info FROM 'Form:\s*([a-zA-Z]+)'),
            CASE 
                WHEN pack_info LIKE '%tabs%' THEN 'Tablet'
                WHEN pack_info LIKE '%caps%' THEN 'Capsule'
                WHEN pack_info LIKE '%ml%' THEN 'Liquid'
                WHEN pack_info LIKE '%g%' AND (pack_info LIKE '%Cream%' OR pack_info LIKE '%Bandage%') THEN 'Cream/Bandage'
                WHEN pack_info LIKE '%units%' THEN 'Kit'
                ELSE NULL
            END
        )
    ) AS form
FROM products;

ALTER TABLE products
ADD COLUMN pack_col TEXT,
ADD COLUMN strength_col TEXT,
ADD COLUMN form_col TEXT;

UPDATE products
SET 
    pack_col = TRIM(SUBSTRING(pack_info FROM 'Pack:\s*([^/|]+)')),
    strength_col = TRIM(SUBSTRING(pack_info FROM 'Strength:\s*([^/|]+)')),
    form_col = TRIM(SUBSTRING(pack_info FROM 'Form:\s*([^/|]+)'));




