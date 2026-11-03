SELECT desk, trader, pnl,
       ROW_NUMBER() OVER (PARTITION BY desk ORDER BY pnl DESC, trader) AS row_num,
       RANK()       OVER w AS rnk,
       DENSE_RANK() OVER w AS dense
FROM pnl
WINDOW w AS (PARTITION BY desk ORDER BY pnl DESC)
ORDER BY desk, row_num;
