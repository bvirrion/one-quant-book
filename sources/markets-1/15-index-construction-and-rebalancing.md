# 15. Index Construction and Rebalancing — brief and source ledger

## Brief

- **Hook.** A committee in New York adds a company to an index and forty billion dollars must buy it by Friday's close.
- **Sections.** Methodologies; The rebalance calendar; Announcement and effective dates; The index effect and its decay; The footprint of passive.
- **Defines.** index methodology, float adjustment, index reconstitution, buffer rule, index effect, demand shock, pro-forma index.
- **Tutorial.** Predict index adds and deletes from a ranked universe with buffers.
- **Build.** Reconstitution predictor.
- **Weekend problem.** Russell day — named result: the expected trade size as a multiple of average daily volume.
- **Facts to verify.** Russell reconstitution schedule and move to semi-annual; S&P inclusion criteria; Tesla S&P inclusion Dec 2020 numbers; index effect literature figures.

## Ledger

| id | claim | source | URL | accessed | evidence | used in |
|---|---|---|---|---|---|---|
| F1 | Russell US Indexes reconstitute semi-annually (June and December) from 2026; June 2026: rank day 30 April, updated preliminary lists 29 May, 5, 12, 18 June, effective after the close Friday 26 June; Russell 1000/2000 breakpoint $5.7bn, up 24%; about $12.2tn benchmarked to or invested in products based on the Russell US Indexes | LSEG / FTSE Russell press release | https://www.lseg.com/en/media-centre/press-releases/ftse-russell/2026/ftse-russell-begins-june-2026-semi-annual-russell-us-indexes-reconstitution | 2026-09-18 | "Effective this year, the reconstitution of the Russell US Indexes will again be held semi-annually in June and December"; "increased 24% to $5.7 billion" | hook; dat:m1:index-construction-and-rebalancing:rules; fig timeline; exo 4 |
| F2 | December 2026: rank day Friday 30 October, preliminary lists Friday 13 November, effective after the close Friday 11 December; "first December reconstitution in more than three decades" | LSEG / FTSE Russell press release | https://www.lseg.com/en/media-centre/press-releases/ftse-russell/2026/ftse-russell-announces-december-2026-russell-us-indexes-reconstitution-schedule | 2026-09-18 | quoted schedule | dat rules |
| F3 | S&P 500 addition guideline: total company market cap US$22.7bn or more from 1 July 2025; criteria are "for additions to an index, not for continued membership"; reviewed at the beginning of every calendar quarter | S&P DJI press release 1 July 2025 | https://press.spglobal.com/2025-07-01-S-P-Dow-Jones-Indices-Announces-Update-to-S-P-Composite-1500-Market-Cap-Guidelines | 2026-09-18 | "US$ 22.7 billion or more" | dat rules |
| F4 | FMC at least 50% of the index's minimum total cap threshold; FALR minimum lowered from 1.00 to 0.75 effective 4 Jan 2023; thresholds target about the 85th percentile of cumulative cap of the S&P Total Market Index | S&P DJI press release 4 Jan 2023 (PR Newswire) | https://www.prnewswire.com/news-releases/sp-dow-jones-indices-announces-update-to-sp-composite-1500-market-cap-guidelines-and-results-of-sp-composite-1500-index-consultation-on-market-capitalization-and-liquidity-eligibility-criteria-301713920.html | 2026-09-18 | "at least 50% of the respective index's total company-level minimum market capitalization threshold" | dat rules |
| F5 | 2020 large addition: announced 16 Nov 2020; consultation closed 20 Nov; on 30 Nov single step at full float-adjusted weight effective prior to the open of Monday 21 Dec 2020; pro-forma files after the close of Friday 11 Dec | S&P DJI press release 30 Nov 2020 | https://press.spglobal.com/2020-11-30-S-P-Dow-Jones-Indices-Announces-Implementation-of-Teslas-Addition-to-S-P-500 | 2026-09-18 | "at its full float-adjusted market capitalization weight effective prior to the open of trading on Monday, December 21, 2020" | ex:m1:index-construction-and-rebalancing:large |
| F6 | Abnormal return on S&P 500 additions fell from an average 7.4% in the 1990s to 0.3% in 2010-2020; deletions: large negative in the 1990s, 0.1% in 2010-2020; J. Finance 80(2), April 2025, 657-698 | Greenwood and Sammon, "The Disappearing Index Effect" | https://www.nber.org/papers/w30748 | 2026-09-18 | abstract; journal record https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13410 | section 4; fig event; exo 6 |

## EXCLUDED

- Dollar figures of the December 2020 addition (index-fund purchases, the day's volume, the stock's weight): seen only in news snippets, primary pages returned 403; the example uses explicit round numbers "not the provider's".
- The 16 Nov 2020 announcement date comes from the title/date of the S&P release listed in search results (nasdaq.com press-release mirror timed out); kept because the 30 Nov release refers back to it. The quarterly-expiry remark is calendar arithmetic (18 Dec 2020 = third Friday), asserted in test_solutions.
- S&P 500 profitability rule (positive GAAP earnings, last quarter and last four quarters): the methodology PDF returned 403; the dated box says only "tests of profitability and domicile".
- FALR is described in the text as annual value traded over float-adjusted capitalisation: standard definition, methodology PDF not retrievable; only the 0.75 level is sourced.
- Russell banding at +/-2.5% of cumulative capitalisation: not verified; appears only as a "what to change next" suggestion without attribution.
- The first preliminary list date (22 May 2026) appeared in a search summary but not in the fetched page; the dated box and figure use the 29 May update, which was.
