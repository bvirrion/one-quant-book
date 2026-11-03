SELECT symbol, MAX(ts) AS ts, price
FROM prices
GROUP BY symbol;
