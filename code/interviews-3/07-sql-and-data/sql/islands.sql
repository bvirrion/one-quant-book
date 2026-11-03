WITH numbered AS (
    SELECT day, pnl, ROW_NUMBER() OVER (ORDER BY day) AS pos
    FROM daily
),
wins AS (
    SELECT day, pos - ROW_NUMBER() OVER (ORDER BY day) AS island
    FROM numbered
    WHERE pnl > 0
)
SELECT MIN(day) AS first_day, MAX(day) AS last_day, COUNT(*) AS days
FROM wins
GROUP BY island
ORDER BY days DESC, first_day
LIMIT 1;
