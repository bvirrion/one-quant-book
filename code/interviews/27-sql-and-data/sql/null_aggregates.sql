SELECT COUNT(*) AS n_rows, COUNT(qty) AS n_qty, SUM(qty) AS total_qty, AVG(qty) AS avg_qty
FROM trades;
