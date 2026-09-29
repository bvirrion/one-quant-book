SELECT account, day, cum_pnl,
       cum_pnl - MAX(cum_pnl) OVER (PARTITION BY account ORDER BY day) AS drawdown
FROM (
    SELECT account, day, SUM(pnl) OVER (PARTITION BY account ORDER BY day) AS cum_pnl
    FROM pnl
) c
ORDER BY account, day;
