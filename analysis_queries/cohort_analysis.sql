WITH customer_regions AS (
    SELECT DISTINCT ON (fs.customer_id)
        fs.customer_id,
        ds.region
    FROM fact_sales fs
    JOIN dim_stores ds ON fs.store_id = ds.store_id
    WHERE fs.customer_id IS NOT NULL
    ORDER BY fs.customer_id, fs.sale_date, fs.sale_id
),

transaction_level AS (
    SELECT
        customer_id,
        sale_id,
        MIN(sale_date) AS sale_date,
        SUM(
            quantity * unit_price *
            (1 - COALESCE(discount_pct, 0))
        ) AS revenue
    FROM fact_sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id, sale_id
),

ranked_purchases AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY sale_date, sale_id
        ) AS purchase_rank
    FROM transaction_level
),

first_purchase AS (
    SELECT
        customer_id,
        sale_id
    FROM ranked_purchases
    WHERE purchase_rank = 1
),

customer_metrics AS (
    SELECT
        customer_id,
        COUNT(*)        AS total_orders,
        SUM(revenue)    AS total_revenue
    FROM transaction_level
    GROUP BY customer_id
)

SELECT
    COALESCE(r.region, 'Unknown')                                   AS geographic_cohort,
    COUNT(*)                                                        AS total_customers,
    COUNT(*) FILTER (WHERE m.total_orders >= 2)                     AS repeat_customers,
    ROUND(
        COUNT(*) FILTER (WHERE m.total_orders >= 2) * 100.0
        / NULLIF(COUNT(*), 0),
        2
    )                                                               AS repeat_rate_pct,
    ROUND(AVG(m.total_orders)::numeric, 2)                          AS avg_orders,
    ROUND(SUM(m.total_revenue)::numeric, 2)                         AS total_revenue,
    ROUND(AVG(m.total_revenue)::numeric, 2)                         AS revenue_per_customer
FROM customer_metrics m
LEFT JOIN customer_regions r ON m.customer_id = r.customer_id
GROUP BY r.region
ORDER BY total_revenue DESC;






WITH transaction_level AS (
    SELECT
        customer_id,
        sale_id,
        MIN(sale_date) AS sale_date,
        SUM(
            quantity * unit_price *
            (1 - COALESCE(discount_pct, 0))
        ) AS revenue
    FROM fact_sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id, sale_id
),

customer_metrics AS (
    SELECT
        customer_id,
        COUNT(*)     AS total_orders,
        SUM(revenue) AS total_revenue
    FROM transaction_level
    GROUP BY customer_id
)

SELECT
    COALESCE(c.customer_segment, 'Unknown')                         AS customer_type_cohort,
    COUNT(*)                                                        AS total_customers,
    COUNT(*) FILTER (WHERE m.total_orders >= 2)                     AS repeat_customers,
    ROUND(
        COUNT(*) FILTER (WHERE m.total_orders >= 2) * 100.0
        / NULLIF(COUNT(*), 0),
        2
    )                                                               AS repeat_rate_pct,
    ROUND(AVG(m.total_orders)::numeric, 2)                          AS avg_orders,
    ROUND(SUM(m.total_revenue)::numeric, 2)                         AS total_revenue,
    ROUND(AVG(m.total_revenue)::numeric, 2)                         AS revenue_per_customer
FROM customer_metrics m
LEFT JOIN dim_customers c
       ON m.customer_id = c.customer_id
WHERE c.customer_segment IN ('Gold', 'Silver', 'Platinum', 'Others')
   OR c.customer_segment IS NULL        
GROUP BY c.customer_segment
ORDER BY total_revenue DESC;







WITH transaction_level AS (
    SELECT
        customer_id,
        sale_id,
        MIN(sale_date) AS sale_date,
        MIN(payment_method) AS payment_method,
        SUM(
            quantity * unit_price *
            (1 - COALESCE(discount_pct, 0))
        ) AS revenue
    FROM fact_sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id, sale_id
),

ranked_purchases AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY sale_date, sale_id
        ) AS purchase_rank
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
    COUNT(*) FILTER (
        WHERE m.total_orders >= 2
    ) AS repeat_customers,
    ROUND(
        COUNT(*) FILTER (
            WHERE m.total_orders >= 2
        ) * 100.0 / NULLIF(COUNT(*), 0),
        2
    ) AS repeat_rate_pct,
    ROUND(AVG(m.total_orders)::numeric, 2) AS avg_orders,
    ROUND(SUM(m.total_revenue)::numeric, 2) AS total_revenue,
    ROUND(AVG(m.total_revenue)::numeric, 2) AS revenue_per_customer
FROM first_payment f
JOIN customer_metrics m USING (customer_id)
GROUP BY f.payment_cohort
ORDER BY total_revenue DESC;