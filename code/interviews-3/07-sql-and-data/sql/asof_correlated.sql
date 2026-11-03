WITH matched AS (
    SELECT t.trade_id, t.ts,
           (SELECT MAX(q.ts) FROM quotes q
             WHERE q.ts <= t.ts AND q.ts >= t.ts - 10) AS quote_ts
    FROM trades t
)
SELECT m.trade_id, m.quote_ts, q.bid, q.ask
FROM matched m LEFT JOIN quotes q ON q.ts = m.quote_ts
ORDER BY m.trade_id;
