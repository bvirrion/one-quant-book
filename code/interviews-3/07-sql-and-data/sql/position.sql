SELECT seq, ts, qty, SUM(qty) OVER (ORDER BY ts) AS position
FROM fills
ORDER BY seq;
