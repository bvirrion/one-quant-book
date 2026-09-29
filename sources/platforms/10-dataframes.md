# 10. Dataframes — brief and source ledger

## Brief

- **Hook.** Two researchers computed the same five-minute bars from the same ticks and got different volumes: one resampled on a clock that labelled each bar by its start, the other by its end, and one of the libraries dropped the empty bars. The dataframe is the research platform's language, and its idioms are where its bugs live.
- **Sections.** The dataframe model; Eager and lazy evaluation; Query plans and optimisation; Out-of-core and streaming execution; Idioms for market data.
- **Defines.** dataframe, eager evaluation, lazy evaluation, query optimiser, out-of-core processing, streaming execution, window function, long format, wide format.
- **Uses (defined earlier).** bar (B7.2), time bar (B7.2), as-of join (B7.3), look-ahead bias (B7.3), chunked processing (ch8), peak resident memory (ch8), predicate pushdown (ch3), projection pushdown (ch3), tick store (ch4).
- **Tutorial.** Write one research pipeline -- ticks to bars, as-of join of trades to quotes, rolling features per symbol, a cross-sectional rank, a pivot from long to wide -- in pandas (eager), in Polars eager and lazy, and in DuckDB SQL over the Parquet store; print the lazy plans and see the pushdowns; run the lazy version out of core on a month of partitions; test that all versions agree, including bar labelling and empty bars. End state: a table of time and peak memory by engine and mode, and the explained plan.
- **Build.** `firm.marketdf`: market-data idioms with one contract and three implementations (pandas, Polars, DuckDB): `bars(ticks, freq, label, closed, fill)`, `asof(left, right, by, tolerance)`, `rolling(df, by, window)`, `xs_rank`, `to_wide`/`to_long`; equivalence tests on edge cases (empty bars, ties, time zones, duplicate timestamps); Python.
- **Weekend problem.** Two sets of bars -- named result: the volume and return discrepancies produced by each labelling and gap convention on a generated day, and the time and memory of the pipeline eager, lazy and out of core on a month of data.
- **Facts to verify.** pandas documentation: resample label/closed, merge_asof; Polars documentation: lazy API, streaming engine, join_asof, group_by_dynamic; DuckDB documentation: window functions, time_bucket, ASOF JOIN; Wickham 2014, Tidy data (Journal of Statistical Software).
- **Data.** The chapter 4 store; a month of generated partitions (small).

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | pandas resample: closed and label default to 'left' for all frequency offsets except 'ME', 'YE', 'QE', 'BME', 'BA', 'BQE' and 'W', which default to 'right' | pandas 3.0.6 API reference, DataFrame.resample | https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.resample.html | 2026-09-28 | "The default is 'left' for all frequency offsets except for 'ME', 'YE', 'QE', 'BME', 'BA', 'BQE', and 'W' which all have a default of 'right'." | solution exo:pl:dataframes:8 |
| F2 | Polars streaming: collect(engine="streaming") executes the query in batches, for data that do not fit in memory; operations not implemented in streaming fall back to the in-memory engine | Polars user guide, Streaming | https://docs.pola.rs/user-guide/concepts/streaming/ | 2026-09-28 | "we pass the engine="streaming" argument to collect"; "execute the query in batches allowing you to process datasets that do not fit in memory"; "Polars will fall back to the in-memory engine for those operations" | section Out-of-core; dat:pl:dataframes:versions; omsources |
| F3 | DuckDB ASOF joins look up the value of a varying property at a point in time; the common inequality is >= | DuckDB documentation, AsOf join guide | https://duckdb.org/docs/current/guides/sql_features/asof_join | 2026-09-28 | "the value of a varying property at a specific point in time"; "The inequality is >= (the most common case)"; the strict > form verified by firm.marketdf tests | listing lst:pl:dataframes:sql; omsources |
| F4 | Wickham, "Tidy Data", Journal of Statistical Software 59(10), 2014 | Crossref, DOI 10.18637/jss.v059.i10 | https://api.crossref.org/works/10.18637/jss.v059.i10 | 2026-09-28 | title "Tidy Data", author Wickham, volume 59, issue 10, issued 2014 | omsources |
| F5 | DuckDB's // is integer division (5 // 2 = 2) and truncates toward zero for negative operands (-7 // 5 = -1) | DuckDB documentation, Numeric functions; measured in test_exercise_1_and_4_edges | https://duckdb.org/docs/current/sql/functions/numeric | 2026-09-28 | "// Division 5 // 2 2"; the page says nothing on negative operands; duckdb.sql("SELECT -7 // 5") returns -1 in DuckDB 1.5.5 | listing lst:pl:dataframes:bars; exo 4 |
| F6 | Linux getrusage: ru_maxrss is the maximum resident set size; resource usage metrics are preserved across execve | Linux man-pages, getrusage(2) | https://man7.org/linux/man-pages/man2/getrusage.2.html | 2026-09-28 | "This is the maximum resident set size used (in KiB)."; "Resource usage metrics are preserved across an execve(2)." (and observed: the first measurement gave about the same peak for every engine) | rem:pl:dataframes:rss |

## EXCLUDED

- Specific DuckDB spilling and memory-limit behaviour: not claimed beyond the measured memory.
- pandas merge_asof documentation (brief): mechanism only, exercised by the tests.

