# data/markets-1 — provenance

| file | content | source | licence |
|---|---|---|---|
| venues_sample.csv | ten venues for the Chapter 4 build's tests | codes as published in the ISO 10383 MIC registry (https://www.iso20022.org/market-identifier-codes); `kind` and `fee_model` columns are this book's own coarse labels | the MIC list is published free of charge by the registration authority; this is a ten-row sample, **not** an authoritative copy — reload from the registry for production use |
| contracts_sample.csv | six futures contracts for the Chapter 18 build's tests | multipliers and ticks transcribed from the sources in `sources/markets-1/18-futures-contracts-and-exchanges.md` (exchange rulebooks and product pages); bond multipliers are expressed per price point (face 100,000 = 1,000 per point) | facts, not a database; a six-row sample for tests, **not** reference data — load the exchange's own files in production |
| sessions_sample.csv | trading sessions of three index futures for the Chapter 22 build's tests | FESX and HSI hours transcribed from the exchanges' product pages (see `sources/markets-1/22-*.md`); the ES row is an assumption made for the tests and says so | facts; a test fixture, not a holiday-aware calendar |
