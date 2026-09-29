SELECT t.ts, t.sym,
       (SELECT q.bid FROM quotes q
        WHERE q.sym = t.sym AND q.ts <= t.ts
        ORDER BY q.ts DESC, q.rowid DESC LIMIT 1) AS bid
FROM trades t
ORDER BY t.ts;
