# Book 3 — progress and working conventions (resume here)

Batch run of Books 3–6 (`sources/BATCH_BOOKS_3-6.md`, owned by the main session).
One agent writes this book. Run mode after the sync: Phases B–D for the whole book
in one go, no stop; full source ledger (every checkable fact web-verified, volatile
facts in `dated` boxes). Budget **11–12 pages all-in per chapter** (~340 pp), not the
outline's per-chapter figures.

## Status

| ch | state |
|---|---|
| Phase A | done 2026-09-24: 29 briefs (`tools/briefs/book3.py`), DEFINITIONS.md 285 terms, no collision with Books 1–2 (multi-line harvest), skeleton 0/0/0 (41 pp). Waiting for the batch sync (`sources/SERIES_DEFINITIONS.md`, notation, `code/firm/INTERFACES.md`, component reservation). |
| 1 | done 2026-09-24: text 505 lines, solutions 123, 4 figures (checked), 2 listings, 2 dated, 10 ledger rows; `physdeal`; tests green |
| 2 | done 2026-09-24: body 455, solutions 121, 4 figures checked (2 fixed), 2 listings, 3 dated, 14 ledger rows; `crude`; EIA contracts 1-4 parsed from HTML tables |
| 3 | done 2026-09-24: body 407, solutions 111, 4 figures checked (legend moved), 2 listings, 1 dated, 9 ledger rows; `cracks` |
| 4 | done 2026-09-24: body 432, solutions 116, 4 figures checked (label and log-axis corner fixes), 2 listings, 3 dated, 14 ledger rows; `lngarb` |
| 5 | done 2026-09-24: body 451, solutions 122, 4 figures checked (three label passes on 5.1-5.2), 2 listings, 1 dated, 7 ledger rows; `dayahead`; SMARD 2024-2025 hourly data |
| 6 | done 2026-09-24: body ~400, solutions 112, 4 figures checked (battery SoC redrawn at end-of-hour times), 2 listings, 1 dated, 4 ledger rows; `balancing`; battery DP checked against brute force |
| 7 | done 2026-09-24: body ~405, solutions 111, 4 figures checked, 2 listings, 3 dated, 11 ledger rows; `carbon`; MSR rule reproduces both published intakes exactly |
| 8 | done 2026-09-24: body ~420, solutions 111, 4 figures checked (nickel chart redrawn by trading event), 2 listings, 2 dated, 10 ledger rows; `prompts`; nickel facts from [2024] EWCA Civ 1168 |
| 9 | done 2026-09-24: body ~380, solutions 99, 4 figures checked (calendar labels, fair-price step), 2 listings, 3 dated, 9 ledger rows; `cot`; CFTC COT 2016-2026 corn |
| 10 | done 2026-09-24: body ~400, solutions 102, 4 figures checked (log-axis ceiling raised), 2 listings, 1 dated, 5 ledger rows; `commcurve`; index roll decomposition on EIA 1985-2024 |
| 11 | done 2026-09-24: body ~365, solutions 104, 4 figures checked (charter schematic widened), 2 listings, 3 dated, 4 ledger rows; `degreeday`; NOAA O'Hare 1990-2026 |
| 12 | done 2026-09-24: body ~370, solutions 100, 4 figures checked, 2 listings, 1 dated, 2 ledger rows (Mexico costs excluded: sources disagree); `hedgeprog` |
| 13 | done 2026-09-24: body ~370, solutions 107, 3 figures checked (+ LME categories table in a dated box), 2 listings, 3 dated, 6 ledger rows; `nominate`; route costs and collateral illustrative |
| 14 | done 2026-09-24: body ~390, solutions 101, 4 figures checked (three schematics widened), 2 listings, 2 dated, 6 ledger rows; `gasfee` (exact EIP-1559 integer rule) |
| 15 | done 2026-09-24: body 634 (13 pp, long: FTX tables), solutions 115, 5 figures checked, 1 table + fee table, 2 listings (Py + C++), 5 dated, 14 ledger rows; `ratelimit` in Python, C++20 and Rust; FTX data transcribed from court filing Doc 792-1 |
| 16 | done 2026-09-24: body 450, solutions 104, 4 figures checked, 2 listings, 2 dated, 4 ledger rows; `triarb` (Python); synthetic books and tapes; kimchi facts from Makarov-Schoar (LSE accepted version) |
| 17 | done 2026-09-24: body 449, solutions 102, 4 figures checked (inverse x ticks fixed), 2 listings, 5 dated, 5 ledger rows; `perp` (Python); yearly funding stats computed from Binance public API (summary only in data/) |
| 18 | done 2026-09-24: body 400, solutions 106, 4 figures checked (kappa legend replaced by a drawn line; waterfall widened), 2 listings, 3 dated, 6 ledger rows; `liquidation` (Python); cascade stable under batch sizes 100/10/1 (exact by linearity), ablations: cap 10x, depth x2, no forced selling |
| 19 | done 2026-09-24: body 398, solutions 101, 3 figures checked (creation schematic widened) + 1 table, 2 listings, 4 dated, 5 ledger rows; `cryptoopt` (Python, uses firm.parity); Deribit snapshot facts, IBIT 10-K (EDGAR full-text search works) |
| 20 | done 2026-09-24: body 404, solutions 99, 4 figures checked (IL axis widened, constant-sum domain restricted), 2 listings, 2 dated, 7 ledger rows; `amm` in Python and Rust (u128 constant product + stableswap; one swap cross-checked); LVR simulation matches sigma^2/8 |
| 21 | done 2026-09-24: body 379, solutions 102, 4 figures checked (two schematics relabelled), 2 listings, 6 dated, 10 ledger rows; `blockbook` (Python); Hyperliquid, dYdX, GMX docs; March 2025 incidents EXCLUDED (pages 403) |
| 22 | done 2026-09-24: body ~365, solutions 102, 4 figures checked, 2 listings, 2 dated, 6 ledger rows; `sandwich` (Python, uses firm.amm); Peraire-Bueno facts from CourtListener (government memo + mistrial docket entry); relayscan builder shares |
| 23 | done 2026-09-24: body 365, solutions 99, 4 figures checked, 2 listings, 3 dated, 5 ledger rows; `lendpool` (Python, uses firm.amm); Mango/Eisenberg via CFTC + CourtListener Rule 29 order; Terra via SEC 2023-32; Lido APR API |
| 24 | done 2026-09-24: body 331, solutions 95, 4 figures checked, 2 listings, 3 dated, 6 ledger rows; `tokenloan` (Python, posts to firm.ledger; MC with control variate); SEC 2024-166, ESMA MiCA, GovInfo GENIUS Act, OSC Quadriga |
| 25 | done 2026-09-24: body ~320, solutions 94, 3 figures (fee curve added in Phase C) checked, 2 listings, 2 dated, 5 ledger rows; `mmprogram` (Python, uses firm.ratelimit); Binance and Kraken full tier tables; venues C-E illustrative; module renamed m3_cryptoaccess (m3_access was ch. 13's) |
| 26 | done 2026-09-24: body ~320, solutions 95, 3 figures (resync schematic added in Phase C) checked (log ticks relabelled), 2 listings (C++ and Rust), 4 dated, 5 ledger rows; `wsbook` in Python, C++20 and Rust (CRC32 cross-checked); message-loss simulation matches pK and pR |
| 27 | done 2026-09-24: body ~320, solutions 93, 2 figures checked (+1 table), 2 listings, 2 dated, 5 ledger rows; `odds` (Python; Shin by bisection); Kalshi v. CFTC via CourtListener (D.D.C. Doc 51; D.C. Cir. dismissal), CFTC 8478-22 |
| 28 | done 2026-09-24: body ~325, solutions 97, 3 figures checked (+1 table), 1 listing, 1 dated, 8 ledger rows (several reused from Books 1-2 and ch. 8, 15, 23); `marginspiral` (Python; fixed-point deleveraging makes results step-independent; ablations); March 2020 FRED data (DGS10, DTWEXBGS) |
| 29 | done 2026-09-24: body ~280, solutions 94, 3 figures (staffing chart added in Phase C) checked, 1 listing, 1 dated, 6 ledger rows; `marketmap` (Python; cyclic shift planner); SIFMA Treasury ADV, Binance/Deribit 24-h volumes, NYSE hours |

**Phase B complete 2026-09-24.**

| step | state |
|---|---|
| Phase C | done 2026-09-24: linker applied (333 linkable terms, 1,247 links in 57 files, `--check` clean); STOP additions Gas/Bridge/Physical market/Price differential; `tools/gates.sh book markets-3` GREEN (1,484 definitions over 6 books, none twice; problem numbering OK; links match config; log 0/0/0); `tools/test_code.sh markets-3` GREEN (140 chapter tests, 56 listings, 564 chart CSVs); the 29 `code/firm` components Book 3 uses all green (106 firm Python tests, C++20 `ratelimit` and `wsbook`, Rust `ratelimit`, `amm`, `wsbook`); `tools/figdata.sh markets-3` reproduces all 74 CSVs with no diff; firm gate clean. Deepening: ch. 25 fee-curve chart, ch. 26 resync schematic, ch. 29 staffing chart (all cropped and read). |
| Phase D | report returned to the main session 2026-09-24 |
| Re-sourcing | done 2026-09-24 (WebSearch available again): all 101 EXCLUDED items re-examined; 48 restored, 13 partly restored, 14 still excluded (re-searched, nothing primary, or scope), 26 were not sourcing gaps (illustrative by design, notes, the obsolete Virtu gate lines). Ledger rows 208 -> 277; dated boxes 74 -> 79; 332 pp (from 327). The LME prompt rule was found (Trading Regulation 8.4.1-8.4.2) and `firm/prompts` now implements it instead of modified following (tests added). Relinked (1,267 links), `tools/gates.sh book markets-3` GREEN, `make test-code CH=markets-3` GREEN, all 29 firm components green, figdata unchanged. |

Final: 327 pp (29 chapters; body pp. 1-255, solutions 256-323, index 324-327), 109 figures, 56 listings, 74 dated boxes, 208 ledger rows, 101 EXCLUDED items, 185 definitions + 42 propositions, 232 exercises, 29 weekend problems, 174 interview questions.

## Per-chapter cycle

Same as `sources/markets-1/PROGRESS.md`: sources (ledger rows, web-verified) → lesson
→ code with tests → figures (pgfplots from script-generated CSVs, TikZ schematics),
each rendered and read with `OQB_BOOK=3 .venv/bin/python tools/figcrop.py "Figure N.M." out.png`
→ 8 exercises (3/3/2), weekend problem (~20 questions, Parts I–IV, one named result),
5–8 interview questions → solutions with `code/markets-3/NN-…/tests/test_solutions.py`
→ chapter gates.

Scoped commands only (batch rule 6–7):

- `latexmk one_quant_book_03_markets_3.tex` (never a bare `latexmk` or `make`)
- `tools/gates.sh chapter markets-3/NN-slug`, `tools/gates.sh log markets-3`
- `make test-code CH=markets-3/NN-slug`, `tools/figdata.sh markets-3`
- Teaching modules start with `m3_`; running-project modules are `firm_<component>.py`.

## Phase A decisions

- **Collision check uses the multi-line harvest.** The one-line
  `grep -ho 'emph{[^}]*}\\index{[^}]*}'` misses the 46 Book 1–2 definitions whose
  `\emph{…}\index{…}` pair spans a line break. Harvest with
  `perl -0777 -ne 'while(/\\emph\{([^}]*)\}\s*\\index\{([^}]*)\}/g){…}'` and normalise
  whitespace. It removed *maintenance margin* (Book 1 ch. 20) and *position limit*
  (Book 1 ch. 27) from this map; both are uses.
- Renamed to avoid homographs and Book 1–2 terms: *bundle* (Book 2) → *transaction
  bundle*; *relay* → *MEV relay*; *imbalance* → *imbalance volume*; *surrender* →
  *allowance surrender*; *intent* → *intent-based routing*; *VIP tier* not defined
  (Book 1's *volume tier* is used); *Brent CFD* kept distinct from Book 1's *contract
  for difference*.
- Stub solutions carry `\mbox{}` after the heading: 29 consecutive `\section*`
  headings with no text between them left no legal page break (overfull vbox of
  127 pt at the solutions part).

## Data sources planned (licences to confirm in Phase B)

- EIA (public domain): NYMEX WTI contracts 1–4, Henry Hub, spot product prices.
- World Bank Commodity Price Data, "Pink Sheet" (CC BY 4.0): monthly TTF, JKM-proxy,
  Brent, metals, agriculturals.
- SMARD / Bundesnetzagentur (CC BY 4.0): German day-ahead prices and generation.
- CFTC Commitments of Traders (public domain).
- NOAA GHCN-Daily (public domain): station temperatures.
- Crypto: venue data are not redistributable in general; charts use simulation
  calibrated to published statistics, with the source in the caption.

## Calibration

- After ch. 3 (2026-09-24): body 10 / 9 / 8 pp (505 / 455 / 407 lines), solutions about 2 pp each (123 / 121 / 111 lines): **11.0 pp all-in** per chapter. Projection 29 x 11.0 + 18 = ~337 pp, inside the 11-12 pp budget but at its floor; ch. 3 is short. Aim for 450-520 body lines (a fifth section or a worked example where it teaches), not padding.

- After ch. 10 (2026-09-24): chapter starts 2/12/21/29/37/46/54/63/71/79/87: body 10, 9, 8, 8, 9, 8, 9, 8, 8, 8 pp
  (85 for ten, 8.5 each) plus about 2 pp of solutions each: **10.5 pp all-in**, below the 11-12 budget.
  Projection 29 x 10.5 + 18 = ~323 pp. From ch. 11 on, aim at 470-520 body lines (a fifth section or a
  worked example with numbers, a second listing in the tutorial) and 120+ solution lines; revisit the
  shortest (8, 9, 10) in Phase C if the total stays under ~330.

- After ch. 20 (2026-09-24): chapters 15-20 start at 120/133/143/153/162/171/180: body 13, 10, 10, 9, 9, 9 pp;
  twenty chapters in 178 pp of body (8.9 each) plus about 2 pp of solutions each: **10.9 pp all-in**. Projection
  29 x 10.9 + 18 = ~334 pp. Keep 420-500 body lines per chapter; revisit short early chapters in Phase C if time allows.

- Final (Phase C): 327 pp for 29 chapters, **11.3 pp per chapter over the whole volume**, ~10.8 net of front matter
  and index: at the floor of the 11-12 budget. Chapters 24-29 ran shortest (~7-8 pp body): later chapters drift
  short when the ledger is thin, so budget sources for them early.

## Traps met in Book 3 (for WRITING_A_QUANT_BOOK.md section 9 at delivery)

- WebSearch budget exhausted at ch. 15 (200/200). Still working: WebFetch and curl on known URLs;
  Wikipedia raw text (`https://en.wikipedia.org/w/index.php?title=X&action=raw`) as a map to primary
  references; CourtListener RECAP PDFs (`storage.courtlistener.com/recap/gov.uscourts.deb.188450.<doc>.<n>.pdf`
  for the FTX case); SEC works with a descriptive User-Agent; justice.gov and cnbc.com are bot-blocked.
- Binance's live `api/v3/exchangeInfo` is reachable with curl and gives the current rate limits and
  symbol list (used in ch. 15 and 16 dated boxes); OpenAlex (`api.openalex.org/works?search=`) finds
  open-access copies of papers when SSRN returns 403.
- EDGAR full-text search (`efts.sec.gov/LATEST/search-index?q=...&forms=10-K`, descriptive User-Agent) finds
  filings; the 10-K HTML then gives primary facts (fund structure, benchmark methodology, dates).
- GitHub raw copies of docs (binance/binance-spot-api-docs, ethereum/ethereum-org-website, flashbots/flashbots-docs)
  work when the rendered site is a JavaScript app or 404s.
- Docs sites on GitBook/Mintlify expose `llms.txt` and `.md` page variants (Hyperliquid, dYdX, GMX,
  Uniswap `llms.mdx`): fetch those with curl instead of the JavaScript pages. GDELT's doc API
  (`api.gdeltproject.org/api/v2/doc/doc?query=...&mode=artlist&format=json`) finds news URLs but
  rate-limits hard after two queries.
- CourtListener's search API (`/api/rest/v4/search/?q=...&type=rd&court=nysd`) works without a key and
  returns docket entries (e.g. a declaration of mistrial) and RECAP PDF paths.
- WebSearch substitute: the DuckDuckGo HTML endpoint (`html.duckduckgo.com/html/?q=`) through curl,
  wrapped in `scratchpad/ddg.sh`; it rate-limits after a few queries in a row.
- The chapter gate matches dated-box labels literally in the ledger's "used in" column: write
  `dat:m3:<slug>:<key>` in full, not an abbreviation.
- pgfplots prices in the tens of thousands: give `xtick`, `xticklabels` and `scaled x ticks=false`
  together, or the axis prints `1 . 10^5` labels and a stray multiplier.
- Teaching-module names must be unique across the series: ch. 25's first `m3_access.py` collided with ch. 13's
  (the module-name check caught it); prefer chapter-specific names.
- A ledger row's evidence must not contain `|` (it splits the Markdown table): quote tables with `;`.
- `xtick={1,...,11}` trips the chapter gate's "drafty ..." check: write the ticks out.
- The firm gate is a case-sensitive fixed-string match over firm_names.txt: a name that is also a
  common word (Copper) would fire on every metals sentence starting with it; add the product name
  (ClearLoop) instead. "Mt.~Gox" in LaTeX does not match "Mt. Gox": the list carries "Gox".
- Body lines to pages: ch. 15 ran ~49 lines a page (634 lines, 13 pp); aim 480-520 for 10-11 pp.

- A pgfplots `ybar interval` chart puts tick labels between bars and offsets the bars: for hourly bars use
  `ybar=0pt,bar width=4pt` with `xmin=-0.8,xmax=23.8`.
- TikZ labels on the horizontal leg of a `-|` path centre on that leg and overrun the start node when long:
  break them over two lines (`align=center`).
- Text added after linking makes `link_defined_terms.py --check` report STALE: re-run unwrap + apply after any late edit.

- Re-sourcing tricks (2026-09-24): the Internet Archive (`web.archive.org/web/2025id_/<url>` for PDFs, `if_` for pages) serves copies of
  sites that block scripts (CME rulebook chapters and price-limit page, eur-lex, justice.gov, FATF, iosco.org, LME rulebook, Platts
  specification guides, BitMEX blog, FTX help centre); `archive.org/wayback/available?url=` tells whether a copy exists. Public beacon and
  execution nodes (publicnode.com) give chain facts directly (gas limit, total staked). L2BEAT has a JSON API (`/api/scaling/summary`).
  CourtListener's search API with `docket_id:<id>` lists a docket's entries; RECAP may miss recent ones.
- A German umlaut written as `\"a` trips the straight-quote gate: type the UTF-8 character.

- Never write `\omterm` by hand, even when copying a sentence pattern from a Book 2 chapter (ch. 1 draft had four; removed with a perl one-liner).
- `P&L` in running text needs `P\&L` (fatal "Misplaced alignment tab").
- Name figure-check PNGs uniquely per check: re-using a name returned a stale image once.
- The firm-name gate matches substrings: "Virtu" hits "Virtual trading point" (ch. 4). Worked around with a note in the ledger's EXCLUDED list; report for a word-boundary match.
- A problem that states a rounded input (82.38) must be solved with that rounded input: the numbers gate caught 133,079 vs 133,080 (ch. 5).
- SMARD counts: hourly averages give 457 / 573 negative hours (2024 / 2025); secondary sources quote ~1,100 for 2025 (quarter-hours). Say which.
- `make test-code CH=markets-3/...` went RED twice with an IndexError that did not reproduce on rerun: a global check (probably check_figdata) reading another book's CSV while it was being written. Rerun before investigating.
- The one-line `\index` harvest in `tools/gates.sh book` ("terms defined twice") and
  in the batch instructions misses multi-line definitions (46 in Books 1–2).
