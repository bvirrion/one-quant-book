SELECT t.ts, t.sym, q.bid, q.ts AS quote_ts
FROM trades t ASOF LEFT JOIN quotes q ON t.sym = q.sym AND t.ts <= q.ts
ORDER BY t.ts;
