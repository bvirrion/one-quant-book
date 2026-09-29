SELECT t.ts, t.sym, q.bid
FROM trades t ASOF LEFT JOIN quotes q ON t.sym = q.sym AND t.ts >= q.ts
ORDER BY t.ts;
