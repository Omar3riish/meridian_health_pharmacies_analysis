
WITH analysis_date AS (
    SELECT MAX(sale_date) AS max_date FROM fact_sales
),
customer_rfm AS (
    SELECT
        customer_id,
        MAX(sale_date) AS last_purchase,
        COUNT(DISTINCT sale_id) AS frequency,
        SUM(quantity * unit_price * (1 - COALESCE(discount_pct, 0))) AS monetary
    FROM fact_sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),
rfm AS (
    SELECT
        c.customer_id,
        (a.max_date - c.last_purchase) AS recency,
        c.frequency,
        c.monetary
    FROM customer_rfm c
    CROSS JOIN analysis_date a
),
rfm_scores AS (
    SELECT
        customer_id,
        recency,
        frequency,
        monetary,
        NTILE(5) OVER (ORDER BY recency DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM rfm
),
customer_segments AS (
    SELECT
        customer_id,
        recency,
        frequency,
        monetary,
        r_score,
        f_score,
        m_score,
        ROUND(((r_score + f_score + m_score) / 3.0)::numeric, 2) AS avg_rfm_score,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 4                  THEN 'Loyal Customers'
            WHEN r_score >= 4 AND f_score >= 2                  THEN 'Potential Loyalists'
            WHEN r_score >= 4 AND f_score = 1                   THEN 'New Customers'
            WHEN r_score <= 2 AND f_score >= 3                  THEN 'At Risk'
            WHEN r_score <= 2 AND f_score = 2                   THEN 'Hibernating'
            ELSE 'Lost Customers'
        END AS rfm_segment
    FROM rfm_scores
)
SELECT
    rfm_segment,
    COUNT(*) AS customers,
    ROUND(SUM(monetary)::numeric, 2) AS net_revenue,
    ROUND((COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0))::numeric, 2) AS customer_share_pct,
    ROUND((SUM(monetary) * 100.0 / NULLIF(SUM(SUM(monetary)) OVER (), 0))::numeric, 2) AS revenue_share_pct,
    ROUND(AVG(monetary)::numeric, 2) AS avg_revenue_per_customer
FROM customer_segments
GROUP BY rfm_segment
ORDER BY net_revenue DESC;


SELECT
    COALESCE(c.customer_segment, 'Others') AS customer_segment,
    COUNT(DISTINCT fs.customer_id) AS unique_customers,
    COUNT(DISTINCT fs.sale_id) AS total_transactions,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price))::numeric, 2) AS gross_revenue,
    ROUND(SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))::numeric, 2) AS net_revenue,
    ROUND((
        SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))
        - SUM(fs.quantity * COALESCE(dp.cost_price, 0))
    )::numeric, 2) AS net_profit,
    ROUND((AVG(COALESCE(fs.discount_pct, 0)) * 100)::numeric, 2) AS avg_discount_pct,
    ROUND((
        SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))
        / NULLIF(COUNT(DISTINCT fs.customer_id), 0)
    )::numeric, 2) AS observed_clv_per_customer,
    ROUND((
        SUM(fs.quantity * COALESCE(fs.unit_price, dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))
        / NULLIF(COUNT(DISTINCT fs.sale_id), 0)
    )::numeric, 2) AS avg_order_value
FROM fact_sales fs
JOIN dim_products dp  ON fs.product_id = dp.product_id
JOIN dim_customers c  ON fs.customer_id = c.customer_id
GROUP BY COALESCE(c.customer_segment, 'Others')
ORDER BY net_revenue DESC;


WITH customer_first_purchase AS (
    SELECT
        customer_id,
        MIN(sale_date) AS first_date
    FROM fact_sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),
tagged_sales AS (
    SELECT
        fs.sale_id,
        fs.customer_id,
        CASE WHEN fs.sale_date = cfp.first_date THEN 'New' ELSE 'Returning' END AS customer_type,
        (fs.quantity * fs.unit_price * (1 - COALESCE(fs.discount_pct, 0))) AS net_revenue
    FROM fact_sales fs
    JOIN customer_first_purchase cfp ON fs.customer_id = cfp.customer_id
)
SELECT
    customer_type,
    COUNT(DISTINCT customer_id) AS customers,
    COUNT(DISTINCT sale_id) AS orders,
    ROUND(SUM(net_revenue)::numeric, 2) AS net_revenue,
    ROUND((SUM(net_revenue) / NULLIF(COUNT(DISTINCT sale_id), 0))::numeric, 2) AS aov,
    ROUND((SUM(net_revenue) / NULLIF(COUNT(DISTINCT customer_id), 0))::numeric, 2) AS revenue_per_customer
FROM tagged_sales
GROUP BY customer_type
ORDER BY net_revenue DESC;
