WITH groups AS (
    SELECT day, price, COUNT(price) OVER (ORDER BY day) AS grp
    FROM closes
)
SELECT day, MAX(price) OVER (PARTITION BY grp) AS filled
FROM groups
ORDER BY day;
