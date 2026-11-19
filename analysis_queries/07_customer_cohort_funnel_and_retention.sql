
WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(DISTINCT sale_id) AS total_orders,
        SUM(quantity * unit_price * (1 - COALESCE(discount_pct, 0))) AS total_revenue,
        MIN(sale_date) AS first_purchase
    FROM fact_sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT
    TO_CHAR(DATE_TRUNC('month', first_purchase), 'YYYY-MM') AS cohort_month,
    COUNT(*) AS acquired_customers,
    COUNT(*) FILTER (WHERE total_orders >= 2) AS repeat_customers,
    COUNT(*) FILTER (WHERE total_orders >= 5) AS loyal_customers,
    ROUND((COUNT(*) FILTER (WHERE total_orders >= 2) * 100.0 / NULLIF(COUNT(*), 0))::numeric, 2) AS repeat_conversion_pct,
    ROUND((COUNT(*) FILTER (WHERE total_orders >= 5) * 100.0 / NULLIF(COUNT(*), 0))::numeric, 2) AS loyal_conversion_pct
FROM customer_orders
GROUP BY DATE_TRUNC('month', first_purchase)
ORDER BY cohort_month ASC;


WITH customer_regions AS (
    SELECT DISTINCT ON (fs.customer_id)
        fs.customer_id,
        ds.region
    FROM fact_sales fs
    JOIN dim_stores ds ON fs.store_id = ds.store_id
    WHERE fs.customer_id IS NOT NULL
    ORDER BY fs.customer_id, fs.sale_date, fs.sale_id
),
customer_metrics AS (
    SELECT
        customer_id,
        COUNT(DISTINCT sale_id) AS total_orders,
        SUM(quantity * unit_price * (1 - COALESCE(discount_pct, 0))) AS total_revenue
    FROM fact_sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
)
SELECT
    COALESCE(r.region, 'Unknown') AS geographic_cohort,
    COUNT(*) AS total_customers,
    COUNT(*) FILTER (WHERE m.total_orders >= 2) AS repeat_customers,
    ROUND((COUNT(*) FILTER (WHERE m.total_orders >= 2) * 100.0 / NULLIF(COUNT(*), 0))::numeric, 2) AS repeat_rate_pct,
    ROUND(AVG(m.total_orders)::numeric, 2) AS avg_orders,
    ROUND(SUM(m.total_revenue)::numeric, 2) AS total_revenue,
    ROUND(AVG(m.total_revenue)::numeric, 2) AS revenue_per_customer
FROM customer_metrics m
LEFT JOIN customer_regions r ON m.customer_id = r.customer_id
GROUP BY r.region
ORDER BY total_revenue DESC;


WITH transaction_level AS (
    SELECT
        customer_id,
        sale_id,
        MIN(sale_date) AS sale_date,
        MIN(payment_method) AS payment_method,
        SUM(quantity * unit_price * (1 - COALESCE(discount_pct, 0))) AS revenue
    FROM fact_sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id, sale_id
),
ranked_purchases AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY sale_date, sale_id) AS purchase_rank
    FROM transaction_level
),
first_payment AS (
    SELECT
        customer_id,
        COALESCE(payment_method, 'Unknown') AS payment_cohort
    FROM ranked_purchases
    WHERE purchase_rank = 1
),
customer_metrics AS (
    SELECT
        customer_id,
        COUNT(*) AS total_orders,
        SUM(revenue) AS total_revenue
    FROM transaction_level
    GROUP BY customer_id
)
SELECT
    f.payment_cohort,
    COUNT(*) AS total_customers,
    COUNT(*) FILTER (WHERE m.total_orders >= 2) AS repeat_customers,
    ROUND((COUNT(*) FILTER (WHERE m.total_orders >= 2) * 100.0 / NULLIF(COUNT(*), 0))::numeric, 2) AS repeat_rate_pct,
    ROUND(AVG(m.total_orders)::numeric, 2) AS avg_orders,
    ROUND(SUM(m.total_revenue)::numeric, 2) AS total_revenue,
    ROUND(AVG(m.total_revenue)::numeric, 2) AS revenue_per_customer
FROM first_payment f
JOIN customer_metrics m USING (customer_id)
GROUP BY f.payment_cohort
ORDER BY total_revenue DESC;


WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(DISTINCT sale_id) AS total_orders
    FROM fact_sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),
funnel_stages AS (
    SELECT 1 AS stage_order, 'First Purchase (1+ Order)' AS funnel_stage, COUNT(*) AS customers FROM customer_orders WHERE total_orders >= 1
    UNION ALL
    SELECT 2, 'Repeat Purchase (2+ Orders)', COUNT(*) FROM customer_orders WHERE total_orders >= 2
    UNION ALL
    SELECT 3, 'Loyal Customer (5+ Orders)', COUNT(*) FROM customer_orders WHERE total_orders >= 5
),
funnel_metrics AS (
    SELECT
        *,
        LAG(customers) OVER (ORDER BY stage_order) AS previous_stage_customers,
        FIRST_VALUE(customers) OVER (ORDER BY stage_order) AS initial_customers
    FROM funnel_stages
)
SELECT
    stage_order,
    funnel_stage,
    customers,
    ROUND((100.0 * customers / NULLIF(previous_stage_customers, 0))::numeric, 2) AS conversion_from_previous_pct,
    ROUND((100.0 * customers / NULLIF(initial_customers, 0))::numeric, 2) AS overall_conversion_pct,
    COALESCE(previous_stage_customers - customers, 0) AS customer_dropoff
FROM funnel_metrics
ORDER BY stage_order;


WITH ranked_orders AS (
    SELECT
        customer_id,
        sale_id,
        sale_date,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY sale_date, sale_id) AS order_rank
    FROM fact_sales
    WHERE customer_id IS NOT NULL
),
purchase_intervals AS (
    SELECT
        first_order.customer_id,
        (second_order.sale_date - first_order.sale_date) AS days_to_return
    FROM ranked_orders first_order
    JOIN ranked_orders second_order
        ON first_order.customer_id = second_order.customer_id
    WHERE first_order.order_rank = 1
      AND second_order.order_rank = 2
      AND (second_order.sale_date - first_order.sale_date) >= 0
),
return_buckets AS (
    SELECT
        customer_id,
        days_to_return,
        CASE
            WHEN days_to_return <= 7  THEN 'Within 7 Days'
            WHEN days_to_return <= 30 THEN '8-30 Days'
            WHEN days_to_return <= 60 THEN '31-60 Days'
            WHEN days_to_return <= 90 THEN '61-90 Days'
            ELSE '90+ Days'
        END AS return_period
    FROM purchase_intervals
)
SELECT
    return_period,
    COUNT(*) AS customers,
    ROUND((100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER (), 0))::numeric, 2) AS percentage
FROM return_buckets
GROUP BY return_period
ORDER BY
    CASE return_period
        WHEN 'Within 7 Days' THEN 1
        WHEN '8-30 Days'     THEN 2
        WHEN '31-60 Days'    THEN 3
        WHEN '61-90 Days'    THEN 4
        ELSE 5
    END;
