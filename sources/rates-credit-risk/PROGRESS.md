# Book 6 — progress and working conventions (resume here)

Batch run of Books 3-6 (`sources/BATCH_BOOKS_3-6.md`), one agent per book.
Run mode: Phase A, stop and report; after the main session's sync (series
definitions, notation table, `code/firm/INTERFACES.md`), Phases B-D for the
whole book with no stop. Budget: **11-12 pages all-in per chapter** (~345 pp).
Chapter 29 (risk engine on Book 5's pricing library) is written **last**.

## Status

| ch | state |
|---|---|
| Phase A | done 2026-09-24: 29 briefs (`tools/briefs/book6.py`), DEFINITIONS.md 226 terms, no collision with the Books 1-2 harvest (multi-line aware); three overlaps with the published Book 3/5 briefs yielded to the lower book (Samuelson effect B3.10, trinomial tree B5.22, valuation reserve B5.27) and every use renamed to their exact terms; skeleton 0/0/0 (42 pp) |
| sync | done 2026-09-24 (copula -> B4.15 removed from ch. 15; notation: Th, y_c, kappa/x-bar; no scipy; role `risk`) |
| 1 | done 2026-09-24: curvebuild (4 interpolations, global Newton), 5 figures, 3 listings, 1 dated box, 6 ledger rows, ECB Svensson data; 10 body + 2.5 sol pp |
| 2 | done 2026-09-24: multicurve (projection on fixed discount, tenor basis, CollateralChoiceCurve, ShiftedCurve), 4 figures, 2 listings, 1 dated box, 5 ledger rows; 9 body + 2.5 sol pp |
| 3 | done 2026-09-24: ratesrisk (ladders, Jacobian, key rates, PCA, min-variance hedge, cross-gamma), Treasury par yields 2016-2026 in data/, 4 figures, 2 listings, 4 ledger rows; 8 body + 2 sol pp |
| 4 | done 2026-09-24: capfloor (Black/Bachelier caplets, stripping, physical and par-yield cash swaptions), 4 figures, 2 listings, 1 dated box, 3 ledger rows |
| 5 | done 2026-09-24: sabrcube (Hagan lognormal on shifted rates, normal SABR, LM calibration, density, Cube bilinear in parameters), 4 figures, 2 listings, 1 dated box, 5 ledger rows |
| 6 | done 2026-09-24: cms (timing, linear TSR, replication on the cube smile, CMS caplet, quanto, spread options), 4 figures, 2 listings, 2 ledger rows |
| 7 | done 2026-09-24: shortrate (HW Gaussian form, piecewise sigma, ZBO, Jamshidian, co-terminal calibration, HW trinomial tree, Vasicek, G2++ correlation), 5 figures, 2 listings, 4 ledger rows |
| 8 | done 2026-09-24: lmm (abcd vols, exponential correlation, spot-measure predictor-corrector MC, caplet calibration, Rebonato), 5 figures, 2 listings, 4 ledger rows |
| 9 | done 2026-09-24: bermudan (tree Bermudan, exercise boundary, callable zero, LSM under the terminal measure), 3 figures + 1 table, 2 listings, 1 dated box, 3 ledger rows |
| 10 | done 2026-09-24: rfrcaplet (HW backward/forward caplets closed form + aligned-grid MC, GFMM variance, meeting variance), 4 figures, 2 listings, 1 dated box, 5 ledger rows |
| 11 | done 2026-09-24: inflopt (JY with deterministic nominal, YoY convexity closed form + MC, YoY caplets, LPI by MC; seasonality via Book 2 firm_breakeven), 4 figures, 2 listings, 1 dated box, 5 ledger rows |
| 12 | done 2026-09-24: mbsoas (HW monthly paths, turnover+S-curve+burnout, OAS, option cost, IO/PO, effective risk), 4 figures (incl. Fed MBS from Book 2 data), 2 listings, 1 dated box, 4 ledger rows |
| 13 | done 2026-09-24: cdscurve (piecewise hazard bootstrap on any discount curve, standard upfront via Book 2 firm_cds, risky bond, bucketed CS01, JTD), 4 figures, 2 listings, 1 dated box, 2 ledger rows; negative-basis weekend problem; 8 body + 2 sol pp |
| 14 | done 2026-09-24: structural (Merton, inversion, DD, Black-Cox first passage -> hazard curve -> CDS spread via cdscurve, asset_from_equity), 4 figures, 2 listings, 1 dated box (BIS QR June 2005), 4 ledger rows; May 2005 capital-structure trade |
| 15 | done 2026-09-24: portcredit (Gaussian copula recursion + GH quadrature, cached count paths per pool/rho, base/compound correlation, t-copula by conditional binomial, default correlation), 4 figures, 1 listing, 1 dated box, 5 ledger rows (BIS QR 2005, Li, Vasicek, Hull-White, FCIC); tests take ~20 s |
| 16 | done 2026-09-24: energymodel (two-factor forward-curve model exact sim + LM calibration, Margrabe/Kirk/MC, storage intrinsic DP / vectorised rolling intrinsic / LSM, swing as a facility), EIA Henry Hub daily data, 4 figures, 2 listings, 1 dated box, 5 ledger rows |
| 17 | done 2026-09-24: exposure (HW + FX scenarios, Swap/XccySwap/FxForward revaluation, CSA collateral with MPoR lag, EE/ENE/PFE/EPE, conditional EE; aggregation kernel twinned in C++20 cpp/ and Rust rust/ on a shared fixture), 5 figures, 2 listings, 2 dated boxes, 2 ledger rows (FCIC Lehman, BCBS 279 MPoR) |
| 18 | done 2026-09-24: cva (deflators from HW paths, discounted EE/ENE, unilateral and first-to-default CVA/DVA, pathwise wrong-way CVA, bucketed CS01, running spread), 4 figures, 1 listing, 1 dated box, 3 ledger rows (BCBS 2011 two-thirds, Basel III para 75 + 2012 DVA rule, IFRS 13) |
| 19 | done 2026-09-24: xvafund (FCA/FBA, MVA over Book 2 ccpbasis, SA-CCR IR/FX with BCBS example 1 = 569 as test, reduced BA-CVA, KVA), 4 figures, 2 listings, 1 dated box, 7 ledger rows; funding exposure uses lag 0, default exposure lag 1 |
| 20 | done 2026-09-24: xvaquote (netting_cva, incremental, Euler CVA, proxy spread regression, running charge); ch19 now uses effective maturity (avg payment time) for BA-CVA M; 4 figures, 1 listing, 1 dated box, 3 ledger rows (BCBS d507) |
| 21 | done 2026-09-24: varmodel (HS/EWMA/param/MC/FHS VaR-ES, delta-gamma, Kupiec, Christoffersen, traffic light, Euler); ECB FX data added to data/; 4-year backtest (~15 s, cached); 4 figures, 2 listings, 1 dated box, 7 ledger rows |
| 22 | done 2026-09-24: stresstest (historical, conditioning, Mahalanobis, reverse linear + nonlinear); Treasury+ECB 2008 data; 2 figures, 1 listing, 2 dated boxes, 7 ledger rows (SEC Archegos via WebFetch, Fed 2026 scenarios, EBA 2027 draft) |
| 23 | done 2026-09-24: frtb (SBM GIRR/FX delta, FX vega, curvature, 3 scenarios; ES + LH; IMCC; PLA Spearman/KS; RFET; amber surcharge); latest EU (delegated act 2026/1221, 1 Jan 2027 + 3y relief), UK (CP9/26, IMA 1 Jan 2028), US (19 Mar 2026 proposal); 3 figures, 2 listings, 1 dated box, 5 ledger rows. TRAP: never wrap latexmk in a short timeout (a killed run truncates .aux/.toc: delete them and rebuild, ~4 min) |
| 24 | done 2026-09-24: alm (six IRRBB shocks, BalanceSheet EVE/NII with NMD core slotting and beta, LCR with L2 cap/haircut, FTP, run capacity); stylised SVB-like bank; 4 figures, 2 listings, 1 dated box, 5 ledger rows (Fed SVB review, BTFP, BCBS LCR/NSFR/IRRBB) |
| 25 | done 2026-09-24: initmargin (HS/FHS IM, SIMM-shaped sensitivity IM with illustrative RWs, BCBS-IOSCO schedule + NGR, APC buffer with rebuild and stressed weight, backtest); March 2020 replay on Treasury proxies; 2 figures, 2 listings, 2 dated boxes, 4 ledger rows |
| 26 | done 2026-09-24: modelval (ModelRecord tiering, benchmark harness, binomial tail, relative_change with the 2012 error); HW tree vs Jamshidian validation (216 points); SR 26-2 (17 Apr 2026) supersedes SR 11-7; PRA SS1/23; 2 figures, 1 listing, 2 dated boxes, 4 ledger rows |
| 27 | done 2026-09-24: pnlexplain (FD Greeks incl. vanna/volga, risk-based and revaluation attribution, IPV to boundary, MPU AVA 90%, 50% aggregation, simplified 0.1%); symmetric risk reversal (pure delta at start, vanna explains 391k of 398k unexplained); 2 figures, 2 listings, 2 dated boxes, 3 ledger rows |
| 28 | done 2026-09-24: tradecontrol (five blotter rules, scoring, hash-chained AuditLog); synthetic blotter 2,000 + 60 scheme trades (any rule 88.3%/7.1%, two rules 61.7%/0.05%); Basel SA op capital; SG unwind 9.8%; 2 figures (TikZ control chain + rule bars), 1 listing, 1 dated box, 5 ledger rows (Hansard Barings, FSA UBS, BBC SG, CFTC Sumitomo, BCBS 2017) |
| 29 | done 2026-09-24: riskengine consumes Book 5's code/firm/pricing (present and green, 14 tests) -- no stub needed; registers PillarCurve/IRSwap/Swaption/NormalRates via fp.register; full/grid/delta-gamma/planned revaluation with call counter; aggregation, VaR/ES, Euler ES, limits; C++20 + Rust kernel on a shared fixture; 1,000-trade book, 250 1-day and 10-day historical scenarios (Treasury + ECB); named result: plan 1.50 h / 0.76% vs full 4.36 h; 3 figures, 4 listings, 1 dated box, 2 ledger rows (BCBS 239, 2023 progress report) |
| Phase C | done 2026-09-24: linker (269 terms, 819 links, config unchanged: no homograph needed a STOP/DROP entry); `gates.sh book rates-credit-risk` GREEN (0/0/0, no term defined twice over 6 books); `make figdata` reproduces every CSV (after fixing ch. 5's fig import); `make test-code CH=rates-credit-risk` 144 tests + 29 firm components (125 tests, C++20 and Rust for exposure and riskengine) green; dated boxes all in ledgers; cross-reference pass fixed ch. 19 (FRTB dates are ch. 23) and the ch. 28 hook. 310 pp (10.7 pp/chapter all-in, just under the 11-12 budget) |
| Phase D | done 2026-09-24: report returned to the main session |

## Per-chapter cycle

Same as `sources/markets-1/PROGRESS.md`: sources -> lesson -> code with tests
-> figures (charts from script-generated CSVs, each read with
`OQB_BOOK=6 .venv/bin/python tools/figcrop.py "Figure N.M." out.png`) -> 8
exercises (3/3/2), weekend problem (~20 questions, Parts I-IV), 5-8 interview
questions -> solutions with `test_solutions.py` -> chapter gates.
Gates: `tools/gates.sh chapter rates-credit-risk/NN-slug`,
`make test-code CH=rates-credit-risk/NN-slug`, `tools/gates.sh sources|firms
rates-credit-risk/NN-slug`, `latexmk one_quant_book_06_rates_credit_risk.tex`,
`tools/gates.sh log rates-credit-risk`. Build only this entry file.
Before each chapter's definitions: grep `\index{<term>}` over `parts/*/`
(multi-line aware, see traps) and check `sources/SERIES_DEFINITIONS.md`.

## Running-project components (proposed, none exist yet; create only after the sync)

curvebuild, multicurve, ratesrisk, capfloor, sabrcube, cms, shortrate, lmm,
bermudan, rfrcaplet, inflopt, mbsoas, cdscurve, structural, portcredit,
energymodel, exposure (Py + C++20 + Rust), cva, xvafund, xvaquote, varmodel,
stresstest, frtb, alm, initmargin, modelval, pnlexplain, tradecontrol,
riskengine (Py + C++20 + Rust). Book 2's `curve`, `cds`, `tranche`,
`normalvol`, `prepay`, `breakeven`, `ccpbasis` and Book 1's `pnl` are imported,
never edited.

## How each chapter is built (resume notes)

- Code: `code/rates-credit-risk/NN-slug/python/rc_<topic>.py` (teaching module; imports firm components
  by `sys.path.insert(0, ROOT / "code/firm/<comp>")`, and earlier chapters' modules the same way:
  rc_curves (ch1 SOFR curve), rc_multicurve (ch2 EUR curves: `discount()`, `projection()`),
  rc_sabrcube (ch5 cube: `build_cube()`, DISC, PROJ), rc_shortrate (ch7), rc_ratesrisk (ch3 Treasury data)).
  `fig_rc_<topic>.py` writes CSVs to `figdata/rates-credit-risk/<NN-slug>/` (OUT built from
  `pathlib.Path(__file__).parents[1].name`). Tests: `tests/test_rc_<topic>.py` (tutorial end state) and
  `tests/test_solutions.py` (every printed number, rounded as printed).
- Firm component: `code/firm/<comp>/firm_<comp>.py` + `tests/test_firm_<comp>.py` (acceptance).
- Chapter: ~450-500 body lines, 4-5 figures (pgfplots from CSV + TikZ schematics), 2 listings via
  `\omcode`, 8 exercises 3/3/2, problem 20 Q, 6 interview questions, omsources; solutions file.
- After writing: `latexmk one_quant_book_06_rates_credit_risk.tex`, `tools/gates.sh log rates-credit-risk`,
  `tools/gates.sh chapter rates-credit-risk/NN-slug`, `make test-code CH=rates-credit-risk/NN-slug`,
  ruff on code/firm/<comp>, `tools/omcode_ends.py rates-credit-risk/NN`, crops with
  `OQB_BOOK=6 .venv/bin/python tools/figcrop.py "Figure N.i." scratchpad/b6/cNN_i.png` and READ each.
- Ledger rows: web-verified (WebSearch/WebFetch; PDFs via curl + pdftotext), in
  `sources/rates-credit-risk/NN-slug.md` under `## Ledger`, `## EXCLUDED` notes illustrative data.

## Calibration

- After ch. 3 (2026-09-24): body 10 / 9 / 8 pp (554 / 486 / 453 lines), solutions ~2 pp each (167 /
  167 / 153 lines): **11.0 pp all-in per chapter**. Projection 29 x 11.0 + ~15 = ~334 pp against the
  11-12 pp budget (~345): inside. Aim at 480-520 body lines (9 body pp) from ch. 4 on.
- After ch. 10 (2026-09-24): chapters 1-10 take 85 body pages (p9-93) and ~20.5 solution pages:
  **10.6 pp all-in per chapter** (body 8-10 pp from 400-550 lines). Projection 29 x 10.6 + 16 = ~323 pp,
  at the low edge of 11-12 pp (319-348). Parts III-IV carry more prose and dated boxes; aim at
  480-540 body lines and 4-5 figures per chapter from ch. 11 on.

## Traps met in Book 6 (for WRITING_A_QUANT_BOOK.md section 9 at delivery)

- The session scratchpad is shared with the other book agents (their PNGs appear in it): write
  figure crops to `scratchpad/b6/` only. Page map helper: `scratchpad/b6/pages.py` (run from repo root).
- Book 2 defect: `code/firm/curve/firm_curve.py` `bootstrap` bisects ln P in [-1, 0], so any pillar
  with P < 1/e (a 30-year at 4%) is silently wrong. Book 6 never calls it beyond 20 years.
- Monotone convex interpolation is continuous but not linear in its inputs: a 1 bp bucket bump can
  switch the case on an interval, so 1 bp buckets of an off-pillar book summed to 866k against a
  555k parallel DV01. Book 6 bumps by 0.01 bp and scales (`BUMP = 1e-6` in rc_curves).
- Captions drafted before the chart is rendered were wrong three times in ch. 1 (the spline did not
  oscillate; monotone convex did load 5Y/12Y): write captions from the rendered figure.
- Never hand-write `\omterm`, least of all to another book's label (undefined reference).
- `listings` cannot print UTF-8 (`€`): a listed code file with `€STR` in a docstring was a fatal error. Write ESTR and EUR in code files.

- The prescribed harvest one-liner
  `grep -ho 'emph{[^}]*}\\index{[^}]*}' …` misses every `\index{}` broken
  across a source line: eight Books 1-2 terms (credit support annex, negative
  convexity, Global Master Repurchase Agreement, clearing member,
  liability-driven investment, money-market yield, wildcard option, basis
  trade at index close). Harvest with a multi-line regex over the whole file
  (Python `re` on `\index\{…\}`, whitespace collapsed) instead.
- A skeleton of 29 empty solution stubs is 29 consecutive `\section*`
  headings with no break allowed between them: one overfull `\vbox` (145 pt)
  while `\output` is active. Each stub carries a `\strut` paragraph until its
  solutions are written.
- Homographs to curate in Phase C: *fair value* (Book 1: futures fair value;
  here accounting fair value), *level 3* (Book 1: market-data level; here the
  fair-value hierarchy), *exposure*, *threshold*, *model*, *reserve(s)*
  (Book 2: central-bank reserves), *turnover* (housing turnover), *basis*
  (tenor basis), *convexity adjustment* inside *CMS convexity adjustment*.
- A Monte Carlo time grid must contain the period dates: with 250 steps a year, E = 1.25 gave int(312.5) = 312 steps and S = 1.0 fell between nodes, so the compounded period was cut short and an out-of-the-money backward-looking caplet came out 6% low with a tight standard error (ch. 10). The function now refuses grids that miss S or E.
- The session web-search budget (200 calls, apparently shared by the batch agents) ran out during ch. 11 (2026-09-24). From then on: WebFetch on primary-source URLs (regulators, ONS, legislation.gov.uk, BIS, Fed), curl + pdftotext, and earlier ledgers of Books 1-2. Report it.
- A comma inside a pgfplots legend entry (LPI $[0\%,5\%]$) was fatal again (Book 2 trap): brace every legend entry containing a comma. `ybar interval` on a histogram garbled the x ticks: plot const plot mark mid on bin centres instead (ch. 11).
- `make figdata` can fail where every test passes: ruff's import sorting moves `from firm_x import ...` above `from rc_x import ...`, so a fig script that relied on the rc module's `sys.path` insert breaks (ch. 5's `fig_rc_sabrcube.py`, found in Phase C). `check_figdata.py` only checks the CSVs, never runs the scripts. Fig scripts now insert their firm paths themselves.
- Ch. 29: Book 5's `code/firm/pricing/` was present and green (14 tests) when ch. 29 was written, so no `pricing_stub.py`; `firm_riskengine` registers its rates instruments with `fp.register` and runs full revaluation through `fp.price_batch`. If Book 5 changes the library's behaviour (not its interface), ch. 29's printed numbers only depend on its own engines plus `EuropeanOption`/`BlackScholes`/`AnalyticEngine`.

## Re-sourcing pass (2026-09-24, after the web-search limit was raised)

Every EXCLUDED item of chapters 1-29 re-examined. Restored with new ledger rows (123 -> 160 rows): ch12 (2020 primary-secondary spread, NBER), ch13 (Hull-Predescu-White Table 1), ch14 (Tracinda offer on EDGAR, CreditGrades 2002, Yu 2006 abstract), ch15 (SFBC report on UBS super-senior write-downs, Andersen-Sidenius-Basu attribution), ch16 (EIA monthly Henry Hub, Kirk 1995 record), ch17 (ISDA netting opinions, new dated box; Gregory), ch18 (IFRS 13 para 42; JPMorgan 3Q11 DVA gain), ch19 (JPMorgan 4Q13 FVA loss in the hook; US and EU SA-CCR / CVA dates), ch20 (EU RTS 526/2014 proxy spreads), ch21 (1996 sixty-day averaging rule), ch22 (Fed: Archegos > USD 10bn across banks; EBA 2025 results), ch23 (Basel 2.5 stressed VaR), ch24 (BCBS July 2024 IRRBB recalibration: USD long shock 150 -> 225 bp, `firm_alm.USD_SHOCKS_2024`, new dated box; GAO on SVB's HTM loss; FDIC on First Republic), ch25 (SIMM v2.8+2512 effective 11 July 2026; EMIR RTS Art. 28 APC options), ch26 (Senate PSI: CIO VaR 132 -> 66m; ECB internal-models guide July 2025), ch27 (IFRS 13 levels; Totem consensus service via SRC DP 98), ch28 (Fed order on Daiwa; Sumitomo USD 2.6bn; AIB 20-F on Allfirst USD 691.2m; SG Mission Green: EUR 49bn, 6.4bn unwind loss, 947 fictitious trades -> weekend problem recomputed: 6.4/49 = 13.1%, 128bn, VaR 1.80bn), ch29 (BCBS newsletter No 36, Jan 2026; ECB RDARR guide May 2024; McKinsey 2011 survey of VaR run times).
Still excluded after search: 4:15 report (secondary only), LPI market size, CMS steepener losses (trade press only), Commission bancaire 2008 decision text, named banks' XVA desks, US FRTB final rule (none), agency MBS outstanding, iTraxx 2005 quotes; illustrative inputs are marked "by design".
Trap: EDGAR serves scripted requests only with a declared User-Agent carrying a contact; EUR-Lex serves `legal-content/EN/TXT/PDF/?uri=CELEX:...` PDFs to curl; Washington Post archive pages via the Wayback Machine.
Result: 314 pp; book gate GREEN (0/0/0); `make test-code CH=rates-credit-risk` GREEN (144 tests), firm alm and tradecontrol GREEN; linker 824 links.
