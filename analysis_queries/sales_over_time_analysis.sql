SELECT 
    TO_CHAR(fs.sale_date, 'YYYY-MM') AS sales_month,
    
    TO_CHAR(COUNT(fs.sale_id), 'FM999,999,990') AS total_transactions,
    TO_CHAR(SUM(fs.quantity), 'FM999,999,990') AS total_units_sold,
    
    TO_CHAR(SUM(fs.quantity * dp.unit_price), 'FM999,999,990.00') AS gross_revenue,
    TO_CHAR(SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))), 'FM999,999,990.00') AS net_revenue

FROM fact_sales fs
JOIN dim_products dp ON fs.product_id = dp.product_id
WHERE fs.sale_date IS NOT NULL
GROUP BY sales_month
ORDER BY sales_month ASC;


SELECT 
    TO_CHAR(fs.sale_date, 'YYYY') AS sales_year,
    
    TO_CHAR(COUNT(fs.sale_id), 'FM999,999,990') AS total_transactions,
    TO_CHAR(SUM(fs.quantity), 'FM999,999,990') AS total_units_sold,
    
    TO_CHAR(SUM(fs.quantity * dp.unit_price), 'FM999,999,990.00') AS gross_revenue,
    TO_CHAR(SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))), 'FM999,999,990.00') AS net_revenue

FROM fact_sales fs
JOIN dim_products dp ON fs.product_id = dp.product_id
WHERE fs.sale_date IS NOT NULL
GROUP BY sales_year
ORDER BY sales_year ASC;


SELECT 
    TO_CHAR(fs.sale_date, 'YYYY') AS sales_year,
    
    TO_CHAR(SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))), 'FM999,999,990.00') AS total_sales,
    
    TO_CHAR(SUM(fs.quantity * dp.cost_price), 'FM999,999,990.00') AS total_cost,
    
    TO_CHAR(
        SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))) - SUM(fs.quantity * dp.cost_price), 
        'FM999,999,990.00'
    ) AS total_profit,
    
    ROUND(
        ((SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))) - SUM(fs.quantity * dp.cost_price)) / 
        NULLIF(SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0))), 0)) * 100, 2
    ) || '%' AS profit_margin_pct

FROM fact_sales fs
JOIN dim_products dp ON fs.product_id = dp.product_id
WHERE fs.sale_date IS NOT NULL
GROUP BY sales_year
ORDER BY sales_year ASC;