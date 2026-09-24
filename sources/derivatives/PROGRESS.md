# Book 5 — progress and working conventions (resume here)

Batch run of Books 3–6 (rules: `sources/BATCH_BOOKS_3-6.md`, binding). One
agent writes this book; the main session owns every shared file.
Run mode: Phase A, stop and report; after the sync, Phases B–D for the whole
book with no stop. Full source ledger (every checkable fact web-verified).

## Status

| ch | state |
|---|---|
| Phase A | done 2026-09-24: 28 briefs (`tools/briefs/book5.py`), `DEFINITIONS.md` 178 terms, none in the Books 1–2 harvest (547 `\index` entries checked, not only the adjacent `\emph…\index` pairs), skeleton 42 pp at 0/0/0; waiting for the sync (`SERIES_DEFINITIONS.md`, notation table, `code/firm/INTERFACES.md`) |
| Sync | applied 2026-09-24: *equivalent martingale measure*, *risk-neutral measure*, *calibration* removed (Book 4 ch. 5, 24), *copula* → Book 4 ch. 15; 175 terms |
| 1 | done 2026-09-24: `arbcheck` (with `lp_max` by vertex enumeration), 9 ledger rows, 4 figures checked, gates green, 54 pp built (12 pp all-in) |
| 2 | done 2026-09-24: `binomial` (CRR/JR/LR, American, escrowed-dividend hook), 4 ledger rows, 4 figures checked, 9 pp all-in (outline 10) |
| 3 | done 2026-09-24: `bs` in Python + C++20 + Rust (erfc by series/continued fraction in Rust, no memorised constants), 6 ledger rows, 4 figures checked |
| 4 | done 2026-09-24: `greeks` (desk units), Derman-Kamal sqrt(pi/4) verified in the source PDF, 5 ledger rows, 4 figures checked |
| pricing core | landed with ch. 4: `code/firm/pricing/firm_pricing.py` implements INTERFACES.md section 1 for European/American options (MarketData, bumps by risk-factor id, GridSurface nodes, BlackScholes, Analytic and Tree engines, price/greeks/sensitivities/bucketed_vega/reprice/price_batch, JSON, seed_for); 14 acceptance tests. Additions to the frozen interface (allowed: additive only): `MarketData.funding` (underlying -> curve for its forward), `Dividends.div_yield` (the DIV factor), `register_bump(kind, handler)`, `STANDARD_SHIFT`, `grid_from`, `FlatCurve`, `FlatVol`, `GridSurface`, `ShiftedCurve`, `ShiftedSurface`, `DEFAULT_BUMPS`, `seed_for`, `instrument_type` decorator |
| 5 | done 2026-09-24: `divfwd` (parity regression, implied carry/borrow, dividend strip); escrowed = proportional for Europeans at equal vol, spot model needs sigma_eff (derived, matches to 0.01 vol pt); 6 ledger rows |
| 6 | done 2026-09-24: `american` (Barone-Adesi-Whaley within 3 c of a 2001-step tree except deep ITM at 8 %, boundary, Bermudan, ex-date decision); 5 ledger rows. Correction made in ch. 5 and 6: a borrow fee acts like a dividend yield (puts: less early exercise; calls: can be exercised early) |
| 7 | done 2026-09-24: `volsurface` (total variance, not-a-knot spline: a natural spline manufactured butterfly arbitrage at the grid ends; Gatheral-Jacquier g(k) verified in the arXiv PDF); 8 ledger rows; 11 pp |
| 8 | done 2026-09-24: `svi` (quasi-explicit inner LS + Nelder-Mead, Lee bound imposed, SSVI with GJ conditions, event variance); synthetic market = SSVI slices with expiry-dependent rho; 5 ledger rows; 11 pp |
| 9 | done 2026-09-24: `localvol` (Dupire in total variance = dw/dT over the butterfly factor g; grid fixed in absolute spot -- the first version measured moneyness against the new spot and gave the wrong-sign dynamics); forward skew ratio 0.57; LV ATM moves 2.7x sticky strike (Bergomi's rule says 2 for short, weak skews); daily Euler bias 0.08 vol pt; 5 ledger rows; 9 pp |
| 10 | done 2026-09-24: `heston` (principal-branch cf, Lewis integral, LM calibration, full-truncation Euler); calibrated to the ch. 9 surface RMSE 0.37 pt, Feller fails; 1-week skew half the market's; a sign error in a drafted solution (expected vol change after a 1% fall: 1.05 pt, not 0.2) caught by recomputation; 5 ledger rows; 10 pp |
| 11 | done 2026-09-24: `sabr` (Hagan formula verified in the 2002 PDF, alpha from the ATM cubic, Bartlett delta); MV delta cuts one-day hedge-error variance 19% vs Black, Hagan delta +25%; example numbers first copied from a run with other parameters (rho -0.3) and caught by the numbers gate; 4 ledger rows; 9 pp |
| 12 | done 2026-09-24: `fwdvar` (log-strip variance, ForwardVarianceCurve, rough Bergomi by exact Cholesky of (Y, W1) with G(x) by a singularity-removing substitution, mixing-formula smiles, VIX, fBM, roughness estimator); market skew exponent -0.44 (H 0.06 by the rule, ~0.1 against rBergomi's own fit); realised-variance noise of 0.08 in log makes an OU (H 1/2) read 0.17-0.23; 14 ledger rows (arXiv + Crossref APIs only); 5 figures checked; 12 pp body (569 lines) |
| 13 | done 2026-09-24: `jumps` (Merton/Kou/Bates/VG/EventJump behind cf(u, t), Lewis grid to u = 1e6 for pure-jump short expiries, generic LM `calibrate(make, z0, quotes)`); quotes at 100 exp(0.2 sqrt(T) z), z in [-2, 2] (fixed 80-120 strikes at one week are 7 sd out and wreck any fit); binary event = one-step binomial: chord ratio 0.20 removes it, Black delta leaves 11%, uncertain sizes leave 16.5%; 6 ledger rows (Crossref abstracts); 4 figures checked; 11 pp |
| 14 | done 2026-09-24: `varswap` (index formula with K0 correction, strip payoff, MTM, jump_error, Heston vol swap by the integrated-CIR Laplace transform and sqrt(x) = int (1 - e^{-sx}) s^{-3/2} ds / (2 sqrt pi), VIX futures by the CIR Laplace transform, both checked by simulation); named result: 1.62 vol pts at 1y (21.4 vs 19.8); strip under Merton short by 0.18 pt; Cboe methodology v6.0 in a dated box; 7 ledger rows; 4 figures + 1 table checked; 12 pp |
| 15 | done 2026-09-24: `barrier` (8 single barriers + rebates by the image formulas, touches, double no-touch by sine series, BGK shift, discrete-monitoring MC, put-call symmetry, DEK-style calendar hedge); named result: width 200 points, overhedge 0.89m on a 5.77m digital; LV knock-out 6.15 vs 6.51 flat; EURCHF 2015 from the SNB release + ECB fixings; 5 ledger rows (Reiner-Rubinstein unverifiable, not attributed); 4 figures checked; 11 pp |
| 16 | done 2026-09-24: `pathdep` (common path array; geometric Asian CV x1357, GSG lookback + shifted extreme, forward-start, cliquet/reverse cliquet, forward smile from paths); `firm_heston.simulate_paths` added (additive); named result: monthly cliquet +-1% LV 1.53% vs Heston 2.22% (gap 0.69 pt, 45%); forward smile 6m->7m LV flat (skew 2.6) vs Heston 4.0; Asians agree across models (4.34 vs 4.36); Bergomi 2004 PDF + Jeffery 2004 title; 5 ledger rows; 4 figures checked; 9 pp |
| 17 | done 2026-09-24: `multiasset` (Cholesky paths with per-asset vol functions and quanto drift, equicorrelated local-correlation generator, basket/worst/best payoffs, moment matching, implied/realised correlation, quanto/composite); named result: implied correlation 0.549/0.408/0.308 at 90/100/110 (0.559 VS), dispersion +270.6k for -15 pts; quadratic local correlation reprices 3 strikes; DMV (SSRN abstracts) + Langnau (arXiv); Cboe/CME pages 403 -> EXCLUDED; 3 ledger rows; 4 figures checked; 10 pp |
| 18 | done 2026-09-24: `autocall` (TermSheet, daily-LV simulator for 1..n assets, Phoenix/snowball cash flows with memory and KI, fair coupon by linearity, snowball tail closed form via `barrier`, hedge across KI); 3y LV grid rebuilt with pillar-tent vol bumps for bucket vega; named result: 497m sold per 100m notes (delta 7.63 -> 1.00) one month out; fair coupon 6.18% LV vs 3.14% flat, worst-of 11.5%/10.4%; facts via Crossref abstracts (Yin 2026, Fang 2026 SSRN, Lim-Choi 2015, Kim-Park-Moon 2025 title); Korean/Chinese loss amounts EXCLUDED; 4 figures checked; 10 pp; tests 4.5 min (lru_cache on heavy runs) |
| 19 | done 2026-09-24: `termsheet` (Leg/Note, bond at r+s, participation and spread solvers, capped note, reverse convertible, EWMA vol-target index, decrement index); named result: 240 bp for 70% participation (34.6% at zero spread); VT index on Heston: calls at 10.2% vs 19.0% IV; PRIIPs text (Publications Office PDF) and FINRA 12-03 in a dated box; 2 ledger rows; 4 figures checked; 10 pp |
| 20 | done 2026-09-24: `fxvol` (vanna-volga weights/price/implied, VV one-touch convention, SLV with mixing weight, particle-method leverage calibration, SLV simulator, TARF cash flows); market = Heston on a USD/EM pair, local vol by mesh Dupire on Heston prices (firm_jumps Fourier grid: firm_heston's u<=200 grid fails at short, low-vol expiries); named result: TARF redeems after 1.73 fixings, expected loss 7.12m per 1m monthly notional after a +10% Q1 move; one-touch spread LV 43.3 vs Heston 38.9 at 7.20, VV overshoots mid barriers; BIS QR Sep 2015 for the PBoC fixing change; 5 ledger rows; 4 figures checked; ~10 pp |
| 21 | done 2026-09-24: `convertible` (CN in log-spot with hazard lambda(S), recovery source, projection for conversion/soft call/puts, coupons with Rannacher restarts); named result: delta-hedged loss 2.55 per 100 face for share -20% & spread +300 bp (4.38 with the constant-hazard delta; +1.93 with CDS); gamma by grid differences needs a 3% bump (1% gives oscillating gamma); 5 ledger rows (2005 episode by title only); 4 figures checked |
| 22 | done 2026-09-24: `fdpricer` Python (non-uniform log grid, theta scheme, Rannacher, payoff smoothing, dividend jump condition, Brennan-Schwartz, trinomial tree) + C++20 + Rust twins of the uniform-grid American put (agree to 1e-9); named result: tree 1,500 steps (1,125,750 node updates) vs grid 200x200 (40,600), speed-up 28 in work units (run times machine-dependent, not printed); CN gamma spike 0.217 vs 0.141; projection-after-solve falls to first order; 4 ledger rows; 4 figures checked |
| 23 | done 2026-09-24: `mcpricer` (GBM paths, Heston QE/Euler, LSM fit/price on independent paths, Andersen-Broadie dual with nested inner paths, pathwise/LR/smoothed Greeks, adjoint Asian bucket vegas, Halton + Brownian bridge, norm_inv by Newton on erf -- a memorised 1.959963984540054 in a test replaced by a round trip); named result: max-call rich basis 18.649/18.713 gap 0.064 (0.3%), small basis 18.137/18.805 gap 0.668; in-sample LSM (2,000 training paths) 18.74 exceeds the dual bound; Euler bias 0.857 at 4 steps vs QE within 1 se; Halton+bridge 14x MC; 5 ledger rows; 4 figures checked; 10 pp + solutions |
| 24 | done 2026-09-24: `calib` (COS with per-strike range c1 + ln(F/K) +- 16 sqrt(c2) -- 12 stalls at 3e-5 on Heston's left tail; Carr-Madan FFT + 4-point interpolation; Gauss-Legendre Lewis reference to 1e-9 -- firm_jumps' trapezoid grid is only 1.5e-6; QuoteSet, filter with reasons, vega-weighted LM with Tikhonov penalty on z - z_yesterday, Fit diagnostics incl. condition number, jump_alarm); synthetic market = Bates + 0.3 vol pt noise, 4 expiries x 5 strikes, one crossed + one stale quote a day (a pure-Heston market or +-1.5 sd strikes with 0.1 pt noise identify eta well: no wander); named result lambda = 1e-3 (max daily d-eta 0.235 -> 0.071, fit error +0.012 pt); hook day 58->59 eta 0.51 -> 0.28, vol-swap convexity 1.32 -> 0.39; Lewis formula derived (promised by ch. 10); 4 ledger rows; 4 figures checked |
| 25 | done 2026-09-24: `volpnl` (Option, SkewSurface with sticky-strike/sticky-delta via ref, value, book_greeks, per-option explain vs full revaluation, hedged_pnl, gamma_scalp with cash-gamma sum, roll_down); named result: same 25% realised, long 18-vol straddle makes 3.28 evenly spread vs -0.78 on the wrong days (15 x +0.5% drift, then +-2.84% at 107.8, cash gamma 39 vs 770); carry of 3m straddle -1.88 (roll-down -0.28); RR on a -5% day -0.023 sticky strike vs +0.081 sticky delta (explain misses 0.08: full reval); 63-day book explain totals differ by rule; short-vol programme (Bates path, fair vol + 2 pts): +0.44%/month, Sharpe 1.15, worst -5.04%; with no premium mean -0.008 (Jensen: implied 21.5 vs realised 20.6, RMS equal); Cboe PUT methodology PDF (moved URL) in a dated box; 5 ledger rows; 4 figures checked |
| 26 | done 2026-09-24: `optmm` (theo + vega per point on a SkewSurface, width model w e^{-w/ws} vs informed tail with golden-section optimum, band half-width c (cost S Gamma^2)^{1/3} derived by a scaling argument -- WW's exact constant not verifiable, not quoted; vectorised hedge_paths with erf via np.vectorize, dividend_play + closed-form best size, Bucket/vega_by_bucket, quote shading and withdrawal); named result: 30% failure -> best q 32,947, 2,605 unassigned (87%), net $108,553 (fees $0.50 per q, an assumption); band c=1 = daily-hedge cost with 41% less P&L sd; toy MM limits: $11,141 vs -$607 on one path, +$9,585 +- 2,593 over 20 seeds; Cboe fee schedule 15 Sep 2026 footnote 13 (dividend strategies not capped) in a dated box; 3 ledger rows; 4 figures checked |
| 27 | done 2026-09-24: `reserves` (bid-offer by bucket, prudent_point = 90% point with mid-point plotting positions, model_reserve, parameter_reserve, 50% aggregation, DayOne split, release_schedule, stress_grid, concentration_days); note = 3y worst-of Phoenix on two indices priced with firm_autocall.simulate at annual steps (exact, cheap; daily steps would need 1.2 GB); named result: 2m margin -> 0.621 bid-offer, 1.054 deferred (model 0.621 + correlation 0.433), 0.325 recognised; 0.424 released after one year (0.362 from correlation); the firm (issuer) is long vega and long the KI put: worst stress cell -10% & -5 vol (-6.31m); regulatory texts via publications.europa.eu with Accept: application/xhtml+xml (EUR-Lex returns 202/empty to curl); SR 11-7 superseded by SR 26-2 on 17 Apr 2026 (WebSearch back) in a dated box; Natixis EUR 259m from its own release; 5 ledger rows; 4 figures checked |
| 28 | done 2026-09-24: `pricing` completed (additive only): instruments DigitalOption, BarrierOption, AsianOption, ForwardStart, Cliquet, VarianceSwap, BasketOption, WorstOf, Autocallable, TARF, ConvertibleBond; models HestonModel, CreditBlackScholes; engines ClosedFormEngine, MonteCarloEngine(n_paths, seed_offset, crn) with term-structure variance at a reference strike, PDEEngine (fd_vanilla, both Brennan-Schwartz directions), FourierEngine (COS), ConvertibleEngine; engines_for(); C++20 cpp/pricing.hpp + pricing_test.cpp and Rust crate rust/ (path dep on firm_bs) reproduce Analytic/PDE prices and desk Greeks to 1e-9; named result: book's (1y, 90) vega 2,072/pt (autocall +2,249, Am put -88, var swap -90), MC sd 51 with CRN vs 217 without (x4.3; 25 with 4x paths); QuantLib 1.43 Instrument docs, ORE README, FINOS CDM, FpML (dated box); 4 ledger rows; 4 figures checked |
| Phase B | complete 2026-09-24: 28 chapters, gates 0/0/0 |
| Phase C | done 2026-09-24: term links (STOP += rho, straddle, backbone, arbitrage: SABR's "rho", the verb "straddles", an ordinary "backbone", "arbitrage" as a strategy) -> 1,378 links, 182 linkable terms; tools/gates.sh book derivatives GREEN (0/0/0, no term defined twice, problem numbering OK, links match config); tools/figdata.sh derivatives: no diff; tools/test_code.sh derivatives GREEN (147 chapter tests) and all 28 components GREEN (C++20/Rust twins: bs, fdpricer, pricing); DEFINITIONS.md = \index (175 = 175, chapters agree); facts restored once WebSearch returned: Korean HSCEI ELS amounts (ch18), Giles-Glasserman (ch23), Martin 2011 on the single-name variance market (ch14), 2005 convertible redemptions (ch21); ch07 caption reworded ("Circles" hit the new firm name "Circle"); 348 pp |
| Phase D | report returned to the coordinator 2026-09-24 |

## Identifiers

Entry `one_quant_book_05_derivatives.tex`, slug `derivatives`, labels
`<type>:dv:<chapter-slug>:<name>`, teaching modules `dv_*.py`, running-project
modules `code/firm/<component>/firm_<component>.py`, linker `--book 5`.

## Per-chapter cycle

Same as `sources/markets-1/PROGRESS.md`: sources → lesson → code with tests →
figures (script-generated CSVs; payoff kinks at strikes, Greeks with the right
sign) → 8 exercises (3/3/2), weekend problem (~20 questions, one named
result), 5–8 interview questions → solutions with `test_solutions.py` →
chapter gates. Figures: `OQB_BOOK=5 .venv/bin/python tools/figcrop.py …`.
Gates: `tools/gates.sh chapter derivatives/NN-slug`, `tools/gates.sh log
derivatives`, `make test-code CH=derivatives/NN-slug`. Build only
`latexmk one_quant_book_05_derivatives.tex`.

## Budget

11–12 pages all-in per chapter (Book 1: 11.5, Book 2: 11.2) → 28 × 11.5 + ~18
≈ **340 pp** against the outline's ~386 (−12 %, the same gap as Book 2: the
outline's 14–16 pp chapters come out at 12–13). Body 430–560 lines, solutions
~160–200 lines. Chapter 18 (16 pp) and 26 (16 pp) get a fifth section, not
longer prose. Chapter 28 is a "Build:" chapter: lesson ~3 pp, build ~5 pp.

## Calibration

- After ch. 10 (2026-09-24): 146 pp for ten chapters: **10.4 pp all-in per chapter** (body 400-560
  lines). Projection 28 x 10.4 + 18 = ~309 pp against the brief's ~335. Chapters 11-28 to be written
  at 520-600 body lines (a fifth section or a second worked example), solutions ~140 lines; the
  outline's 14-16 pp chapters (14, 17, 18, 20, 23, 25, 26) at 600+.

- After ch. 6 (2026-09-24): 105 pp built for six chapters (skeleton 42): 10.5 pp all-in per
  chapter. Part II chapters (outline 14 pp) should run 520-580 body lines.

- After ch. 4 (2026-09-24): chapters start at pp. 2, 12, 21, 31; the PDF is 85 pp against a 42-pp
  skeleton: **10.75 pp all-in per chapter** (body 557/443/489/486 lines, solutions 145/124/134/127).
  Projection 28 x 10.75 + 18 = ~320 pp against the 335 of the brief and the outline's 386. Write
  chapters 5-28 at 500-560 body lines (the 14-16 pp chapters with a fifth section), solutions
  150-170 lines.

## Components (frozen at the sync)

One `code/firm/<name>/` per chapter; the chapter components are stateless
kernels, and chapter 28's `pricing` wraps them as models and engines behind
one interface (Book 6 ch. 29 runs on it). C++20 and Rust twins: `bs`,
`fdpricer`, `pricing` (core types + analytic and finite-difference engines).
Numpy only (no scipy in `.venv`): simplex, Levenberg–Marquardt and quadrature
are written by hand.

## Environment notes

- `.venv`: Python 3.10, numpy 2.2, pandas; **no scipy**. g++ 11.4
  (`-std=c++20`), cargo 1.97.
- Skeleton trap: 28 consecutive empty `\section*` stubs in the solutions
  appendix gave one overfull `\vbox` (headings cannot break between each
  other); each stub now carries `\mbox{}` until its solutions are written.

## Traps met in Book 5 (for WRITING_A_QUANT_BOOK.md section 9 at delivery)

- The WebSearch budget (200 searches for the session) ran out during chapter 12. From then on facts are
  verified only by fetching known URLs: the arXiv API (`https://export.arxiv.org/api/query?id_list=...`
  or `search_query=...`) for abstracts and PDFs, and the Crossref API
  (`https://api.crossref.org/works/<doi>` or `works?query.bibliographic=...`) for journal, volume, pages
  and sometimes abstracts. SSRN and most publisher pages return 403 to curl. What cannot be fetched goes
  under EXCLUDED.

- Memorised numerical constants are facts too: the first Rust erfc used rational-approximation
  coefficients typed from memory (and did not even compile); replaced by a series and a continued
  fraction that need no constants, tested against Python's math.erfc.
- A claim drafted from intuition ("a high borrow fee makes early exercise of puts more likely")
  was backwards; the borrow fee acts as a dividend yield. Test the direction of every comparative
  statement against the pricer.
- Concurrent builds: one figure crop returned a Book 4 page (Hawkes figure) from `build/one_quant_book_05_derivatives.pdf` while other books were building; re-running gave the right page. Re-render any crop whose running header is not this book's.
- A comma in a `\legend` entry ("before, and after") split it: brace every entry with a comma (Book 2 trap, met again).
- `np.polynomial.legendre.leggauss(4000)` costs half a minute (an eigenvalue problem): cache a few hundred nodes at module level.
- Levenberg–Marquardt on Merton's (lambda, mu_J) stalls in a flat valley from a far start (RMSE 2e-4 against a known 0): start calibrations near a plausible point and test recovery from there.
- The at-the-forward strike of a replicating strip must hold half a put and half a call (as the index formula does), or the strip's payoff is off by dK/(2F^2)(S-F) everywhere.
- A histogram cannot show a distribution 30 times narrower than the other on the same bins: plot tail probabilities P(loss > x) on a log axis instead.
- `ruff --fix` removes imports that are unused *at that moment*: a function appended later that needs one fails at run time (NameError). Re-run the module after appending code.
- `firm_heston.call_prices` integrates to u = 200 only: for low volatility and short expiries (sigma sqrt(T) < 0.02) the characteristic function has not decayed and prices go negative; use `firm_jumps.call_prices` (grid to 1e6) for such markets.
- `V''` in math trips the quote-balance gate (as in Book 1's trap): write `V^{\prime\prime}`.

- The Phase A harvest command (`\emph{…}\index{…}` adjacent) misses 38 of
  Books 1–2's 547 index entries (`put--call parity`, `term structure of
  volatility`, `European exercise`, `normal volatility`, `strike price` …,
  where the `\emph` wraps a line). Check against `grep -ho '\\index{[^}]*}'`.
- Book 1 ch. 26 defines *delta* with `\emph{delta}` and no `\index` (so the
  linker never links it); Book 1 ch. 23 does the same for *intrinsic value*.
- **Ch. 23-28 (2026-09-24).** LSM in-sample pricing on 2,000 training paths is biased *above the dual bound*; fit and price on
  independent paths. COS truncation: [a,b] = c1 +- L sqrt(c2) needs L = 16 for Heston (12 stalls at 3e-5: fat left tail).
  firm_jumps' trapezoid Lewis grid is accurate to ~1.5e-6 only; use firm_calib.lewis_calls (Gauss-Legendre) as reference.
  A pure-Heston synthetic market identifies eta well: calibration instability needs misspecification (Bates) and
  realistic noise. A hedged straddle's P&L depends on *where* the variance is realised (15 quiet days of drift then
  a wild week far from the strike loses with 25 realised vs 18 implied). The EU texts: EUR-Lex returns 202/empty to
  curl; publications.europa.eu/resource/celex/<CELEX> with "Accept: application/xhtml+xml" works. SR 11-7 was
  superseded by SR 26-2 on 17 Apr 2026. firm_autocall.simulate at daily steps for 3y x 100k paths needs ~1.2 GB:
  use annual steps when only observation dates matter (exact under flat vol). pgfplots groupplots reject
  `bar width` in the group options: put `ybar,bar width` in each \nextgroupplot; a `coordinates` line inside an
  xbar axis is drawn as a bar -- use \draw (axis cs:...). MC engine: vol from the last date only gives zero vega to
  earlier surface nodes; use increments of total variance at a reference strike.
- **Tooling (for the main session).** tools/check_figdata.py:11 crashes (IndexError) on an empty CSV instead of
  reporting it (seen on another book's transient file); tools/gates.sh sources <slug> without a chapter looks for
  sources/<slug>.md; tools/firm_names.txt's "Circle" flags the ordinary word.
