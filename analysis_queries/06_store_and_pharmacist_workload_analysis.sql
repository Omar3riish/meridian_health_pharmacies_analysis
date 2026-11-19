

WITH StoreSales AS (
    SELECT
        fs.store_id,
        COUNT(DISTINCT fs.customer_id) AS unique_customers,
        ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price))::numeric, 2) AS gross_revenue,
        ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))::numeric, 2) AS net_revenue,
        ROUND(SUM(fs.quantity * COALESCE(dp.cost_price, 0))::numeric, 2) AS total_cost,
        ROUND((
            SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))
            - SUM(fs.quantity * COALESCE(dp.cost_price, 0))
        )::numeric, 2) AS net_profit
    FROM fact_sales fs
    JOIN dim_products dp ON fs.product_id = dp.product_id
    GROUP BY fs.store_id
),
StorePayroll AS (
    SELECT 
        store_id,
        SUM(salary) AS total_payroll,
        COUNT(employee_id) AS total_staff_count,
        COUNT(CASE WHEN is_pharmacist = TRUE THEN 1 END) AS pharmacist_count
    FROM dim_employees
    GROUP BY store_id
),
StoreWorkload AS (
    SELECT 
        store_id,
        COUNT(prescription_id) AS total_prescriptions
    FROM fact_prescriptions
    GROUP BY store_id
)
SELECT 
    st.store_id,
    st.store_name,
    st.city,
    st.region,
    COALESCE(ss.unique_customers, 0) AS unique_customers,
    COALESCE(ss.gross_revenue, 0) AS gross_revenue,
    COALESCE(ss.net_revenue, 0) AS net_revenue,
    COALESCE(ss.total_cost, 0) AS total_cost,
    COALESCE(ss.net_profit, 0) AS net_profit,
    ROUND((COALESCE(ss.net_profit, 0) / NULLIF(ss.net_revenue, 0) * 100)::numeric, 2) AS profit_margin_pct,
    COALESCE(sp.total_staff_count, 0) AS total_staff_count,
    COALESCE(sp.pharmacist_count, 0) AS pharmacist_count,
    ROUND(COALESCE(sp.total_payroll, 0)::numeric, 2) AS total_store_payroll,
    COALESCE(sw.total_prescriptions, 0) AS total_prescriptions,
    ROUND((
        COALESCE(sw.total_prescriptions, 0)::numeric / NULLIF(sp.pharmacist_count, 0)
    ), 2) AS prescriptions_per_pharmacist,
    ROUND((
        COALESCE(sp.total_payroll, 0)::numeric / NULLIF(sw.total_prescriptions, 0)
    ), 2) AS labor_cost_per_prescription
FROM dim_stores st
LEFT JOIN StoreSales ss    ON st.store_id = ss.store_id
LEFT JOIN StorePayroll sp  ON st.store_id = sp.store_id
LEFT JOIN StoreWorkload sw ON st.store_id = sw.store_id
ORDER BY net_profit DESC;
