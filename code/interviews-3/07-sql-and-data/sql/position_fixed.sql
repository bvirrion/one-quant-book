SELECT seq, ts, qty,
       SUM(qty) OVER (ORDER BY ts, seq ROWS UNBOUNDED PRECEDING) AS position
FROM fills
ORDER BY seq;
