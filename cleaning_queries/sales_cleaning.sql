/*set up the sales tables*/

CREATE TABLE sales_data (
    sale_id INTEGER PRIMARY KEY,
    store_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    sale_date TEXT NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    discount_pct NUMERIC(5, 2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL
);

CREATE TABLE sales_data_2 (
    sale_id INTEGER PRIMARY KEY,
    store_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    sale_date TEXT NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    discount_pct NUMERIC(5, 2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL
);

CREATE TABLE sales_data_3 (
    sale_id INTEGER PRIMARY KEY,
    store_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    sale_date TEXT NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    discount_pct NUMERIC(5, 2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
	notes VARCHAR(200)
);




SELECT *
FROM sales_data;
SELECT *
FROM sales_data_2;
SELECT *
FROM sales_data_3;


SELECT
    table_name,
    ordinal_position,
    column_name,
    data_type,
    character_maximum_length,
    numeric_precision,
    numeric_scale,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN (
      'sales_data',
      'sales_data_2',
      'sales_data_3'
  )
ORDER BY
    ordinal_position,
    table_name;



SELECT 
    tc.table_name, 
    tc.constraint_name, 
    tc.constraint_type, 
    kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.table_schema = 'public' 
  AND tc.table_name IN ('sales_data', 'sales_data_2', 'sales_data_3')
  AND tc.constraint_type = 'PRIMARY KEY';


  SELECT 
    COUNT(*) AS total_rows,
    COUNT(sale_id) AS non_null_sale_ids,
    COUNT(*) - COUNT(sale_id) AS null_sale_ids
FROM sales_data_3;

SELECT 
    c.table_name,
    c.column_name,
    c.is_nullable,
    COALESCE(tc.constraint_type, 'NO CONSTRAINT') AS key_type
FROM information_schema.columns c
LEFT JOIN information_schema.table_constraints tc
    ON c.table_name = tc.table_name 
    AND tc.constraint_type = 'PRIMARY KEY'
LEFT JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND c.column_name = kcu.column_name
WHERE c.table_schema = 'public'
  AND c.column_name = 'sale_id'
  AND c.table_name IN ('sales_data', 'sales_data_2', 'sales_data_3')
ORDER BY c.table_name;








/*cleaning sales_3 table's sale_id*/

SELECT 
    sale_id, 
    COUNT(*) AS duplicate_count
FROM sales_data_3
GROUP BY sale_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, sale_id;



SELECT *
FROM (
    SELECT 
        *,
        COUNT(*) OVER(PARTITION BY sale_id) AS total_occurrences
    FROM sales_data_3
) subquery
WHERE total_occurrences > 1
ORDER BY sale_id, sale_date;


SELECT 
    sale_id, 
    COUNT(*) AS occurrences_across_tables
FROM (
    SELECT sale_id FROM sales_data
    UNION ALL
    SELECT sale_id FROM sales_data_2
    UNION ALL
    SELECT sale_id FROM sales_data_3
) all_sales
GROUP BY sale_id
HAVING COUNT(*) > 1
ORDER BY occurrences_across_tables DESC, sale_id;


DELETE FROM sales_data_3 a
USING sales_data_3 b
WHERE a.ctid > b.ctid 
  AND a.sale_id = b.sale_id;

ALTER TABLE sales_data_3 ADD PRIMARY KEY (sale_id);

ALTER TABLE sales_data_3 
    ALTER COLUMN sale_id SET NOT NULL,
    ALTER COLUMN store_id SET NOT NULL,
    ALTER COLUMN employee_id SET NOT NULL,
    ALTER COLUMN product_id SET NOT NULL,
    ALTER COLUMN customer_id SET NOT NULL,
    ALTER COLUMN quantity SET NOT NULL,
    ALTER COLUMN sale_date SET NOT NULL,
    ALTER COLUMN unit_price SET NOT NULL,
    ALTER COLUMN discount_pct SET NOT NULL,
    ALTER COLUMN payment_method SET NOT NULL;

	SELECT
    table_name,
    ordinal_position,
    column_name,
    data_type,
    character_maximum_length,
    numeric_precision,
    numeric_scale,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN (
      'sales_data',
      'sales_data_2',
      'sales_data_3'
  )
ORDER BY
    ordinal_position,
    table_name;




/*cleaning unit_price colums*/

SELECT table_name, column_name, data_type 
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('sales_data', 'sales_data_2', 'sales_data_3')
  AND column_name IN ('unit_price', 'unit_price')
ORDER BY table_name;


SELECT unit_price 
FROM sales_data_2;

UPDATE sales_data_2
SET unit_price = REPLACE(REPLACE(TRIM(unit_price), '$', ''), ',', '');

ALTER TABLE sales_data_2
ALTER COLUMN unit_price TYPE NUMERIC(10,2) 
USING unit_price::NUMERIC(10,2);



ALTER TABLE sales_data_3
ALTER COLUMN unit_price TYPE NUMERIC(10,2) 
USING unit_price::NUMERIC(10,2);


SELECT table_name, column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_schema = 'public'
  AND column_name = 'unit_price'
  AND table_name IN ('sales_data', 'sales_data_2', 'sales_data_3');


/*combination of the sales tables)*/
CREATE TABLE sales AS
SELECT 
    sale_id,
    store_id,
    employee_id,
    product_id,
    customer_id,
    quantity,
    sale_date, 
    unit_price,
    discount_pct,
    INITCAP(TRIM(payment_method)) AS payment_method, 
    CAST(NULL AS VARCHAR(200)) AS notes, 
    'Group 1' AS source_table
FROM sales_data

UNION ALL

SELECT 
    sale_id,
    store_id,
    employee_id,
    product_id,
    customer_id,
    quantity,
    sale_date, 
    unit_price,
    discount_pct,
    INITCAP(TRIM(payment_method)) AS payment_method,
    CAST(NULL AS VARCHAR(200)) AS notes, 
    'Group 2' AS source_table
FROM sales_data_2

UNION ALL

SELECT 
    sale_id,
    store_id,
    employee_id,
    product_id,
    customer_id,
    quantity,
    sale_date, 
    unit_price,
    discount_pct,
    INITCAP(TRIM(payment_method)) AS payment_method,
    notes, 
    'Group 3' AS source_table
FROM sales_data_3;






/*cleaning discount_pct*/


ALTER TABLE sales 
ALTER COLUMN discount_pct TYPE numeric(6,4);
UPDATE sales
SET discount_pct = discount_pct / 100.0;

SELECT discount_pct
FROM sales;



/*solving date column problems*/

SELECT * 
FROM sales;


SELECT 
    'Group 2' AS source_table, 
    sale_id, 
    sale_date AS raw_date
FROM sales_data_2
WHERE CAST(SPLIT_PART(sale_date, '/', 1) AS INTEGER) > 12

UNION ALL

SELECT 
    'Group 3' AS source_table, 
    sale_id, 
    sale_date AS raw_date
FROM sales_data_3
WHERE CAST(SPLIT_PART(sale_date, '/', 1) AS INTEGER) > 12

ORDER BY source_table, sale_id;


SELECT 
    'Group 1' AS source_table, 
    sale_id, 
    sale_date AS raw_date,
    CAST(SPLIT_PART(sale_date, '/', 2) AS INTEGER) AS second_number
FROM sales_data
WHERE CAST(SPLIT_PART(sale_date, '/', 2) AS INTEGER) > 12
ORDER BY sale_id;

SELECT 
    sale_id,
    source_table,
    sale_date AS original_date_text,
    CASE 
        WHEN source_table = 'Group 1' THEN TO_DATE(sale_date, 'DD/MM/YYYY')
        
        WHEN source_table IN ('Group 2', 'Group 3') THEN TO_DATE(sale_date, 'MM/DD/YYYY')
        
        ELSE NULL
    END AS cleaned_sale_date
FROM sales;

UPDATE sales
SET sale_date = CASE 
    WHEN source_table = 'Group 1' THEN TO_CHAR(TO_DATE(sale_date, 'DD/MM/YYYY'), 'MM/DD/YYYY')
    
    WHEN source_table IN ('Group 2', 'Group 3') THEN TO_CHAR(TO_DATE(sale_date, 'MM/DD/YYYY'), 'MM/DD/YYYY')
    
    ELSE sale_date
END;

ALTER TABLE sales
ALTER COLUMN sale_date TYPE DATE 
USING TO_DATE(sale_date, 'MM/DD/YYYY');


SELECT*
FROM sales;


