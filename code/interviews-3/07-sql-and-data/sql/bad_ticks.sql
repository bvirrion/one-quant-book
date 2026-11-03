WITH q AS (
    SELECT seq, ts, bid, ask, bid_size,
           LAG(ts) OVER (ORDER BY seq) AS prev_ts,
           LAG((bid + ask) / 2) OVER (ORDER BY seq) AS prev_mid
    FROM quotes
)
SELECT seq,
       CASE WHEN bid >= ask THEN 'crossed'
            WHEN bid_size <= 0 THEN 'size'
            WHEN ts <= prev_ts THEN 'time'
            WHEN ABS((bid + ask) / 2 - prev_mid) > 0.05 * prev_mid THEN 'jump'
       END AS problem
FROM q
WHERE bid >= ask OR bid_size <= 0 OR ts <= prev_ts
   OR ABS((bid + ask) / 2 - prev_mid) > 0.05 * prev_mid
ORDER BY seq;
