SELECT
    c.customer_segment,

    COUNT(DISTINCT fs.customer_id)                          AS unique_customers,
    COUNT(fs.sale_id)                                       AS total_transactions,

    SUM(fs.quantity * dp.unit_price)                        AS gross_revenue,

    SUM((fs.quantity * dp.unit_price)
        * (1 - COALESCE(fs.discount_pct, 0)))               AS net_revenue,

    SUM((fs.quantity * dp.unit_price)
        * (1 - COALESCE(fs.discount_pct, 0)))
      - SUM(fs.quantity * dp.cost_price)                    AS net_profit,

    ROUND(
        (SUM((fs.quantity * dp.unit_price) * (1 - COALESCE(fs.discount_pct, 0)))
         - SUM(fs.quantity * dp.cost_price))
        / NULLIF(SUM((fs.quantity * dp.unit_price)
                     * (1 - COALESCE(fs.discount_pct, 0))), 0) * 100, 2
    )                                                       AS profit_margin_pct,

    ROUND(AVG(COALESCE(fs.discount_pct, 0)) * 100, 2)       AS avg_discount_pct,

    ROUND(
        SUM((fs.quantity * dp.unit_price)
            * (1 - COALESCE(fs.discount_pct, 0)))
        / NULLIF(COUNT(DISTINCT fs.customer_id), 0), 2
    )                                                       AS net_revenue_per_customer,

    ROUND(
        SUM(fs.quantity * dp.unit_price
            * (1 - COALESCE(fs.discount_pct, 0)))
        / NULLIF(COUNT(fs.sale_id), 0), 2
    )                                                       AS avg_order_value

FROM fact_sales fs
JOIN dim_products  dp ON fs.product_id  = dp.product_id
JOIN dim_customers c  ON fs.customer_id = c.customer_id
GROUP BY c.customer_segment
ORDER BY net_revenue DESC;



SELECT*
FROM dim_customers;