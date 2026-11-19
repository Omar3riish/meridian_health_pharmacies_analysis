
ALTER TABLE IF EXISTS customer_masters RENAME TO dim_customers;
ALTER TABLE IF EXISTS products         RENAME TO dim_products;
ALTER TABLE IF EXISTS stores           RENAME TO dim_stores;
ALTER TABLE IF EXISTS suppliers        RENAME TO dim_suppliers;
ALTER TABLE IF EXISTS employees        RENAME TO dim_employees;
ALTER TABLE IF EXISTS categories       RENAME TO dim_categories;

ALTER TABLE IF EXISTS sales            RENAME TO fact_sales;
ALTER TABLE IF EXISTS prescriptions    RENAME TO fact_prescriptions;
ALTER TABLE IF EXISTS stock_log        RENAME TO fact_stock_log;


SELECT 
    fs.sale_id,
    fs.sale_date,
    st.store_id,
    st.store_name,
    st.city AS store_city,
    st.region,
    c.customer_id,
    c.full_name AS customer_name,
    c.customer_segment,
    e.employee_id,
    e.employee_name AS handled_by,
    p.product_id,
    p.product_name,
    cat.category_name,
    fs.quantity,
    COALESCE(fs.unit_price, p.unit_price) AS unit_price,
    COALESCE(fs.discount_pct, 0) AS discount_pct,
    (fs.quantity * COALESCE(fs.unit_price, p.unit_price)) AS gross_revenue,
    (fs.quantity * COALESCE(fs.unit_price, p.unit_price) * (1 - COALESCE(fs.discount_pct, 0))) AS net_revenue,
    (fs.quantity * COALESCE(p.cost_price, 0)) AS total_cost,
    fs.payment_method
FROM fact_sales fs
JOIN dim_stores st      ON fs.store_id = st.store_id
JOIN dim_customers c    ON fs.customer_id = c.customer_id
LEFT JOIN dim_employees e ON fs.employee_id = e.employee_id
JOIN dim_products p     ON fs.product_id = p.product_id
JOIN dim_categories cat ON p.category_id = cat.category_id
ORDER BY fs.sale_id;


SELECT 
    sl.batch_number,
    st.store_name,
    p.product_name,
    cat.category_name,
    sup.supplier_name,
    sup.contact_person AS supplier_contact,
    sl.quantity AS stock_quantity,
    sl.reorder_level,
    sl.is_below_reorder_level,
    sl.expiry_date,
    sl.last_restocked,
    sl.shelf_life_status,
    sl.condition_notes
FROM fact_stock_log sl
JOIN dim_products p        ON sl.product_id = p.product_id
LEFT JOIN dim_stores st    ON sl.store_id = st.store_id
JOIN dim_categories cat    ON p.category_id = cat.category_id
LEFT JOIN dim_suppliers sup ON p.supplier_id = sup.supplier_id;


SELECT 
    fp.prescription_id,
    fp.issue_date,
    c.full_name AS patient_name,
    c.phone AS patient_phone,
    p.product_name AS prescribed_medication,
    cat.category_name,
    fp.dosage,
    fp.doctor_name,
    st.store_name AS fulfillment_store,
    st.region
FROM fact_prescriptions fp
JOIN dim_customers c    ON fp.customer_id = c.customer_id
JOIN dim_products p     ON fp.product_id = p.product_id
JOIN dim_categories cat ON p.category_id = cat.category_id
JOIN dim_stores st      ON fp.store_id = st.store_id;
