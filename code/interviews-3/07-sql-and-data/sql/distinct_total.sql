SELECT symbol, SUM(qty) AS total
FROM (SELECT DISTINCT trade_id, symbol, qty FROM trades)
GROUP BY symbol
ORDER BY symbol;
