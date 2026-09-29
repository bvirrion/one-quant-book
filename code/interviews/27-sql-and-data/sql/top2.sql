SELECT sym, ts, qty
FROM (
    SELECT sym, ts, qty, ROW_NUMBER() OVER (PARTITION BY sym ORDER BY qty DESC, ts) AS rk
    FROM trades
    WHERE qty IS NOT NULL
) ranked
WHERE rk <= 2
ORDER BY sym, rk;
