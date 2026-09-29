SELECT sym, ts, px, px / LAG(px) OVER (PARTITION BY sym ORDER BY ts) - 1 AS ret
FROM trades
ORDER BY sym, ts;
