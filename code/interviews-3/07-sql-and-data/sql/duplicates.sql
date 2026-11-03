-- Which IDs repeat, and do the copies agree?
SELECT trade_id, COUNT(*) AS copies, COUNT(DISTINCT qty) AS versions
FROM trades
GROUP BY trade_id
HAVING COUNT(*) > 1;

-- Totals per symbol, where the latest version of each trade wins
WITH ranked AS (
    SELECT symbol, qty,
           ROW_NUMBER() OVER (PARTITION BY trade_id ORDER BY seq DESC) AS rn
    FROM trades
)
SELECT symbol, SUM(qty) AS total
FROM ranked
WHERE rn = 1
GROUP BY symbol
ORDER BY symbol;
