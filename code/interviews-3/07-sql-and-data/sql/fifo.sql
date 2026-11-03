WITH spans AS (
    SELECT seq, side, price,
           SUM(qty) OVER (PARTITION BY side ORDER BY seq) - qty AS lo,
           SUM(qty) OVER (PARTITION BY side ORDER BY seq) AS hi
    FROM fills
),
lots AS (
    SELECT b.seq AS buy_seq, s.seq AS sell_seq, b.price AS buy_price, s.price AS sell_price,
           CASE WHEN b.hi < s.hi THEN b.hi ELSE s.hi END
         - CASE WHEN b.lo > s.lo THEN b.lo ELSE s.lo END AS qty
    FROM spans b JOIN spans s
      ON b.side = 'B' AND s.side = 'S' AND b.lo < s.hi AND s.lo < b.hi
)
SELECT buy_seq, sell_seq, qty, (sell_price - buy_price) * qty AS pnl
FROM lots
ORDER BY sell_seq, buy_seq;
