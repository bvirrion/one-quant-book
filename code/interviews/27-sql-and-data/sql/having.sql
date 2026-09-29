SELECT a.desk, SUM(t.qty) AS volume
FROM trades t JOIN accounts a ON t.account = a.account
GROUP BY a.desk
HAVING SUM(t.qty) > 20000
ORDER BY a.desk;
