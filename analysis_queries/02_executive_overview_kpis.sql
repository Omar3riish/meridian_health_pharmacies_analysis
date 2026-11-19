
SELECT 
    COUNT(DISTINCT fs.sale_id) AS total_orders,
    COUNT(DISTINCT fs.customer_id) AS unique_customers,
    SUM(fs.quantity) AS total_units_sold,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price))::numeric, 2) AS total_gross_revenue,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))::numeric, 2) AS total_net_revenue,
    ROUND(SUM(fs.quantity * COALESCE(dp.cost_price, 0))::numeric, 2) AS total_cost,
    ROUND((
        SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))
        - SUM(fs.quantity * COALESCE(dp.cost_price, 0))
    )::numeric, 2) AS total_net_profit,
    ROUND((
        (SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))
         - SUM(fs.quantity * COALESCE(dp.cost_price, 0)))
        / NULLIF(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))), 0) * 100
    )::numeric, 2) AS profit_margin_pct,
    ROUND(AVG(fs.quantity * COALESCE(fs.unit_price, dp.unit_price))::numeric, 2) AS gross_avg_order_value,
    ROUND(AVG(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))::numeric, 2) AS net_avg_order_value
FROM fact_sales fs
JOIN dim_products dp ON fs.product_id = dp.product_id;


SELECT 
    TO_CHAR(fs.sale_date, 'YYYY-MM') AS sales_month,
    COUNT(DISTINCT fs.sale_id) AS total_transactions,
    SUM(fs.quantity) AS total_units_sold,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price))::numeric, 2) AS gross_revenue,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))::numeric, 2) AS net_revenue,
    ROUND(SUM(fs.quantity * COALESCE(dp.cost_price, 0))::numeric, 2) AS total_cost,
    ROUND((
        SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))
        - SUM(fs.quantity * COALESCE(dp.cost_price, 0))
    )::numeric, 2) AS net_profit,
    ROUND((
        (SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))
         - SUM(fs.quantity * COALESCE(dp.cost_price, 0)))
        / NULLIF(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))), 0) * 100
    )::numeric, 2) AS profit_margin_pct
FROM fact_sales fs
JOIN dim_products dp ON fs.product_id = dp.product_id
WHERE fs.sale_date IS NOT NULL
GROUP BY sales_month
ORDER BY sales_month ASC;


SELECT 
    TO_CHAR(fs.sale_date, 'YYYY') AS sales_year,
    COUNT(DISTINCT fs.sale_id) AS total_transactions,
    SUM(fs.quantity) AS total_units_sold,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price))::numeric, 2) AS gross_revenue,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))::numeric, 2) AS net_revenue,
    ROUND(SUM(fs.quantity * COALESCE(dp.cost_price, 0))::numeric, 2) AS total_cost,
    ROUND((
        SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))
        - SUM(fs.quantity * COALESCE(dp.cost_price, 0))
    )::numeric, 2) AS total_profit,
    ROUND((
        (SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))
         - SUM(fs.quantity * COALESCE(dp.cost_price, 0)))
        / NULLIF(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))), 0) * 100
    )::numeric, 2) AS profit_margin_pct
FROM fact_sales fs
JOIN dim_products dp ON fs.product_id = dp.product_id
WHERE fs.sale_date IS NOT NULL
GROUP BY sales_year
ORDER BY sales_year ASC;


SELECT 
    c.category_name,
    SUM(fs.quantity) AS units_sold,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))::numeric, 2) AS net_revenue,
    ROUND((AVG(COALESCE(fs.discount_pct, 0)) * 100)::numeric, 2) AS avg_discount_pct
FROM fact_sales fs
JOIN dim_products dp   ON fs.product_id = dp.product_id
JOIN dim_categories c  ON dp.category_id = c.category_id
GROUP BY c.category_name
ORDER BY net_revenue DESC;

SELECT 
    st.store_name,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))::numeric, 2) AS net_revenue
FROM fact_sales fs
JOIN dim_stores st   ON fs.store_id = st.store_id
JOIN dim_products dp ON fs.product_id = dp.product_id
GROUP BY st.store_name
ORDER BY net_revenue DESC;
