SELECT sym, ts AS halt_start, next_ts AS halt_end
FROM (
    SELECT sym, ts, state, LEAD(ts) OVER (PARTITION BY sym ORDER BY ts) AS next_ts
    FROM status
) s
WHERE state = 'HALTED'
ORDER BY sym, halt_start;
