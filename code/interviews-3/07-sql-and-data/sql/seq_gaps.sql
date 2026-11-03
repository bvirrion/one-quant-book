SELECT seq + 1 AS first_missing, next_seq - 1 AS last_missing
FROM (SELECT seq, LEAD(seq) OVER (ORDER BY seq) AS next_seq FROM msgs)
WHERE next_seq > seq + 1
ORDER BY first_missing;
