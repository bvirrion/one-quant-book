WITH groups AS (
    SELECT day, price,
           COUNT(price) OVER (ORDER BY day) AS grp,
           MAX(CASE WHEN price IS NOT NULL THEN day END) OVER (ORDER BY day) AS last_day
    FROM closes
)
SELECT day,
       CASE WHEN day - last_day <= 1 THEN MAX(price) OVER (PARTITION BY grp) END AS filled
FROM groups
ORDER BY day;
