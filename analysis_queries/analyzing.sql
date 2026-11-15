SELECT 
    SUM(fs.quantity * dp.unit_price) AS total_gross_revenue,
    
    SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))) AS total_net_revenue,
    
    SUM(fs.quantity * dp.cost_price) AS total_cost,
    
    SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))) - SUM(fs.quantity * dp.cost_price) AS total_net_profit,
    
    ROUND(
        ((SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))) - SUM(fs.quantity * dp.cost_price)) / 
        NULLIF(SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))), 0)) * 100, 2
    ) AS overall_profit_margin_pct

FROM fact_sales fs
JOIN dim_products dp ON fs.product_id = dp.product_id;





/*1.Which stores are genuinely profitable after cost and discount adjustments? */

SELECT 
    st.store_id,
    st.store_name,
    st.city,
    st.region,
    SUM(fs.quantity * dp.unit_price) AS gross_revenue,
    
    SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))) AS net_revenue,
    
    SUM(fs.quantity * dp.cost_price) AS total_cost,
    
    SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))) - SUM(fs.quantity * dp.cost_price) AS net_profit,
    
    ROUND(
        ((SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))) - SUM(fs.quantity * dp.cost_price)) / 
        NULLIF(SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))), 0)) * 100, 2
    ) AS profit_margin_pct

FROM fact_sales fs
JOIN dim_stores st ON fs.store_id = st.store_id
JOIN dim_products dp ON fs.product_id = dp.product_id
GROUP BY st.store_id, st.store_name, st.city, st.region
ORDER BY profit_margin_pct DESC;




/*2.Which product categories drive revenue — and which are over-discounted? */
SELECT 
    cat.category_name,
    
    TO_CHAR(COUNT(fs.sale_id), 'FM999,999,990') AS total_transactions,
    TO_CHAR(SUM(fs.quantity), 'FM999,999,990') AS total_units_sold,
    
    TO_CHAR(SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))), 'FM999,999,990.00') AS total_net_revenue,
    
    ROUND(AVG(COALESCE(fs.discount_pct, 0)) * 100, 2) || '%' AS avg_discount_pct,
    
    TO_CHAR(SUM((fs.quantity * dp.unit_price) * COALESCE(fs.discount_pct, 0)), 'FM999,999,990.00') AS total_discount_value

FROM fact_sales fs
JOIN dim_products dp ON fs.product_id = dp.product_id
JOIN dim_categories cat ON dp.category_id = cat.category_id
GROUP BY cat.category_name
ORDER BY SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))) DESC;

