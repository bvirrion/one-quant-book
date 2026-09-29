SELECT COUNT(*) AS rows_after_join, (SELECT COUNT(*) FROM quotes WHERE sym = 'AAA') AS aaa_quotes
FROM quotes q1 JOIN quotes q2 ON q1.sym = q2.sym AND q1.ts = q2.ts
WHERE q1.sym = 'AAA';
