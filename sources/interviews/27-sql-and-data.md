# 27. SQL and Data — brief and source ledger

## Brief

- **Hook.** An as-of join of trades to quotes returns more rows than there were trades. The analyst who wrote it says the join is correct because every trade matched a quote; the interviewer asks what happens when two quotes share a timestamp, and the duplicate rows explain themselves.
- **Sections.** Joins and their cardinality; Window functions: rankings, running totals, gaps and islands; As-of joins and time; Array-language questions: the same answers as vector expressions.
- **Defines.** none (the chapter uses the vocabulary of Books 1-17, listed below).
- **Uses (defined earlier).** relational model (B15.25), primary key (B15.25), ACID transaction (B15.25), isolation level (B15.25), window function (B15.10), as-of join (B7.3), point-in-time data (B7.3), look-ahead bias (B7.3), array programming (B15.8), partitioning (B15.2), tick store (B15.4).
- **Question bank.** 13 questions, 4/5/4. Families: join cardinality (inner, left, anti joins; the duplicate-producing join, counted); aggregation traps (NULLs in COUNT and AVG; HAVING against WHERE); window functions (top-n per group; running P&L and drawdown; the previous trade's price with LAG; volume-weighted average price by bucket); gaps and islands (consecutive days of positive P&L; trading halts from a status table); as-of joins (last quote before each trade, ties and the strict inequality; the look-ahead version and how to see it); array-language versions of three answers (numpy/pandas/Polars: the same result by cumulative sums, searchsorted and group-by). Open tools only (DuckDB, SQLite, pandas, Polars). Roles: researcher 5, developer 5, mle 2, risk 1. Firms: systematic fund 4, market maker 3, bank 2, multi-manager fund 2, any 2.
- **Facts to verify.** DuckDB and SQLite documentation for the ASOF JOIN and window-function syntax at the pinned versions; ISO/IEC 9075 (SQL) for NULL semantics, cited through a public description.
- **Data.** Figures: none planned (small result tables printed from the tests). Code: sql/*.sql (one query per answer), python/iv_sql.py (fixture generator with planted ties and NULLs; the pandas and Polars reference answers); tests run every query on DuckDB (and SQLite where the dialect allows) and assert equality with the reference.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | DuckDB ASOF JOIN: joins each left row to the nearest right row by an inequality on an ordered column, with optional equality conditions | DuckDB documentation, ASOF join | https://duckdb.org/docs/stable/guides/sql_features/asof_join | 2026-09-29 | guide page title; behaviour asserted on DuckDB 1.5.5 by the chapter's tests (including its choice on the planted tie) | section 3; omsources |
| F2 | SQLite supports window functions from version 3.25.0 | SQLite documentation, Window Functions | https://www.sqlite.org/windowfunctions.html | 2026-09-29 | "Window function support was first added to SQLite with release version 3.25.0"; tests run on SQLite 3.37.2 | omsources |

## EXCLUDED

The data are generated (iv_sql.fixtures). DuckDB's pick at a tied timestamp is observed behaviour of version 1.5.5, stated in the text as unspecified.

