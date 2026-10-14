-- business questions for an e-commerce marketplace.
-- each block has a name (the output file) and the question it answers, so the
-- dashboard can show the exact query next to its result.
-- standard SQL tested in DuckDB; runs on Snowflake, Postgres or BigQuery with
-- little change (MEDIAN would be PERCENTILE_CONT(0.5) elsewhere)


-- name: kpi_summary
-- question: How did the business grow year over year, comparing the same months?
-- 2018 data stops in August, so both years use January to August. comparing
-- a full 2017 to eight months of 2018 would make 2018 look like a decline
WITH item_totals AS (
    SELECT order_id, SUM(price) AS gmv FROM order_items GROUP BY order_id
),
base AS (
    SELECT
        SUBSTR(o.purchase_month, 1, 4) AS year,
        o.*,
        i.gmv
    FROM orders o
    LEFT JOIN item_totals i ON i.order_id = o.order_id
    WHERE SUBSTR(o.purchase_month, 6, 2) BETWEEN '01' AND '08'
      AND SUBSTR(o.purchase_month, 1, 4) IN ('2017', '2018')
)
SELECT
    year || ' (Jan-Aug)'                                            AS period,
    COUNT(*)                                                        AS orders,
    COUNT(DISTINCT customer_unique_id)                              AS customers,
    ROUND(SUM(gmv), 2)                                              AS gmv,
    ROUND(SUM(gmv) / COUNT(gmv), 2)                                 AS avg_order_value,
    ROUND(100.0 * SUM(freight_value) / SUM(gmv), 1)                 AS freight_pct_of_gmv,
    ROUND(100.0 * AVG(CASE WHEN is_delivered = 1 THEN 1 - is_late END), 1) AS on_time_pct,
    ROUND(AVG(review_score), 2)                                     AS avg_review,
    ROUND(100.0 * SUM(CASE WHEN order_status = 'canceled' THEN 1 ELSE 0 END) / COUNT(*), 2) AS canceled_pct
FROM base
GROUP BY year
ORDER BY year;


-- name: monthly_trend
-- question: How did orders, revenue and service quality move month by month?
WITH item_totals AS (
    SELECT order_id, SUM(price) AS gmv FROM order_items GROUP BY order_id
)
SELECT
    o.purchase_month                                                AS month,
    COUNT(*)                                                        AS orders,
    ROUND(SUM(i.gmv), 2)                                            AS gmv,
    ROUND(SUM(i.gmv) / COUNT(i.gmv), 2)                             AS avg_order_value,
    ROUND(100.0 * AVG(CASE WHEN o.is_delivered = 1 THEN o.is_late END), 1) AS late_pct,
    ROUND(AVG(o.review_score), 2)                                   AS avg_review
FROM orders o
LEFT JOIN item_totals i ON i.order_id = o.order_id
WHERE o.in_full_months = 1   -- the half-empty months at either end would fake a crash
GROUP BY o.purchase_month
ORDER BY o.purchase_month;


-- name: lateness_vs_reviews
-- question: How much does a late delivery hurt the customer's review?
SELECT
    CASE
        WHEN days_vs_estimate <= -15 THEN '1. 15+ days early'
        WHEN days_vs_estimate <= -7  THEN '2. 7-14 days early'
        WHEN days_vs_estimate <= 0   THEN '3. 0-6 days early'
        WHEN days_vs_estimate <= 3   THEN '4. 1-3 days late'
        WHEN days_vs_estimate <= 7   THEN '5. 4-7 days late'
        ELSE                              '6. 8+ days late'
    END                                                             AS arrival,
    COUNT(*)                                                        AS orders,
    ROUND(AVG(review_score), 2)                                     AS avg_review,
    ROUND(100.0 * AVG(CASE WHEN review_score = 1 THEN 1 ELSE 0 END), 1) AS one_star_pct,
    ROUND(100.0 * AVG(CASE WHEN review_score = 5 THEN 1 ELSE 0 END), 1) AS five_star_pct
FROM delivered_orders
WHERE review_score IS NOT NULL
GROUP BY 1
ORDER BY 1;


-- name: delivery_promise
-- question: How long does delivery really take, and how much padding is in the promised date?
SELECT
    ROUND(MEDIAN(delivery_days), 1)                                 AS median_days_to_deliver,
    ROUND(MEDIAN(EXTRACT(EPOCH FROM (order_estimated_delivery_date - order_purchase_timestamp)) / 86400), 1)
                                                                    AS median_days_promised,
    ROUND(MEDIAN(-days_vs_estimate), 1)                             AS median_days_early,
    ROUND(100.0 * AVG(is_late), 1)                                  AS late_pct,
    COUNT(*)                                                        AS delivered_orders
FROM delivered_orders;


-- name: late_by_customer_state
-- question: Which customer states get the slowest, latest deliveries, and does it show in reviews?
SELECT
    customer_state,
    COUNT(*)                                                        AS delivered_orders,
    ROUND(MEDIAN(delivery_days), 1)                                 AS median_days_to_deliver,
    ROUND(100.0 * AVG(is_late), 1)                                  AS late_pct,
    ROUND(AVG(review_score), 2)                                     AS avg_review
FROM delivered_orders
GROUP BY customer_state
HAVING COUNT(*) >= 500        -- smaller states swing too much on a few orders
ORDER BY late_pct DESC, customer_state;


-- name: worst_shipping_lanes
-- question: Which seller-to-customer routes fail most often?
-- single-seller orders only, so each order has exactly one route
WITH lanes AS (
    SELECT DISTINCT d.order_id, i.seller_state, d.customer_state, d.is_late, d.delivery_days
    FROM delivered_orders d
    JOIN order_items i ON i.order_id = d.order_id
    WHERE d.n_sellers = 1
)
SELECT
    seller_state || ' -> ' || customer_state                        AS lane,
    COUNT(*)                                                        AS orders,
    ROUND(MEDIAN(delivery_days), 1)                                 AS median_days,
    ROUND(100.0 * AVG(is_late), 1)                                  AS late_pct
FROM lanes
GROUP BY seller_state, customer_state
HAVING COUNT(*) >= 300
ORDER BY late_pct DESC, lane
LIMIT 15;


-- name: seller_scorecard
-- question: Which high-volume sellers deliver late or get poor reviews?
-- a review belongs to a whole order, so only single-seller orders are used to
-- rate sellers. otherwise one bad seller would drag down everyone in the cart
WITH seller_orders AS (
    SELECT
        i.seller_id,
        d.order_id,
        MAX(d.is_late)          AS is_late,
        MAX(d.review_score)     AS review_score,
        SUM(i.price)            AS gmv
    FROM delivered_orders d
    JOIN order_items i ON i.order_id = d.order_id
    WHERE d.n_sellers = 1
    GROUP BY i.seller_id, d.order_id
),
marketplace AS (
    SELECT AVG(review_score) AS avg_review, AVG(is_late) AS late_rate FROM seller_orders
)
SELECT
    s.seller_id,
    sl.seller_state,
    COUNT(*)                                                        AS orders,
    ROUND(SUM(s.gmv), 2)                                            AS gmv,
    ROUND(100.0 * AVG(s.is_late), 1)                                AS late_pct,
    ROUND(AVG(s.review_score), 2)                                   AS avg_review,
    ROUND(100.0 * AVG(CASE WHEN s.review_score = 1 THEN 1 ELSE 0 END), 1) AS one_star_pct,
    ROUND(AVG(s.review_score) - MAX(m.avg_review), 2)               AS review_vs_marketplace,
    CASE
        WHEN AVG(s.review_score) < MAX(m.avg_review) - 0.5 AND AVG(s.is_late) > 2 * MAX(m.late_rate)
            THEN 'Review: late and poorly rated'
        WHEN AVG(s.review_score) < MAX(m.avg_review) - 0.5 THEN 'Watch: poorly rated'
        WHEN AVG(s.is_late) > 2 * MAX(m.late_rate)           THEN 'Watch: often late'
        ELSE 'OK'
    END                                                             AS flag
FROM seller_orders s
JOIN sellers sl ON sl.seller_id = s.seller_id
CROSS JOIN marketplace m
GROUP BY s.seller_id, sl.seller_state
HAVING COUNT(*) >= 100
ORDER BY review_vs_marketplace ASC, s.seller_id;  -- seller ID breaks ties, so the order never changes between runs


-- name: seller_concentration
-- question: How dependent is the marketplace on its biggest sellers?
WITH seller_gmv AS (
    SELECT seller_id, SUM(price) AS gmv FROM order_items GROUP BY seller_id
),
ranked AS (
    SELECT gmv,
           ROW_NUMBER() OVER (ORDER BY gmv DESC) AS rnk,
           COUNT(*) OVER ()                      AS n
    FROM seller_gmv
)
SELECT
    tier,
    COUNT(*)                                                        AS sellers,
    ROUND(100.0 * SUM(gmv) / (SELECT SUM(gmv) FROM ranked), 1)      AS gmv_share_pct
FROM (
    SELECT gmv,
           CASE WHEN rnk <= n * 0.01 THEN '1. Top 1%'
                WHEN rnk <= n * 0.10 THEN '2. Next 9% (top 10%)'
                WHEN rnk <= n * 0.50 THEN '3. Next 40% (top half)'
                ELSE                      '4. Bottom 50%' END AS tier
    FROM ranked
) t
GROUP BY tier
ORDER BY tier;


-- name: category_performance
-- question: Which product categories drive revenue, and which ones have a delivery or review problem?
WITH cat_orders AS (
    SELECT
        i.category,
        i.order_id,
        SUM(i.price)            AS gmv,
        SUM(i.freight_value)    AS freight
    FROM order_items i
    GROUP BY i.category, i.order_id
)
SELECT
    c.category,
    COUNT(*)                                                        AS orders,
    ROUND(SUM(c.gmv), 2)                                            AS gmv,
    ROUND(100.0 * SUM(c.gmv) / SUM(SUM(c.gmv)) OVER (), 1)          AS gmv_share_pct,
    ROUND(100.0 * SUM(c.freight) / SUM(c.gmv), 1)                   AS freight_pct_of_price,
    ROUND(100.0 * AVG(CASE WHEN o.is_delivered = 1 THEN o.is_late END), 1) AS late_pct,
    ROUND(AVG(o.review_score), 2)                                   AS avg_review
FROM cat_orders c
JOIN orders o ON o.order_id = c.order_id
GROUP BY c.category
HAVING COUNT(*) >= 500
ORDER BY gmv DESC, c.category
LIMIT 20;


-- name: repeat_customers
-- question: How many customers come back, and how much revenue do they bring?
-- counted on customer_unique_id. customer_id is new on every order, so it
-- would report that nobody ever returns
WITH item_totals AS (
    SELECT order_id, SUM(price) AS gmv FROM order_items GROUP BY order_id
),
people AS (
    SELECT
        o.customer_unique_id,
        COUNT(*)                         AS orders,
        SUM(i.gmv)                       AS gmv,
        MIN(o.order_purchase_timestamp)  AS first_order,
        -- second purchase date, for how long people take to come back
        MIN(CASE WHEN o.order_purchase_timestamp > f.first_ts THEN o.order_purchase_timestamp END) AS second_order
    FROM orders o
    LEFT JOIN item_totals i ON i.order_id = o.order_id
    -- the first-order date has to skip canceled orders too. the first version
    -- didn't, so someone whose first order was canceled looked like they came
    -- back the same day, and one-time buyers showed "0 days to return"
    JOIN (SELECT customer_unique_id, MIN(order_purchase_timestamp) AS first_ts
          FROM orders
          WHERE order_status NOT IN ('canceled', 'unavailable')
          GROUP BY customer_unique_id) f ON f.customer_unique_id = o.customer_unique_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
    GROUP BY o.customer_unique_id
)
SELECT
    CASE WHEN orders = 1 THEN 'One order' WHEN orders = 2 THEN 'Two orders' ELSE 'Three or more' END AS segment,
    COUNT(*)                                                        AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)              AS customer_share_pct,
    ROUND(100.0 * SUM(gmv) / SUM(SUM(gmv)) OVER (), 1)              AS gmv_share_pct,
    ROUND(MEDIAN(EXTRACT(EPOCH FROM (second_order - first_order)) / 86400), 0) AS median_days_to_return
FROM people
GROUP BY 1
ORDER BY MIN(orders);


-- name: payment_mix
-- question: How do customers pay, and do installment plans mean bigger baskets?
WITH item_totals AS (
    SELECT order_id, SUM(price) AS gmv FROM order_items GROUP BY order_id
)
SELECT
    o.payment_type,
    CASE WHEN o.max_installments <= 1 THEN '1. Paid in full'
         WHEN o.max_installments <= 3 THEN '2. 2-3 installments'
         WHEN o.max_installments <= 6 THEN '3. 4-6 installments'
         ELSE '4. 7+ installments' END                              AS installments,
    COUNT(*)                                                        AS orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)              AS order_share_pct,
    ROUND(AVG(i.gmv), 2)                                            AS avg_order_value
FROM orders o
JOIN item_totals i ON i.order_id = o.order_id
WHERE o.payment_type IN ('credit_card', 'boleto', 'debit_card', 'voucher')
GROUP BY 1, 2
HAVING COUNT(*) >= 200
ORDER BY 1, 2;
