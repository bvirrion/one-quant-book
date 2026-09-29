SELECT account, MAX(run_length) AS longest_positive_run
FROM (
    SELECT account, grp, COUNT(*) AS run_length
    FROM (
        SELECT account, day, pnl,
               day - ROW_NUMBER() OVER (PARTITION BY account ORDER BY day) AS grp
        FROM pnl
        WHERE pnl > 0
    ) positive
    GROUP BY account, grp
) runs
GROUP BY account
ORDER BY account;
