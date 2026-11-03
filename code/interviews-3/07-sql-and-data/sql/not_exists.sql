SELECT o.order_id
FROM orders o
WHERE NOT EXISTS (SELECT 1 FROM blocked b WHERE b.trader = o.trader);
