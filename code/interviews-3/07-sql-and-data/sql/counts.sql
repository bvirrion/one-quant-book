SELECT COUNT(*), COUNT(bid), COUNT(DISTINCT bid), SUM(bid), AVG(bid), SUM(bid) / COUNT(*)
FROM quotes;

SELECT COUNT(*) FROM quotes WHERE bid = NULL;
