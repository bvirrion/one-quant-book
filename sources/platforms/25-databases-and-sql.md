# 25. Databases and SQL — brief and source ledger

## Brief

- **Hook.** A regulator asked for the firm's risk report exactly as it stood at 18:00 last Tuesday; the positions table had been corrected in place on Wednesday, and the report could no longer be produced. The database had kept the right answer, but not the answer the firm had given.
- **Sections.** The relational model for trades and positions; Transactions and isolation; Indexes and query plans; Time in the database: system time and time travel; Transactional and analytical workloads.
- **Defines.** relational model, primary key, foreign key, normal form, ACID transaction, isolation level, B-tree index, query plan, write-ahead log, system time, time-travel query, online transaction processing, online analytical processing.
- **Uses (defined earlier).** bitemporal data (B7.3), valid time (B7.3), knowledge time (B7.3), as-of join (B7.3), restatement (B7.3), position (B1.7), canonical trade model (ch21), embedded database (ch5), vectorised query execution (ch5), columnar layout (ch3).
- **Tutorial.** Model instruments, accounts, trades and positions relationally in SQLite and in DuckDB; write trades transactionally and show a lost update at a weak isolation level; add indexes and read the query plans; turn the trades and positions tables into bitemporal tables with valid time and system time, correct a trade, and reproduce Tuesday's 18:00 report exactly; run the same analytical query in both engines. End state: the report as it was and as corrected, and a table of query times by engine and index.
- **Build.** `firm.tradedb`: schema and migrations, a bitemporal table helper (valid-from/to, system-from/to; corrections close rows, never update them), time-travel query helpers (`as_of(valid, system)`), transactional writers with retry, an index advisor from query plans, and the same queries on sqlite3 and DuckDB with equality tests; Python.
- **Weekend problem.** Tuesday at 18:00 -- named result: the positions report reproduced as it stood at 18:00 on the Tuesday against the corrected report, the rows that differ, and the query-time gain from each index.
- **Facts to verify.** Codd 1970, A relational model of data for large shared data banks (CACM); SQL:2011 temporal features (Kulkarni and Michels 2012, SIGMOD Record); SQLite documentation: transactions, isolation, write-ahead logging, EXPLAIN QUERY PLAN; Berenson et al. 1995, A critique of ANSI SQL isolation levels (SIGMOD); Snodgrass 1999, Developing time-oriented database applications in SQL.
- **Data.** Chapter 21's trades and chapter 17's positions; synthetic.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Codd, A relational model of data for large shared data banks, Communications of the ACM 13(6), 377-387, June 1970 | Crossref metadata, DOI 10.1145/362384.362685 | https://doi.org/10.1145/362384.362685 | 2026-09-28 | Crossref: title, author Codd, CACM vol. 13 no. 6 pp. 377-387, issued 1970-06 | sec. relational model; omsources |
| F2 | Berenson, Bernstein, Gray, Melton, O'Neil and O'Neil, A critique of ANSI SQL isolation levels, SIGMOD 1995: P4 lost update, T1 reads x, T2 updates x, T1 updates x from its earlier read and commits, and T2's update is lost; snapshot isolation's first-committer-wins prevents lost updates | Berenson et al. 1995 (Microsoft Research technical report MSR-TR-95-51 copy); Crossref DOI 10.1145/223784.223785 | https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-95-51.pdf | 2026-09-28 | "P4 (Lost Update): The lost update anomaly occurs when transaction T1 reads a data item and then T2 updates the data item (possibly based on a previous read), then T1 (based on its earlier read value) updates the data item and commits"; "This feature, called First-committer-wins prevents lost updates (phenomenon P4)" | sec. transactions; def. isolation level |
| F3 | SQLite: all transactions are serializable (except shared-cache connections with read_uncommitted), implemented by serializing the writes | SQLite documentation, Isolation In SQLite | https://www.sqlite.org/isolation.html | 2026-09-28 | "all transactions in SQLite show \"serializable\" isolation"; "SQLite implements serializable transactions by actually serializing the writes" | sec. transactions; dat:pl:databases-and-sql:temporal |
| F4 | SQLite write-ahead logging: the original content is preserved in the database file and changes are appended to a separate WAL file | SQLite documentation, Write-Ahead Logging | https://www.sqlite.org/wal.html | 2026-09-28 | "The original content is preserved in the database file and the changes are appended into a separate WAL file" | def. write-ahead log |
| F5 | SQL:2011 provides transaction time through system-versioned tables (system-time period SYSTEM_TIME) and valid time through application-time period tables; queries use FOR SYSTEM_TIME AS OF | Kulkarni and Michels, Temporal features in SQL:2011, SIGMOD Record 41(3), 34-43, 2012 | https://sigmodrecord.org/publications/sigmodRecord/1209/pdfs/07.industry.kulkarni.pdf | 2026-09-28 | "In SQL:2011, transaction time support is provided by system-versioned tables, which in turn contain the system-time period, and valid time support is provided by tables containing an application-time period"; example "FROM Emp FOR SYSTEM_TIME AS OF" | sec. time; dat:pl:databases-and-sql:temporal |

## EXCLUDED

- Snodgrass 1999 (Developing time-oriented database applications in SQL): not fetched; not cited.
- Which commercial databases implement SQL:2011 system versioning: not fetched; the chapter names none.
- Query times are measured (bench_tradedb.py, measured_queries.csv + .meta), run while two other book agents were running.
- The regulator's request, the week's trades and the corrections are the chapter's model.
