# One Quant Book 16 — The Desk and the Firm: progress

Slug `desk` (not `firm`: `code/firm/` is the running project), label prefix `fm`, teaching-module
prefix `fm_`, entry file `one_quant_book_16_desk.tex`, 30 chapters in five parts
(`part.fm.business`, `part.fm.desk`, `part.fm.control`, `part.fm.tech`, `part.fm.strategy`).
Written in the Books 14–16 batch (`sources/BATCH_BOOKS_14-16.md`), one agent per book.

## Status

| Phase | State | Date |
|---|---|---|
| A — plan | done: briefs (`tools/briefs/book16.py`), 30 ledgers with briefs, `DEFINITIONS.md` (201 terms), skeleton 0/0/0 (44 pp) | 2026-09-28 |
| sync | done (coordinator's binding decisions) | 2026-09-28 |
| B — write | done: 30 chapters, each through its gates | 2026-09-28 |
| C — whole-book passes | done: 854 term links, `gates.sh book desk` green, `make test-code CH=desk` green, figdata reproduced with no diff | 2026-09-28 |
| D — deliver | done: report handed back | 2026-09-28 |

## Phase A checks (2026-09-28)

- Definition map checked against the multi-line `\index` harvest of Books 1–13 (2,753 terms): no
  exact collision after removing *buy-in* (B1 ch. 16) and *independent amount* (B6 ch. 17), which the
  first draft had planned; both are now `uses`.
- Checked against the Books 14 and 15 draft briefs on disk: *critical path* is Book 14 ch. 6's
  (timing closure, the hardware sense), so ch. 24 defines *critical-path method*; *unit of count*,
  *market-data audit*, *derived data*, *usage report* are Book 15 ch. 23's, so ch. 22 keeps only
  the commercial terms (*data budget*, *enterprise licence*, *derived-data licence*, *redistribution
  licence*, *back-billing*). *vendor lock-in* is contested with Book 14 ch. 27 (argued for Book 16
  ch. 20 in the Phase A report). Added because the batch books use them: *four-eyes principle* (ch. 12,
  used by Book 15), *data budget* (ch. 22) and *build against buy* (ch. 20), both used by Book 14.
  *Latency tier* is defined by nobody (Book 14 ch. 9 does not index it): claimed for ch. 19.
- Every `uses` owner verified: Books 1–13 against the harvest (book and chapter), batch books
  against their draft briefs.
- The 29 running-project components checked against the 378 directories of `code/firm/`: none exists.

## Calibration target

10.5–12 pages a chapter all-in (≈ 450–550 body lines, 160–200 solution lines); book ≈ 330–360 pages
against the outline's ~400. Checkpoints at ch. 10 and ch. 20; a projection more than 15 % under the
outline means chapters are being compressed.

## Case studies already told in the series (re-read here for the firm-level decisions only)

| Episode | Where it is already told | This book's angle |
|---|---|---|
| August 2007 | B7 ch. 28 (unwind model, factor losses), B8 ch. 1 and 28 | ch. 28: sell or hold, funding terms; reuse `firm.capacity.unwind` |
| 1 Aug 2012 software incident | B11 ch. 27 (controls simulation), B13 ch. 22 | ch. 29: the rescue financing, dilution, merger |
| Archegos 2021 | B1 ch. 6 (example), B6 ch. 22 (stress) | ch. 29: the prime brokers' exit race, static against dynamic margin; ch. 14, 18 |
| FTX 2022 | B3 ch. 15 (shortfall data), B3 ch. 24 | ch. 29: governance and counterparties' decisions; reuse B3's derived data |
| LME nickel 2022 | B3 ch. 8 and 28 | ch. 29: the exchange's decision, FCA 2025 final notice, the 2023 judicial review |
| London Whale 2012 | B6 ch. 26 (model), ch. 27 (price testing) | ch. 12: pointer only; ch. 12's hook is the Lehman examiner's report instead |
| Rogue trading cases | B6 ch. 28 | not repeated |
| cum-ex | B1 ch. 16 (BGH 2021) | ch. 15: the Danish refund scheme's court record |

## Source plan

Most source-heavy chapters: 17 (regimes in six jurisdictions), 28–29 (seven case records), 1 and 5
(filings, several years each), 4, 10, 11, 12, 13, 15, 16, 18, 22, 23, 27, 30. Primary URLs fetched
directly wherever known (EDGAR with a name-and-email user agent, GAO, SEC litigation, FCA final
notices, CourtListener RECAP, govinfo for Senate reports, Companies House filing history, eCFR,
legislation.gov.uk). Reusable ledger rows already in the series: Knight order (hft/27 F1–F2), Archegos
report (markets-1/06 F1–F2), FTX shortfall (markets-3/15 F5–F6), LME nickel (markets-3/08 F1).

Fetch checks done in Phase A (no web search used): SEC 34-70694 PDF (200), GAO/GGD-00-3 PDF (200),
FCA final notice to the LME 2025 PDF (200), Federal Reserve enforcement PDF (200), CourtListener
search API (200), Companies House search and filing-history PDFs (200). Refused or moved:
treasury.gov PWG report (timeout), IAPD brochure URL form (403 — use the brochure link from the
firm's IAPD page), sec.gov Archives with a browser user agent (403 — use the name-and-email agent),
hsgac.senate.gov (403 — use govinfo), credit-suisse.com (403 — the SEC comment-file copy that
Book 1's ledger used works), judiciary.uk guessed path (404 — find the neutral citation on BAILII
or the National Archives' Find Case Law).

Search-budget estimate: about 450 searches (18 heavy chapters × ~18, 12 light × ~7, ~40 for
re-verification of dated boxes).

## Data plan (`data/desk/`, all small derived tables, `LICENSES.md`)

`filings_*.csv` (ch. 1–2, 19), `vix_annual.csv` (ch. 1), `form_pf_liquidity.csv` (ch. 4),
`bank_segments.csv` (ch. 5), `regmap.csv` (ch. 17), `tech_spend.csv` (ch. 19), `case_ltcm.csv`,
`case_amaranth.csv` (ch. 28), `case_knight.csv`, `case_archegos.csv`, `case_nickel.csv` (ch. 29),
`concentration.csv` (ch. 30). Each row carries its source document and page.

## Firm names to append to `tools/firm_names.txt` (Phase B, append-only, `# Book 16:`)

Long-Term Capital, Amaranth, KCG, GETCO, Investment Technology Group, Woodford, Link Fund Solutions,
H2O, Teza, Solo Capital, London Metal Exchange, Paul, Weiss (as a report author only), Oliver Wyman,
Blackstone, Investcorp — only those the text actually names.

## Defects and notes for the main session

- `sources/BATCH_BOOKS_14-16.md`, "Operations and post-trade": says `firm.recon` is there to build
  on for reconciliation. `code/firm/recon/firm_recon.py` is Book 1 ch. 15's **index-reconstitution
  predictor**, not reconciliation; no existing component reconciles positions or cash
  (`firm.tradecontrol` flags suspicious bookings, `firm.ledger` posts revenue and costs).

## Traps met in Phase A

- A draft definition map built only from the outline planned two terms that earlier books own
  (*buy-in*, *independent amount*) and one that a batch book defines in another sense
  (*critical path*): run the harvest and read the other batch books' briefs before reporting.

## Phase B chapter log

Searches used (WebSearch tool calls, running): 3 after ch. 2; 5 after ch. 4; 7 after ch. 10; 9 after ch. 11; 11 after ch. 13; 12 after ch. 14; 13 after ch. 15; 14 after ch. 17; 15 after ch. 18 (most facts fetched
directly from primary URLs: EDGAR, eCFR, legislation.gov.uk, publications.europa.eu, FCA, IAPD, Crossref, OpenAlex).

| ch. | body / sol. lines | figures | listings | dated | ledger | tests (ch + firm) | notes |
|---|---|---|---|---|---|---|---|
| 1 | 489 / 101 | 5 | 2 | 2 | 12 | 7 + 4 (firmecon) | Virtu 10-K 2019-25 via EDGAR text + XBRL companyfacts; Man Group results PDFs; GS 10-K 2025 segment; VIX yearly means |
| 2 | 414 / 105 | 5 | 2 | 2 | 12 | 5 + 5 (partnership) | IFR/IFD via legislation.gov.uk `/adopted` and publications.europa.eu CELEX; 15c3-1 via eCFR `--compressed`; Flow Traders AR 2025 |
| 3 | 380 / 95 | 4 | 1 | 1 | 4 | 7 (3 reference) + 5 (podshop) | Millennium ADV Part 2A via IAPD API (`api.adviserinfo.sec.gov/search/firm/<crd>` -> brochure id -> files.adviserinfo.sec.gov); drawdown thresholds EXCLUDED |
| 4 | 397 / 101 | 3 | 1 | 2 | 6 | 6 (1 reference) + 3 (fundterms) | FCA Woodford press releases; SEC Private Funds Statistics 2025Q3; UCITS art. 84 via CELEX; 22e-4, 22c-1 via eCFR |
| 5 | 381 / 98 | 4 | 1 | 1 | 6 | 4 + 3 (bankdesk) | JPMorgan 10-K 2025 (capital allocation method, CIB equity, CET1/SLR, eSLR final rule) |
| 6 | 333 / 93 | 3 | 1 | 0 | 2 | 5 (1 reference) + 3 (deskplan) | FSB RAF principles 2013; OCC Bulletin 2017-43 |
| 7 | 380 / 99 | 4 | 1 | 0 | 2 | 5 (3 reference) + 4 (limitalloc) | bibliographic; BCBS 2009 EXCLUDED (bis.org refuses scripts) |
| 8 | 349 / 98 | 3 | 1 | 0 | 3 | 6 (4 reference) + 3 (ddrules) | bibliographic (Crossref, arXiv) |
| 9 | 341 / 95 | 4 | 1 | 0 | 4 | 5 (1 reference) + 3 (projsel) | bibliographic |
| 10 | 342 / 98 | 3 | 2 | 1 | 7 | 4 (1 reference) + 4 (bonuspool) | CRD IV/V via CELEX; FCA PS23/15; EBA high earners (WebFetch); 10D-1 via eCFR; OpenAlex abstract for Sackett et al. |
| 11 | 409 / 107 | 4 | 1 | 2 | 8 | 5 + 3 (gardenleave) | Aleynikov (2d Cir.) via CourtListener PDF; Pub. L. 112-236 via govinfo; 18 USC 1836/1839 via LII; EU 2016/943 CELEX; UK SI 2018/597; FTC rule page; Jane Street v. Millennium RECAP complaint + stipulation. Tullett Prebon (BAILII 403) EXCLUDED |
| 12 | 395 / 111 | 4 | 2 | 1 | 9 | 6 + 4 (escalation) | Valukas report vol. 1 via a Stanford mirror (jenner.com copy gone); 12 CFR 252.31/.33 via eCFR; SSG 2008 via newyorkfed.org. BCBS 2015 EXCLUDED (bis.org); London Whale left to Book 6 |
| 13 | 381 / 105 | 4 | 2 | 2 | 8 | 6 + 3 (opsmetrics) | SEC 34-96930 PDF; 15c6-1/15c6-2 via eCFR; DTCC after-action press release (WebFetch; the report PDF 404s); CSDR 2017/389, 2021/70, 2023/2845, 2025/2075 via CELEX. UK T+1 and collateral-dispute statistics EXCLUDED |
| 14 | 374 / 104 | 4 | 2 | 2 | 4 | 6 + 4 (treasury) | BIS press release and FSB page via WebFetch (bis.org, iosco.org, fsb.org PDFs refuse scripts); Reg T via eCFR; FINRA 4210 via finra.org. Archegos and LBIE left as pointers |
| 15 | 364 / 101 | 3 | 1 | 1 | 7 | 5 + 3 (signoff) | UK judgment [2025] EWHC 2364 (Comm) via judiciary.uk PDF (326 pp); 26 USC 1256/1091 via LII; GOV.UK stamp duty; OECD TP 2022 via Crossref. French/Italian FTT and the Glostrup judgment EXCLUDED |
| 16 | 344 / 103 | 4 | 2 | 2 | 9 | 4 + 3 (compliance) | FCA CGML press release (2022); MAR via CELEX; 10b-5 and 204A-1 via eCFR; 15(g) via LII. UK MAR, PA-dealing enforcement case EXCLUDED; alert stream from firm.surveil (Book 9) |
| 17 | 361 / 103 | 4 | 1 | 3 | 10 | 3 + 2 (regmap) | MiFID II via CELEX; FSMA s.19/55V via legislation.gov.uk; Exchange Act 15, Advisers Act 203 via LII; 15b9-1 via eCFR; NFA and SFC pages. Map as data in data/desk/regmap.csv (LICENSES row). MAS, FIEA EXCLUDED |
| 18 | 341 / 107 | 3 | 1 | 1 | 4 | 5 + 3 (docterms) | Lomas [2012] EWCA Civ 419 via caselaw.nationalarchives.gov.uk (works for pre-2022 judgments); Metavante via Davis Polk memo (transcript not found); 12 CFR 252.83/84 and 17 CFR 22.2 via eCFR. ISDA texts EXCLUDED. Trap: \foreach with axis cs inside a pgfplots axis fails (illegal parameter) -- write the draws out |
| 19 | 334 / 102 | 4 | 1 | 1 | 6 | 7 + 3 (techtier) | Virtu comm&data from data/desk/filings_virtu.csv; Flow Traders AR 2025; Budish et al. and Aquilina et al. via Crossref + OpenAlex abstracts; tier venue fees read from Book 14 firm.colobill (its ch. 9 ledger F3/F5) pending connplan. Bank run/change split EXCLUDED |
| 20 | 315 / 100 | 4 | 2 | 0 | 4 | 6 + 3 (buildbuy) | Virtu 8-Ks (Nov 2018, Mar 2019) via EDGAR index.json; Dixit-Pindyck via Crossref; Boehm via Open Library. Trap: a grouped xbar tornado misaligns bars -- draw ranges with thick x error bars (draw=none, mark=none) |
| 21 | 322 / 102 | 3 | 1 | 1 | 5 | 5 + 2 (teamtopo) | Conway 1968 from the author's reprint; SRE on-call from sre.google; MacCormack et al. via Crossref; Accelerate and Team Topologies via Open Library |
| 22 | 312 / 100 | 3 | 1 | 1 | 3 | 6 + 3 (databudget) | FCA WDMS report PDF (fca.org.uk); MiFIR art. 13 via CELEX; Rule 614 via eCFR; fee levels illustrative (Nasdaq data policy PDF unreachable). Trap: the chapter gate requires a tutorial section -- one chapter drafted without it failed |
| 23 | 300 / 96 | 3 | 1 | 1 | 4 | 6 + 2 (dealterms) | Nasdaq QMM filing via federalregister.gov full text; Nash 1950 via Crossref; Fisher-Ury and Raiffa via Open Library. Consolidated volume and all costs are inputs |
| 24 | 316 / 100 | 3 | 2 | 0 | 3 | 6 (1 reference) + 3 (entryplan) | Flow Traders AR 2025 (Asia/China); Kelley-Walker via Crossref. Log gate: a 3 pt overfull vbox in the one-page index (known transient, WRITING section 9); recheck after ch. 30 |
| 25 | 322 / 98 | 3 | 1 | 1 | 2 | 4 + 2 (fundlaunch) | SEC marketing rule via eCFR; Aggarwal-Jorion via OpenAlex (title only). No-action letters, PFS size, AIMA DDQ EXCLUDED. Trap repeated: a "%" (and a "$") in a CSV label broke a chart -- sanitise labels in every fig script |
| 26 | 296 / 99 | 3 | 1 | 0 | 5 | 6 + 3 (decisionlog) | Mellers et al. 2014 abstract via OpenAlex; Brier, Murphy, Satopaa, Baron-Hershey via OpenAlex. Trap: test-code rejects a listing over 40 lines (47) -- the chapter gate does not |
| 27 | 279 / 103 | 2 | 1 | 1 | 4 | 5 + 3 (crisisdrill) | CFTC MF Global releases 6776-13, 6904-14, 7508-17; BoE gilt operation release (2022). SIPA trustee report and LDI link EXCLUDED |
| 28 | 351 / 107 | 4 | 1 | 1 | 8 | 5 + 4 (casebook part 1) | GAO/GGD-00-3 PDF (GAO needs the name-and-email UA); PSI hearing S. Hrg. 110-235 via govinfo (the $2bn loss and the no-Fed-intervention line are Senator Coleman's opening statement, not the chairman's); Goldman 8-K Ex 99.1 via EDGAR; Khandani-Lo abstract via Crossref (OpenAlex had none). PWG report, CFTC/FERC Amaranth actions EXCLUDED. Trap: nodes-near-coords labels in grouped ybar overlap unless bar width ~17pt and \tiny labels |
| 29 | 370 / 107 | 4 + 1 table | 1 | 1 | 12 | 7 + 6 (casebook part 2) | Knight 10-Q/8-Ks and KCG 8-K12G3 via EDGAR submissions API; CS Archegos report full text (SEC comment-file PDF); Fed press release (URL is enforcement20230724a.htm); DOJ SDNY sentencing release refused by curl and WebFetch -- Internet Archive copy worked (1 WebSearch); FCA final notice PDF at /publication/final-notices/london-metal-exchange-2025.pdf; CA judgment via LME's PDF. Reused Book 3's FTX data. Traps: `{1,...,7}` in a tick list trips the drafty gate; `\node` inside a `ybar stacked` axis is hidden under the bars -- define coordinates in the axis and draw the nodes after it; a table must use `\caption`, not `\omcaption` (which numbers it as a figure) |
| 30 | 355 / 105 | 4 | 2 | 1 | 11 | 6 + 4 (moats) | Order Competition Rule and its 2025 withdrawal via federalregister.gov API (`fields[]=raw_text_url`; the text is 1 MB, search it in Python since ugrep's long regexes hit complexity limits); 2023 Merger Guidelines PDF from ftc.gov (justice.gov refuses); Virtu 8-K July 2017 via EDGAR submissions; Franklin OnChain prospectus via EDGAR full-text search (efts.sec.gov/LATEST/search-index); 24X order 34-101777 via federalregister; DTCC 24x5 release (1 WebSearch). Named result: six firms and HHI 1,667 at F = $50m; nine and 1,111 when F halves |

Fetch tricks that worked: eCFR versioner API needs `curl --compressed`; legislation.gov.uk EU texts at
`/eur/<year>/<n>/article/<k>/adopted`; Companies House accounts are scanned images (no OCR tool here: render
with pdftoppm and read the page image).

Trap (ch. 4): a `%` inside a chart-CSV label ("gate 10%") comments out the rest of the row in pgfplots; the chart silently
plotted another row's values. `check_figdata.py` does not catch it. Never write `%` into a figdata CSV.

Trap (ch. 5): in an `xbar stacked` axis every `\addplot` is stacked, including an `only marks` series of actual
values; plot such markers on a second, `hide axis` axis with the same geometry.

## Checkpoint at ch. 10 (2026-09-28)

Body pages per chapter 11, 10, 9, 10, 10, 8, 9, 9, 8, 8 (92); solutions exactly 2 pages each (20): **11.2 pages all-in
per chapter**. Projection: 30 x 11.2 + ~15 front and back matter = **~350 pages** against the outline's ~400 (-12 %,
inside the 15 % rule). Chapters 6-10 ran at 8-9 body pages from 340-380 body lines; aim for 400-450 lines (a fifth
section or a second worked example) in the case-study and regulation chapters, which carry more sourced material.

## Checkpoint at ch. 20 (2026-09-28)

Body pages per chapter 11-20: 10, 10, 10, 10, 9, 8, 9, 9, 8, 8 (91); chapters 1-20 average 9.2 body pages plus 2 pages of
solutions. Projection: 30 x 11.2 + ~15 front and back matter = **~350 pages** against the outline's ~400 (-12 %, inside the
15 % rule, unchanged from ch. 10). Chapters 15-20 ran at 315-365 body lines; for 21-30 keep at least 350 lines and four
figures, and give the two case-study chapters (28-29) their full sourced length.
Searches: 15 WebSearch calls after ch. 20; 16 after ch. 22; 17 after ch. 23; 18 after ch. 27; 20 after ch. 28; 21 after ch. 29; 22 after ch. 30 (budget ~450 accepted; actual use is far below because primary URLs are fetched
directly).

## Phase C (2026-09-28)

- Term links: `link_defined_terms.py --book 16 --unwrap --apply` then `--apply`: 244 linkable terms, 854 links in 56
  files, none defined twice (3,268 definitions over 16 books). The inherited STOP/DROP lists were reviewed against the
  per-term tally (net trading revenue 33, bus factor 25, risk committee 21, ...); no Book 16 term needed a STOP entry:
  the one-word candidates (authorisation, custodian) occur only in their regulatory and fund senses.
- `tools/gates.sh book desk`: green (30 chapters, duplicate labels, terms defined twice, problem numbering, links match
  the config, log 0/0/0).
- `make test-code CH=desk`: green after three over-long lines in fig scripts (ch. 4, 20, 25, written when CSV labels
  were sanitised) were split; ruff clean over code/desk and code/firm. 156 chapter tests (14 marked `reference`) and 94
  tests in the 29 Book 16 firm components, all passing.
- `tools/figdata.sh desk`: 87 chart CSVs regenerated, md5 identical before and after.
- Final: 347 pages (outline ~400, -13 %), 108 figures, 40 listings, 14 tables, 32 dated boxes, 182 ledger rows, 126
  definition environments, 61 EXCLUDED entries, 22 WebSearch calls.
