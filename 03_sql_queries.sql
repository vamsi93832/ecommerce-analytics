/* ================================================================================
   E-COMMERCE SALES ANALYTICS PLATFORM
   PROJECT 1: SQL QUERIES
   ================================================================================ */

-- ==================== CREATE TABLES ====================

CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(100),
    email VARCHAR(100),
    country VARCHAR(50),
    state VARCHAR(50),
    signup_date DATE,
    customer_lifetime_value DECIMAL(10, 2),
    total_orders INT
);

CREATE TABLE products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(100),
    price DECIMAL(10, 2),
    category VARCHAR(50),
    stock_quantity INT
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT,
    order_date DATE,
    order_status VARCHAR(50),
    total_order_value DECIMAL(10, 2),
    payment_method VARCHAR(50),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_item_id INT PRIMARY KEY,
    order_id INT,
    product_id INT,
    product_name VARCHAR(100),
    quantity INT,
    unit_price DECIMAL(10, 2),
    line_total DECIMAL(10, 2),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE reviews (
    review_id INT PRIMARY KEY,
    order_id INT,
    customer_id INT,
    product_id INT,
    rating INT,
    review_text VARCHAR(500),
    review_date DATE,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- ==================== ANALYTICAL QUERIES ====================

-- QUERY 1: Daily Sales Summary
SELECT 
    CAST(o.order_date AS DATE) AS sale_date,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(o.total_order_value) AS daily_revenue,
    SUM(oi.quantity) AS units_sold,
    COUNT(DISTINCT o.customer_id) AS unique_customers,
    ROUND(SUM(o.total_order_value) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM orders o
LEFT JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status IN ('Completed', 'Shipped')
GROUP BY CAST(o.order_date AS DATE)
ORDER BY sale_date DESC;

-- QUERY 2: Product Performance Analysis
SELECT 
    p.product_id,
    p.product_name,
    COUNT(DISTINCT o.order_id) AS orders_count,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.line_total), 2) AS total_revenue,
    ROUND(AVG(r.rating), 2) AS avg_rating,
    p.price,
    p.stock_quantity
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
LEFT JOIN orders o ON oi.order_id = o.order_id
LEFT JOIN reviews r ON p.product_id = r.product_id
WHERE o.order_status IN ('Completed', 'Shipped') OR o.order_status IS NULL
GROUP BY p.product_id, p.product_name, p.price, p.stock_quantity
ORDER BY total_revenue DESC;

-- QUERY 3: Category Performance
SELECT 
    p.category,
    COUNT(DISTINCT o.order_id) AS orders_count,
    SUM(oi.quantity) AS total_units_sold,
    ROUND(SUM(oi.line_total), 2) AS category_revenue,
    COUNT(DISTINCT o.customer_id) AS unique_customers,
    ROUND(SUM(oi.line_total) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM order_items oi
LEFT JOIN products p ON oi.product_id = p.product_id
LEFT JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status IN ('Completed', 'Shipped')
GROUP BY p.category
ORDER BY category_revenue DESC;

-- QUERY 4: Customer Metrics
SELECT 
    c.customer_id,
    c.customer_name,
    c.country,
    COUNT(DISTINCT o.order_id) AS purchase_count,
    ROUND(SUM(o.total_order_value), 2) AS total_spent,
    ROUND(AVG(o.total_order_value), 2) AS avg_order_value,
    c.signup_date,
    DATEDIFF(DAY, c.signup_date, GETDATE()) AS customer_age_days,
    CASE 
        WHEN SUM(o.total_order_value) >= 1500 THEN 'Gold'
        WHEN SUM(o.total_order_value) >= 500 THEN 'Silver'
        ELSE 'Bronze'
    END AS customer_segment
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.order_status IN ('Completed', 'Shipped')
GROUP BY c.customer_id, c.customer_name, c.country, c.signup_date
ORDER BY total_spent DESC;

-- QUERY 5: Geographic Performance
SELECT 
    c.country,
    c.state,
    COUNT(DISTINCT o.order_id) AS orders_count,
    ROUND(SUM(o.total_order_value), 2) AS revenue,
    COUNT(DISTINCT c.customer_id) AS unique_customers,
    ROUND(SUM(o.total_order_value) / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status IN ('Completed', 'Shipped')
GROUP BY c.country, c.state
ORDER BY revenue DESC;

-- QUERY 6: Monthly Sales Trend
SELECT 
    YEAR(o.order_date) AS year,
    MONTH(o.order_date) AS month,
    DATEFROMPARTS(YEAR(o.order_date), MONTH(o.order_date), 1) AS month_start,
    COUNT(DISTINCT o.order_id) AS monthly_orders,
    ROUND(SUM(o.total_order_value), 2) AS monthly_revenue,
    SUM(oi.quantity) AS monthly_units,
    COUNT(DISTINCT o.customer_id) AS new_customers_month
FROM orders o
LEFT JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status IN ('Completed', 'Shipped')
GROUP BY YEAR(o.order_date), MONTH(o.order_date)
ORDER BY year DESC, month DESC;

-- QUERY 7: Customer Lifetime Value Cohort Analysis
SELECT 
    c.customer_id,
    c.customer_name,
    YEAR(c.signup_date) AS signup_year,
    MONTH(c.signup_date) AS signup_month,
    COUNT(DISTINCT o.order_id) AS lifetime_orders,
    ROUND(SUM(o.total_order_value), 2) AS lifetime_value,
    ROUND(AVG(o.total_order_value), 2) AS avg_transaction_value,
    MIN(o.order_date) AS first_purchase_date,
    MAX(o.order_date) AS last_purchase_date
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.order_status IN ('Completed', 'Shipped')
GROUP BY c.customer_id, c.customer_name, YEAR(c.signup_date), MONTH(c.signup_date)
ORDER BY lifetime_value DESC;

-- QUERY 8: Top 10 Products by Revenue
SELECT TOP 10
    p.product_id,
    p.product_name,
    p.category,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.line_total), 2) AS revenue,
    ROUND(AVG(r.rating), 2) AS avg_rating,
    COUNT(DISTINCT r.review_id) AS review_count
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
LEFT JOIN reviews r ON p.product_id = r.product_id
WHERE o.order_status IN ('Completed', 'Shipped')
GROUP BY p.product_id, p.product_name, p.category
ORDER BY revenue DESC;

-- QUERY 9: Customer Churn Risk (No purchase in 30 days)
SELECT 
    c.customer_id,
    c.customer_name,
    MAX(o.order_date) AS last_purchase_date,
    DATEDIFF(DAY, MAX(o.order_date), GETDATE()) AS days_since_purchase,
    COUNT(DISTINCT o.order_id) AS total_purchases,
    ROUND(SUM(o.total_order_value), 2) AS total_value,
    CASE 
        WHEN DATEDIFF(DAY, MAX(o.order_date), GETDATE()) > 90 THEN 'High Risk'
        WHEN DATEDIFF(DAY, MAX(o.order_date), GETDATE()) > 30 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END AS churn_risk
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.order_status IN ('Completed', 'Shipped')
GROUP BY c.customer_id, c.customer_name
HAVING MAX(o.order_date) IS NOT NULL
ORDER BY days_since_purchase DESC;

-- QUERY 10: Product Review Analysis
SELECT 
    p.product_id,
    p.product_name,
    ROUND(AVG(r.rating), 2) AS avg_rating,
    COUNT(DISTINCT r.review_id) AS total_reviews,
    SUM(CASE WHEN r.rating >= 4 THEN 1 ELSE 0 END) AS positive_reviews,
    SUM(CASE WHEN r.rating < 4 THEN 1 ELSE 0 END) AS negative_reviews,
    ROUND(CAST(SUM(CASE WHEN r.rating >= 4 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(DISTINCT r.review_id) * 100, 2) AS positive_percentage
FROM products p
LEFT JOIN reviews r ON p.product_id = r.product_id
GROUP BY p.product_id, p.product_name
HAVING COUNT(DISTINCT r.review_id) > 0
ORDER BY avg_rating DESC, total_reviews DESC;

-- QUERY 11: Order Status Summary
SELECT 
    order_status,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(SUM(total_order_value), 2) AS status_revenue,
    ROUND(AVG(total_order_value), 2) AS avg_order_value,
    ROUND(100.0 * COUNT(DISTINCT order_id) / (SELECT COUNT(DISTINCT order_id) FROM orders), 2) AS percentage_of_total
FROM orders
GROUP BY order_status;

-- QUERY 12: Payment Method Analysis
SELECT 
    payment_method,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(SUM(total_order_value), 2) AS payment_revenue,
    ROUND(AVG(total_order_value), 2) AS avg_transaction_value,
    ROUND(100.0 * COUNT(DISTINCT order_id) / (SELECT COUNT(DISTINCT order_id) FROM orders WHERE order_status IN ('Completed', 'Shipped')), 2) AS percentage_usage
FROM orders
WHERE order_status IN ('Completed', 'Shipped')
GROUP BY payment_method
ORDER BY payment_revenue DESC;

-- ==================== INDEX CREATION FOR PERFORMANCE ====================

CREATE INDEX idx_order_date ON orders(order_date);
CREATE INDEX idx_customer_id ON orders(customer_id);
CREATE INDEX idx_product_id ON order_items(product_id);
CREATE INDEX idx_order_status ON orders(order_status);
CREATE INDEX idx_review_product ON reviews(product_id);

-- ==================== END OF QUERIES ====================
