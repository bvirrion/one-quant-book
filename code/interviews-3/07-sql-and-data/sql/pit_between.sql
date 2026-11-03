SELECT t.ticker, t.day, t.qty, m.inst_id
FROM trades t JOIN master m
  ON t.ticker = m.ticker AND t.day BETWEEN m.valid_from AND m.valid_to
ORDER BY t.day, m.inst_id;
