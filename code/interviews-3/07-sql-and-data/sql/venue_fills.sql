-- Query A
SELECT o.order_id, f.qty
FROM orders o LEFT JOIN fills f ON o.order_id = f.order_id
WHERE f.venue = 'X';

-- Query B
SELECT o.order_id, f.qty
FROM orders o LEFT JOIN fills f ON o.order_id = f.order_id AND f.venue = 'X';
