
SELECT 
    TO_CHAR(fs.sale_date, 'YYYY-MM') AS sales_month,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price))::numeric, 2) AS gross_revenue,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))::numeric, 2) AS net_revenue,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * COALESCE(fs.discount_pct, 0))::numeric, 2) AS discount_value,
    ROUND((
        SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * COALESCE(fs.discount_pct, 0)) * 100.0
        / NULLIF(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price)), 0)
    )::numeric, 2) AS discount_leakage_pct
FROM fact_sales fs
JOIN dim_products dp ON fs.product_id = dp.product_id
WHERE fs.sale_date IS NOT NULL
GROUP BY sales_month
ORDER BY sales_month ASC;


SELECT 
    COALESCE(payment_method, 'Not recorded') AS payment_method,
    COUNT(DISTINCT sale_id) AS total_transactions,
    SUM(quantity) AS total_units_sold,
    ROUND(SUM(quantity * unit_price)::numeric, 2) AS gross_sales,
    ROUND(SUM(quantity * unit_price * (1 - COALESCE(discount_pct, 0)))::numeric, 2) AS net_sales,
    ROUND((
        SUM(quantity * unit_price * (1 - COALESCE(discount_pct, 0)))
        / NULLIF(COUNT(DISTINCT sale_id), 0)
    )::numeric, 2) AS avg_order_value,
    ROUND((
        SUM(quantity * unit_price * (1 - COALESCE(discount_pct, 0))) * 100.0
        / NULLIF(SUM(SUM(quantity * unit_price * (1 - COALESCE(discount_pct, 0)))) OVER (), 0)
    )::numeric, 2) AS net_sales_share_pct
FROM fact_sales
GROUP BY payment_method
ORDER BY net_sales DESC;


SELECT 
    s.region,
    COUNT(DISTINCT s.store_id) AS store_count,
    COUNT(DISTINCT f.sale_id) AS total_transactions,
    SUM(f.quantity) AS total_units_sold,
    ROUND(SUM(f.quantity * f.unit_price)::numeric, 2) AS gross_revenue,
    ROUND(SUM(f.quantity * f.unit_price * (1 - COALESCE(f.discount_pct, 0)))::numeric, 2) AS net_revenue,
    ROUND((
        SUM(f.quantity * f.unit_price * (1 - COALESCE(f.discount_pct, 0)))
        / NULLIF(COUNT(DISTINCT f.sale_id), 0)
    )::numeric, 2) AS avg_order_value,
    ROUND((
        SUM(f.quantity * f.unit_price * (1 - COALESCE(f.discount_pct, 0))) * 100.0
        / NULLIF(SUM(SUM(f.quantity * f.unit_price * (1 - COALESCE(f.discount_pct, 0)))) OVER (), 0)
    )::numeric, 2) AS net_revenue_share_pct
FROM fact_sales f
JOIN dim_stores s ON f.store_id = s.store_id
GROUP BY s.region
ORDER BY net_revenue DESC;


SELECT 
    cat.category_name,
    COUNT(DISTINCT fs.sale_id) AS total_transactions,
    SUM(fs.quantity) AS total_units_sold,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price))::numeric, 2) AS gross_revenue,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))::numeric, 2) AS net_revenue,
    ROUND((AVG(COALESCE(fs.discount_pct, 0)) * 100)::numeric, 2) AS avg_discount_pct,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * COALESCE(fs.discount_pct, 0))::numeric, 2) AS total_discount_value
FROM fact_sales fs
JOIN dim_products dp    ON fs.product_id = dp.product_id
JOIN dim_categories cat ON dp.category_id = cat.category_id
GROUP BY cat.category_name
ORDER BY net_revenue DESC;
