SELECT o.desk, SUM(o.qty) AS ordered, SUM(f.filled) AS filled
FROM orders o JOIN fills f ON o.order_id = f.order_id
GROUP BY o.desk
ORDER BY o.desk;
