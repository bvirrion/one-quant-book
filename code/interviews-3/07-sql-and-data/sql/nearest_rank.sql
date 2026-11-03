SELECT MIN(us) AS p90
FROM (SELECT us,
             ROW_NUMBER() OVER (ORDER BY us) AS pos,
             COUNT(*) OVER () AS n
      FROM latency)
WHERE pos * 10 >= n * 9;
