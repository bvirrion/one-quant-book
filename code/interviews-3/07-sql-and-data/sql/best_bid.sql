WITH levels AS (
    SELECT price, seq AS from_seq,
           LEAD(seq) OVER (PARTITION BY price ORDER BY seq) AS to_seq,
           SUM(delta) OVER (PARTITION BY price ORDER BY seq) AS qty
    FROM events
),
ranked AS (
    SELECT e.seq, l.price, l.qty,
           ROW_NUMBER() OVER (PARTITION BY e.seq ORDER BY l.price DESC) AS rn
    FROM events e JOIN levels l
      ON l.from_seq <= e.seq AND (l.to_seq IS NULL OR e.seq < l.to_seq) AND l.qty > 0
)
SELECT e.seq, r.price, r.qty
FROM events e LEFT JOIN ranked r ON r.seq = e.seq AND r.rn = 1
ORDER BY e.seq;
