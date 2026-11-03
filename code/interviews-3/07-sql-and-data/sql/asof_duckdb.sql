SELECT t.symbol, t.ts, q.mid
FROM trades t ASOF LEFT JOIN quotes q
  ON t.symbol = q.symbol AND t.ts >= q.ts
ORDER BY t.symbol, t.ts;
