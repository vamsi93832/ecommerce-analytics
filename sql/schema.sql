-- three tables, loaded by 02_run_sql.py from data/processed/
--
--   orders       one row per order: customer, dates, delivery, money, review
--   order_items  one row per item in an order: product category, seller, price
--   sellers      one row per seller
--
-- GMV (gross merchandise value) is the sum of item prices, without freight.
-- it's measured from order_items, not payments, because payments include
-- installment interest and vouchers that aren't sales

CREATE TABLE orders AS SELECT * FROM orders_src;
CREATE TABLE order_items AS SELECT * FROM order_items_src;
CREATE TABLE sellers AS SELECT * FROM sellers_src;

-- delivered orders only, with the review attached. every delivery and
-- review question reads from here so they all use the same population
CREATE VIEW delivered_orders AS
SELECT *
FROM orders
WHERE is_delivered = 1;
