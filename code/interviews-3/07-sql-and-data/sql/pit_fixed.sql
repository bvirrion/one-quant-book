SELECT t.ticker, t.day, t.qty, m.inst_id
FROM trades t JOIN master m
  ON t.ticker = m.ticker AND m.valid_from <= t.day AND t.day < m.valid_to
ORDER BY t.day, m.inst_id;
