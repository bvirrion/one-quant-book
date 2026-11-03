WITH per_order AS (
    SELECT order_id, SUM(filled) AS filled
    FROM fills
    GROUP BY order_id
)
SELECT o.desk, SUM(o.qty) AS ordered, SUM(COALESCE(p.filled, 0)) AS filled
FROM orders o LEFT JOIN per_order p ON o.order_id = p.order_id
GROUP BY o.desk
ORDER BY o.desk;
