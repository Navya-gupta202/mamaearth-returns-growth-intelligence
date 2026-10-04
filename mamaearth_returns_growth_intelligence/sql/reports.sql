-- Mamaearth Returns & Growth Intelligence Pipeline
-- Part 1: SQL reports. Expected/verified outputs are printed immediately above each query.

-- a) Order totals
-- 180 | 99860.2 | 554.78
SELECT COUNT(*) AS total_orders,
ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct,0)/100.0)), 2) AS total_revenue,
ROUND(AVG(o.quantity * p.price * (1 - COALESCE(o.discount_pct,0)/100.0)), 2) AS avg_order_value
FROM orders o JOIN products p ON o.product_id=p.product_id;

-- b) COUNT(*) vs COUNT(column)
-- 180 | 165 | 15
SELECT COUNT(*) AS count_star, COUNT(rating) AS count_rating, COUNT(*)-COUNT(rating) AS difference FROM orders;

-- c1) LEFT JOIN zero-match customer
-- C045 | Vihaan
SELECT c.customer_id, c.name
FROM customers c LEFT JOIN orders o ON c.customer_id=o.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id)=0;

-- c2) Independent NOT IN confirmation
-- C045 | Vihaan
SELECT customer_id, name FROM customers
WHERE customer_id NOT IN (SELECT DISTINCT customer_id FROM orders);

-- d) City return rates; HAVING > 20%
-- Jaipur | 19 | 8 | 42.1
-- Lucknow | 49 | 15 | 30.6
-- Bangalore | 33 | 8 | 24.2
SELECT c.city, COUNT(*) AS total_orders, SUM(o.returned) AS returned_orders,
ROUND(100.0*SUM(o.returned)/COUNT(*),1) AS return_rate_pct
FROM orders o JOIN customers c ON o.customer_id=c.customer_id
GROUP BY c.city
HAVING return_rate_pct > 20
ORDER BY return_rate_pct DESC;

-- e1) Top 5 customers. customer_id is a deterministic tie-breaker.
-- C043 | Reyansh | 12920.0
-- C026 | Isha | 8371.6
-- C008 | Meera | 4564.6
-- C011 | Arjun | 4111.0
-- C042 | Sanya | 3785.0
SELECT c.customer_id, c.name,
ROUND(SUM(o.quantity*p.price*(1-COALESCE(o.discount_pct,0)/100.0)),2) AS total_spend
FROM orders o JOIN products p ON o.product_id=p.product_id
JOIN customers c ON o.customer_id=c.customer_id
GROUP BY c.customer_id,c.name
ORDER BY total_spend DESC,c.customer_id ASC
LIMIT 5;

-- e2) Ranks 3-5 using LIMIT/OFFSET, without re-deriving top 5.
-- C008 | Meera | 4564.6
-- C011 | Arjun | 4111.0
-- C042 | Sanya | 3785.0
SELECT c.customer_id, c.name,
ROUND(SUM(o.quantity*p.price*(1-COALESCE(o.discount_pct,0)/100.0)),2) AS total_spend
FROM orders o JOIN products p ON o.product_id=p.product_id
JOIN customers c ON o.customer_id=c.customer_id
GROUP BY c.customer_id,c.name
ORDER BY total_spend DESC,c.customer_id ASC
LIMIT 3 OFFSET 2;

-- f) Category revenue
-- Haircare | 54 | 44956.1
-- Skincare | 60 | 27346.0
-- Babycare | 30 | 16805.0
-- PersonalCare | 36 | 10753.1
SELECT p.category, COUNT(*) AS order_count,
ROUND(SUM(o.quantity*p.price*(1-COALESCE(o.discount_pct,0)/100.0)),2) AS category_revenue
FROM orders o JOIN products p ON o.product_id=p.product_id
JOIN customers c ON o.customer_id=c.customer_id
GROUP BY p.category
ORDER BY category_revenue DESC;

-- g) Names starting with A
-- C001 | Aarav
-- C003 | Aditi
-- C004 | Ananya
-- C011 | Arjun
-- C021 | Aryan
-- C030 | Anika
-- C031 | Aditya
-- C036 | Aisha
-- C041 | Ayaan
-- C044 | Aria
SELECT customer_id,name FROM customers WHERE name LIKE 'A%';

-- h) Distinct acquisition sources
-- Ad
-- Organic
-- Referral
-- Social
SELECT DISTINCT acquisition_source FROM customers ORDER BY acquisition_source;

-- i) Add loyalty tier and populate every customer.
ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(10);
UPDATE customers
SET loyalty_tier = CASE WHEN city_tier = 1 THEN 'Gold' ELSE 'Silver' END;
SELECT loyalty_tier, COUNT(*) AS customer_count
FROM customers
GROUP BY loyalty_tier
ORDER BY loyalty_tier;
