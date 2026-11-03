WITH ranked AS (
    SELECT symbol, ts, price,
           ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY ts DESC) AS rn
    FROM prices
)
SELECT symbol, ts, price
FROM ranked
WHERE rn = 1
ORDER BY symbol;
