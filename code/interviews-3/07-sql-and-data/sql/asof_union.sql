WITH merged AS (
    SELECT symbol, ts, 0 AS kind, mid FROM quotes
    UNION ALL
    SELECT symbol, ts, 1 AS kind, NULL FROM trades
),
grouped AS (
    SELECT symbol, ts, kind, mid,
           COUNT(mid) OVER (PARTITION BY symbol ORDER BY ts, kind
                            ROWS UNBOUNDED PRECEDING) AS grp
    FROM merged
)
SELECT symbol, ts, last_mid AS mid
FROM (SELECT symbol, ts, kind,
             MAX(mid) OVER (PARTITION BY symbol, grp) AS last_mid
      FROM grouped)
WHERE kind = 1
ORDER BY symbol, ts;
