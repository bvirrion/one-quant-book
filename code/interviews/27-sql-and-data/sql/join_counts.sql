SELECT
    (SELECT COUNT(*) FROM trades t JOIN accounts a ON t.account = a.account) AS inner_rows,
    (SELECT COUNT(*) FROM trades t LEFT JOIN accounts a ON t.account = a.account) AS left_rows,
    (SELECT COUNT(*) FROM trades t WHERE NOT EXISTS (SELECT 1 FROM accounts a WHERE a.account = t.account)) AS orphans;
