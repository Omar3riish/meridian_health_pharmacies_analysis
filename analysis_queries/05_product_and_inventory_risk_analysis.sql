
SELECT 
    SUM(sl.quantity) AS total_stock_units,
    ROUND(SUM(sl.quantity * COALESCE(dp.cost_price, 0))::numeric, 2) AS inventory_at_cost,
    ROUND(SUM(sl.quantity * COALESCE(dp.unit_price, 0))::numeric, 2) AS inventory_at_retail,
    COUNT(*) FILTER (WHERE sl.shelf_life_status IN ('Critical Danger', 'Expired on Receipt')) AS critical_or_expired_batches,
    COUNT(*) FILTER (WHERE sl.is_below_reorder_level = TRUE OR sl.quantity < sl.reorder_level) AS below_reorder_batches
FROM fact_stock_log sl
JOIN dim_products dp ON sl.product_id = dp.product_id;


SELECT 
    sl.shelf_life_status,
    COUNT(*) AS total_batches,
    SUM(sl.quantity) AS total_quantity,
    ROUND(SUM(sl.quantity * COALESCE(dp.unit_price, 0))::numeric, 2) AS total_retail_value,
    ROUND(SUM(sl.quantity * COALESCE(dp.cost_price, 0))::numeric, 2) AS total_cost_value
FROM fact_stock_log sl
JOIN dim_products dp ON sl.product_id = dp.product_id
GROUP BY sl.shelf_life_status
ORDER BY total_cost_value DESC;


SELECT 
    st.store_id,
    st.store_name,
    sl.shelf_life_status,
    COUNT(*) AS batches_at_risk,
    SUM(sl.quantity) AS total_quantity_at_risk,
    ROUND(SUM(sl.quantity * COALESCE(dp.cost_price, 0))::numeric, 2) AS cost_value_at_risk
FROM fact_stock_log sl
JOIN dim_products dp     ON sl.product_id = dp.product_id
LEFT JOIN dim_stores st  ON sl.store_id = st.store_id
WHERE sl.shelf_life_status IN ('Expired on Receipt', 'Critical Danger', 'High Risk - Monitor')
GROUP BY st.store_id, st.store_name, sl.shelf_life_status
ORDER BY st.store_name, total_quantity_at_risk DESC;


SELECT 
    sl.batch_number,
    dp.product_name,
    st.store_name,
    sl.quantity AS current_stock,
    sl.reorder_level,
    (sl.reorder_level - sl.quantity) AS units_short,
    sl.expiry_date,
    sl.shelf_life_status,
    sl.condition_notes
FROM fact_stock_log sl
JOIN dim_products dp    ON sl.product_id = dp.product_id
LEFT JOIN dim_stores st ON sl.store_id = st.store_id
WHERE sl.is_below_reorder_level = TRUE
   OR sl.quantity < sl.reorder_level
ORDER BY sl.expiry_date ASC NULLS LAST, units_short DESC;


WITH product_sales AS (
    SELECT
        fs.product_id,
        SUM(fs.quantity) AS units_sold,
        SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))) AS net_revenue,
        SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))
          - SUM(fs.quantity * COALESCE(dp.cost_price, 0)) AS net_profit
    FROM fact_sales fs
    JOIN dim_products dp ON fs.product_id = dp.product_id
    GROUP BY fs.product_id
),
product_stock AS (
    SELECT
        product_id,
        SUM(quantity) AS stock_units
    FROM fact_stock_log
    GROUP BY product_id
)
SELECT
    dp.product_id,
    dp.product_name,
    COALESCE(ps.units_sold, 0) AS units_sold,
    COALESCE(pi.stock_units, 0) AS current_stock_units,
    ROUND((COALESCE(ps.units_sold, 0)::numeric / NULLIF(pi.stock_units, 0)), 2) AS turnover_proxy,
    ROUND(COALESCE(ps.net_revenue, 0)::numeric, 2) AS net_revenue,
    ROUND(COALESCE(ps.net_profit, 0)::numeric, 2) AS net_profit,
    ROUND((COALESCE(ps.net_profit, 0) / NULLIF(ps.net_revenue, 0) * 100)::numeric, 2) AS profit_margin_pct
FROM dim_products dp
LEFT JOIN product_sales ps ON dp.product_id = ps.product_id
LEFT JOIN product_stock pi ON dp.product_id = pi.product_id
WHERE COALESCE(ps.net_revenue, 0) > 0
ORDER BY net_profit DESC;
