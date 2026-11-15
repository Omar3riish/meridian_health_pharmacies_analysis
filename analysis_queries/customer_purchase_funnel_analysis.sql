WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(DISTINCT sale_id) AS total_orders
    FROM fact_sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),

funnel_stages AS (
    SELECT
        1 AS stage_order,
        'First Purchase' AS funnel_stage,
        COUNT(*) AS customers
    FROM customer_orders
    WHERE total_orders >= 1

    UNION ALL

    SELECT
        2,
        'Repeat Purchase',
        COUNT(*)
    FROM customer_orders
    WHERE total_orders >= 2

    UNION ALL

    SELECT
        3,
        'Loyal Customer (5+ Orders)',
        COUNT(*)
    FROM customer_orders
    WHERE total_orders >= 5
),

funnel_metrics AS (
    SELECT
        *,
        LAG(customers) OVER (
            ORDER BY stage_order
        ) AS previous_stage_customers,

        FIRST_VALUE(customers) OVER (
            ORDER BY stage_order
        ) AS initial_customers

    FROM funnel_stages
)

SELECT
    stage_order,
    funnel_stage,
    customers,

    ROUND(
        100.0 * customers /
        NULLIF(previous_stage_customers, 0),
        2
    ) AS conversion_from_previous_pct,

    ROUND(
        100.0 * customers /
        NULLIF(initial_customers, 0),
        2
    ) AS overall_conversion_pct,

    previous_stage_customers - customers AS customer_dropoff

FROM funnel_metrics
ORDER BY stage_order;









WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(DISTINCT sale_id) AS total_orders
    FROM fact_sales
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),

funnel AS (
    SELECT
        COUNT(*) FILTER (
            WHERE total_orders >= 1
        ) AS first_purchase,

        COUNT(*) FILTER (
            WHERE total_orders >= 2
        ) AS repeat_purchase,

        COUNT(*) FILTER (
            WHERE total_orders >= 5
        ) AS loyal_customers

    FROM customer_orders
)

SELECT
    'First to Repeat Purchase' AS transition,

    first_purchase AS starting_customers,
    repeat_purchase AS converted_customers,

    first_purchase - repeat_purchase AS dropped_customers,

    ROUND(
        100.0 * (first_purchase - repeat_purchase) /
        NULLIF(first_purchase, 0),
        2
    ) AS dropoff_rate_pct

FROM funnel

UNION ALL

SELECT
    'Repeat to Loyal Customer',

    repeat_purchase,
    loyal_customers,

    repeat_purchase - loyal_customers,

    ROUND(
        100.0 * (repeat_purchase - loyal_customers) /
        NULLIF(repeat_purchase, 0),
        2
    )

FROM funnel;












WITH customer_metrics AS (
    SELECT
        customer_id,

        COUNT(DISTINCT sale_id) AS total_orders,

        SUM(
            quantity * unit_price *
            (1 - COALESCE(discount_pct, 0))
        ) AS total_revenue

    FROM fact_sales

    WHERE customer_id IS NOT NULL

    GROUP BY customer_id
),

customer_groups AS (
    SELECT
        customer_id,
        total_orders,
        total_revenue,

        CASE
            WHEN total_orders = 1
                THEN 'One-Time Customers'

            WHEN total_orders BETWEEN 2 AND 4
                THEN 'Repeat Customers'

            WHEN total_orders >= 5
                THEN 'Loyal Customers'
        END AS customer_group

    FROM customer_metrics
)

SELECT
    customer_group,

    COUNT(*) AS total_customers,

    SUM(total_orders) AS total_orders,

    ROUND(SUM(total_revenue)::numeric, 2)
        AS total_revenue,

    ROUND(AVG(total_revenue)::numeric, 2)
        AS avg_revenue_per_customer,

    ROUND(
        100.0 * SUM(total_revenue) /
        NULLIF(SUM(SUM(total_revenue)) OVER (), 0),
        2
    ) AS revenue_contribution_pct

FROM customer_groups

GROUP BY customer_group

ORDER BY
    CASE customer_group
        WHEN 'One-Time Customers' THEN 1
        WHEN 'Repeat Customers' THEN 2
        WHEN 'Loyal Customers' THEN 3
    END;
















	WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(DISTINCT sale_id) AS total_orders,

        SUM(
            quantity * unit_price *
            (1 - COALESCE(discount_pct, 0))
        ) AS total_revenue,

        MIN(sale_date) AS first_purchase

    FROM fact_sales

    WHERE customer_id IS NOT NULL

    GROUP BY customer_id
),

monthly_cohorts AS (
    SELECT
        DATE_TRUNC('month', first_purchase) AS cohort_month,

        COUNT(*) AS acquired_customers,

        COUNT(*) FILTER (
            WHERE total_orders >= 2
        ) AS repeat_customers,

        COUNT(*) FILTER (
            WHERE total_orders >= 5
        ) AS loyal_customers

    FROM customer_orders

    GROUP BY DATE_TRUNC('month', first_purchase)
)

SELECT
    cohort_month,

    acquired_customers,

    repeat_customers,

    loyal_customers,

    ROUND(
        100.0 * repeat_customers /
        NULLIF(acquired_customers, 0),
        2
    ) AS repeat_conversion_pct,

    ROUND(
        100.0 * loyal_customers /
        NULLIF(acquired_customers, 0),
        2
    ) AS loyal_conversion_pct

FROM monthly_cohorts

ORDER BY cohort_month;











WITH ranked_orders AS (
    SELECT
        customer_id,
        sale_id,
        sale_date,

        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY sale_date, sale_id
        ) AS order_rank

    FROM fact_sales

    WHERE customer_id IS NOT NULL
),

purchase_intervals AS (
    SELECT
        first_order.customer_id,

        first_order.sale_date AS first_purchase,

        second_order.sale_date AS second_purchase,

        second_order.sale_date -
        first_order.sale_date AS days_to_return

    FROM ranked_orders first_order

    JOIN ranked_orders second_order
        ON first_order.customer_id = second_order.customer_id

    WHERE first_order.order_rank = 1
      AND second_order.order_rank = 2
)

SELECT
    COUNT(*) AS returning_customers,

    ROUND(
        AVG(days_to_return), 2
    ) AS avg_days_to_return,

    PERCENTILE_CONT(0.5)
        WITHIN GROUP (ORDER BY days_to_return)
        AS median_days_to_return,

    MIN(days_to_return) AS fastest_return_days,

    MAX(days_to_return) AS slowest_return_days

FROM purchase_intervals;









WITH ranked_orders AS (
    SELECT
        customer_id,
        sale_date,

        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY sale_date, sale_id
        ) AS order_rank

    FROM fact_sales

    WHERE customer_id IS NOT NULL
),

purchase_intervals AS (
    SELECT
        first_order.customer_id,

        second_order.sale_date -
        first_order.sale_date AS days_to_return

    FROM ranked_orders first_order

    JOIN ranked_orders second_order
        ON first_order.customer_id = second_order.customer_id

    WHERE first_order.order_rank = 1
      AND second_order.order_rank = 2
),

return_buckets AS (
    SELECT
        customer_id,

        CASE
            WHEN days_to_return <= 7
                THEN 'Within 7 Days'

            WHEN days_to_return <= 30
                THEN '8-30 Days'

            WHEN days_to_return <= 60
                THEN '31-60 Days'

            WHEN days_to_return <= 90
                THEN '61-90 Days'

            ELSE 'More Than 90 Days'
        END AS return_period

    FROM purchase_intervals
)

SELECT
    return_period,

    COUNT(*) AS customers,

    ROUND(
        100.0 * COUNT(*) /
        NULLIF(SUM(COUNT(*)) OVER (), 0),
        2
    ) AS percentage

FROM return_buckets

GROUP BY return_period

ORDER BY
    CASE return_period
        WHEN 'Within 7 Days' THEN 1
        WHEN '8-30 Days' THEN 2
        WHEN '31-60 Days' THEN 3
        WHEN '61-90 Days' THEN 4
        ELSE 5
    END;