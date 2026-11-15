SELECT
    customer_id,
    COUNT(DISTINCT sale_id) AS total_orders,
    SUM(quantity) AS total_quantity,
    SUM(quantity * unit_price) AS total_revenue,
    MIN(sale_date) AS first_purchase,
    MAX(sale_date) AS last_purchase,
    MAX(sale_date) - MIN(sale_date) AS customer_lifespan_days
FROM fact_sales
GROUP BY customer_id
ORDER BY total_revenue DESC;


WITH customer_rfm AS (
    SELECT
        customer_id,

        MAX(sale_date) AS last_purchase,

        COUNT(DISTINCT sale_id) AS frequency,

        SUM(
            quantity * unit_price
            * (1 - COALESCE(discount_pct, 0))
        ) AS monetary

    FROM fact_sales
    GROUP BY customer_id
),

analysis_date AS (
    SELECT MAX(sale_date) AS max_date
    FROM fact_sales
)

SELECT
    r.customer_id,

    a.max_date - r.last_purchase AS recency,

    r.frequency,

    ROUND(r.monetary::numeric, 2) AS monetary

FROM customer_rfm r
CROSS JOIN analysis_date a
ORDER BY r.customer_id;




WITH analysis_date AS (
    SELECT MAX(sale_date) AS max_date
    FROM fact_sales
),

customer_rfm AS (
    SELECT
        customer_id,
        MAX(sale_date) AS last_purchase,
        COUNT(DISTINCT sale_id) AS frequency,

        SUM(
            quantity * unit_price *
            (1 - COALESCE(discount_pct, 0))
        ) AS monetary

    FROM fact_sales
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
)

SELECT
    *,
    r_score + f_score + m_score AS rfm_score

FROM rfm_scores
ORDER BY rfm_score DESC;




WITH customer_rfm AS (
    SELECT
        customer_id,
        MAX(sale_date) AS last_purchase,
        COUNT(DISTINCT sale_id) AS frequency,
        SUM(quantity * unit_price *
            (1 - COALESCE(discount_pct, 0))) AS monetary
    FROM fact_sales
    GROUP BY customer_id
),

rfm AS (
    SELECT
        customer_id,
        (SELECT MAX(sale_date) FROM fact_sales)
            - last_purchase AS recency,
        frequency,
        monetary
    FROM customer_rfm
),

rfm_scores AS (
    SELECT
        *,
        NTILE(5) OVER (ORDER BY recency DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM rfm
),

final_segments AS (
    SELECT
        *,
        r_score + f_score + m_score AS rfm_score,

        CASE
            WHEN r_score >= 4 AND f_score >= 4
                THEN 'Champions'

            WHEN r_score >= 3 AND f_score >= 4
                THEN 'Loyal Customers'

            WHEN r_score >= 4 AND f_score BETWEEN 2 AND 3
                THEN 'Potential Loyalists'

            WHEN r_score = 5 AND f_score = 1
                THEN 'New Customers'

            WHEN r_score BETWEEN 2 AND 3 AND f_score >= 3
                THEN 'At Risk'

            WHEN r_score = 1 AND f_score >= 2
                THEN 'Hibernating'

            ELSE 'Lost Customers'
        END AS customer_segment

    FROM rfm_scores
)

SELECT *
FROM final_segments
ORDER BY rfm_score DESC;








WITH analysis_date AS (
    SELECT MAX(sale_date) AS max_date
    FROM fact_sales
),

customer_rfm AS (
    SELECT
        customer_id,
        MAX(sale_date) AS last_purchase,
        COUNT(DISTINCT sale_id) AS frequency,

        SUM(
            quantity * unit_price *
            (1 - COALESCE(discount_pct, 0))
        ) AS monetary

    FROM fact_sales
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

        CASE
            WHEN r_score >= 4 AND f_score >= 4
                THEN 'Champions'

            WHEN r_score >= 3 AND f_score >= 4
                THEN 'Loyal Customers'

            WHEN r_score >= 4 AND f_score BETWEEN 2 AND 3
                THEN 'Potential Loyalists'

            WHEN r_score = 5 AND f_score = 1
                THEN 'New Customers'

            WHEN r_score BETWEEN 2 AND 3 AND f_score >= 3
                THEN 'At Risk'

            WHEN r_score = 1 AND f_score >= 2
                THEN 'Hibernating'

            ELSE 'Lost Customers'
        END AS customer_segment

    FROM rfm_scores
)

SELECT
    customer_segment,

    COUNT(*) AS total_customers,

    ROUND(
        100.0 * COUNT(*) /
        SUM(COUNT(*)) OVER (),
        2
    ) AS customer_percentage

FROM customer_segments

GROUP BY customer_segment

ORDER BY total_customers DESC;








WITH analysis_date AS (
    SELECT MAX(sale_date) AS max_date
    FROM fact_sales
),

customer_rfm AS (
    SELECT
        customer_id,
        MAX(sale_date) AS last_purchase,
        COUNT(DISTINCT sale_id) AS frequency,

        SUM(
            quantity * unit_price *
            (1 - COALESCE(discount_pct, 0))
        ) AS monetary

    FROM fact_sales
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

        CASE
            WHEN r_score >= 4 AND f_score >= 4
                THEN 'Champions'

            WHEN r_score >= 3 AND f_score >= 4
                THEN 'Loyal Customers'

            WHEN r_score >= 4 AND f_score BETWEEN 2 AND 3
                THEN 'Potential Loyalists'

            WHEN r_score = 5 AND f_score = 1
                THEN 'New Customers'

            WHEN r_score BETWEEN 2 AND 3 AND f_score >= 3
                THEN 'At Risk'

            WHEN r_score = 1 AND f_score >= 2
                THEN 'Hibernating'

            ELSE 'Lost Customers'
        END AS customer_segment

    FROM rfm_scores
)

SELECT
    customer_segment,

    COUNT(*) AS total_customers,

    ROUND(
        SUM(monetary)::numeric, 2
    ) AS total_revenue,

    ROUND(
        AVG(monetary)::numeric, 2
    ) AS avg_customer_revenue,

    ROUND(
        100.0 * SUM(monetary) /
        NULLIF(SUM(SUM(monetary)) OVER (), 0),
        2
    ) AS revenue_contribution_pct

FROM customer_segments

GROUP BY customer_segment

ORDER BY total_revenue DESC;
