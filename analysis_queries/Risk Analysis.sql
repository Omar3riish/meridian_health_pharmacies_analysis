SELECT 
    st.store_id,
	st.store_name,
    sl.shelf_life_status,
    COUNT(sl.product_id) AS total_items,
    SUM(sl.quantity) AS total_quantity_at_risk
FROM fact_stock_log sl
JOIN fact_sales fs ON sl.product_id = fs.product_id
JOIN dim_stores st ON fs.store_id = st.store_id
WHERE sl.shelf_life_status IN ('Expired on Receipt', 'Critical Danger', 'High Risk - Monitor')
GROUP BY st.store_id, st.store_name, sl.shelf_life_status
ORDER BY st.store_name, total_quantity_at_risk DESC;



SELECT 
    sl.shelf_life_status,
    TO_CHAR(COUNT(sl.product_id), 'FM999,999,990') AS total_tracked_items,
    TO_CHAR(SUM(sl.quantity), 'FM999,999,990') AS total_quantity,
    TO_CHAR(SUM(sl.quantity * dp.unit_price), 'FM999,999,990.00') AS total_retail_value,
    TO_CHAR(SUM(sl.quantity * dp.cost_price), 'FM999,999,990.00') AS total_cost_value
FROM fact_stock_log sl
JOIN dim_products dp ON sl.product_id = dp.product_id
GROUP BY sl.shelf_life_status
ORDER BY SUM(sl.quantity * dp.cost_price) DESC;