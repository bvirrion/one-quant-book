SELECT a.inst_id AS first_id, b.inst_id AS second_id, a.ticker
FROM master a JOIN master b
  ON a.ticker = b.ticker AND a.inst_id < b.inst_id
 AND a.valid_from < b.valid_to AND b.valid_from < a.valid_to;
