SELECT DISTINCT minute,
       FIRST_VALUE(price) OVER w AS open,
       MAX(price)         OVER w AS high,
       MIN(price)         OVER w AS low,
       LAST_VALUE(price)  OVER w AS close
FROM ticks
WINDOW w AS (PARTITION BY minute ORDER BY seq
             ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
ORDER BY minute;
