-- DuckDB: compare each mid with the median of the five before it, so one bad print flags itself only.
SELECT seq
FROM (SELECT seq, (bid + ask) / 2 AS mid,
             MEDIAN((bid + ask) / 2) OVER (ORDER BY seq
                 ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING) AS med
      FROM quotes)
WHERE ABS(mid - med) > 0.05 * med
ORDER BY seq;
