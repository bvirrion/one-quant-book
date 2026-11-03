WITH marked AS (
    SELECT trader, ts,
           CASE WHEN ts - LAG(ts) OVER (PARTITION BY trader ORDER BY ts) <= 300
                THEN 0 ELSE 1 END AS starts
    FROM events
),
numbered AS (
    SELECT trader, ts,
           SUM(starts) OVER (PARTITION BY trader ORDER BY ts) AS session
    FROM marked
)
SELECT trader, session, MIN(ts) AS first_ts, MAX(ts) AS last_ts, COUNT(*) AS n
FROM numbered
GROUP BY trader, session
ORDER BY trader, session;
