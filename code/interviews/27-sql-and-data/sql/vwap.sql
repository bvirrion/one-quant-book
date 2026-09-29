SELECT sym, (ts - ts % 300) / 300 AS bucket, SUM(px * qty) / SUM(qty) AS vwap, SUM(qty) AS volume
FROM trades
WHERE qty IS NOT NULL
GROUP BY sym, (ts - ts % 300) / 300
ORDER BY sym, bucket;
