SELECT order_id
FROM orders
WHERE trader NOT IN (SELECT trader FROM blocked);
