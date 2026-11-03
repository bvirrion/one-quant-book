SELECT symbol, day, SUM(price * qty) / SUM(qty) AS vwap
FROM trades
GROUP BY symbol, day
HAVING COUNT(*) > 2;
