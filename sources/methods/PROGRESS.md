# Book 4 — progress and working conventions (resume here)

Batch run of Books 3-6 (see `sources/BATCH_BOOKS_3-6.md`, binding). One agent writes this
book. Run mode after the sync: whole book, no stop; full source ledger (external facts only:
mathematics is derived, not sourced).

## Status

| ch | state |
|---|---|
| Sync | read 2026-09-24: all four contested terms are Book 4's; notation fixed in CONTRIBUTING.md (Hawkes $\lambda_t$ with baseline $\mu$; $\eta$ vol-of-vol; OU $\bar x$; square-root $\bar v$; MA $\vartheta_j$; characteristic function $\varphi_X$); no scipy; `risk` role valid; components self-contained (Books 5-6 do not import them) |
| Phase A | done 2026-09-24: 29 briefs (`tools/briefs/book4.py`), DEFINITIONS.md 403 terms + named-results table, no Book 1-2 collision, skeleton builds 0/0/0 (43 pp); report returned to the main session; waiting for the sync (SERIES_DEFINITIONS.md, notation table in CONTRIBUTING.md, code/firm reservations) |
| 1 | done 2026-09-24: text (notation tables printed), solutions, `firm.mgtest`, ledger 6 rows, gates green, 4 figures checked; 11 body pp + 1.9 sol |
| 2 | done 2026-09-24: `firm.mcengine` stage 1 (Py + C++20 + Rust, SplitMix64 reference stream identical across the three), ledger 6 rows, 4 figures checked; 10 body pp + 1.5 sol. (Ch. 5 exercise 7 now derives the drifted first-passage formula.) |
| 3 | done 2026-09-24: `firm.stochint`, look-ahead Sharpe 5.67 named result, ledger 4 rows, 4 figures checked; 9 body pp + 1.8 sol |
| 4 | done 2026-09-24: `firm.mcengine` stage 2 (Euler-Maruyama, exact OU and square-root, full truncation; C++20 + Rust twins of the OU and Euler steps), Feller named result (75% failing paths), ledger 6 rows, 4 figures checked; 9 body pp + 1.7 sol |
| 5 | done 2026-09-24: `firm.numeraire`, caplet 3.26 bp named result (forward measure buys dimension, not variance), exercise 7 pays ch. 2's debt (drifted first passage), ledger 6 rows, 4 figures checked; 9 body pp + 1.9 sol |
| 6 | done 2026-09-24: `firm.levy` (exponents of BM, Merton, Kou, VG, NIG; numerical cumulants; subordinated simulation), 1987 named result (21 sigma; jumps at 0.5/yr, mean -11.1%), ledger 5 rows, 4 figures checked; 9 body pp + 1.5 sol. Trap: \\cref to an `lst:` label inside `tutsteps` is undefined (label type tutstepsi): refer to listings in prose |
| 7 | done 2026-09-24: `firm.hawkes` (Py + C++20 + Rust; thinning, O(n) likelihood, compensator; own Nelder-Mead), named result 0.700 +- 0.011 recovered vs spurious 0.87 on a seasonal no-excitation day, ledger 7 rows, 4 figures (incl. schematic) checked; 8.5 body pp + 1.5 sol |
| 8 | done 2026-09-24: `firm.queues` (generator, stationary law, first-step solvers, uniformisation, races), named result 73% fill before the 20-order ask empties, ledger 4 rows, 4 figures checked; 8 body pp + 1.6 sol |
| 9 | done 2026-09-24: `firm.dpsolve` (grid backward induction with optional stopping, Gauss-Hermite), Merton named result (51.4%; 60% costs 3.6 bp/yr; mu uncertainty moves pi* by 59 points), ledger 5 rows, 3 figures checked; 8 body pp + 1.6 sol |
| 10 | done 2026-09-24: `firm.impulse` (band costs by renewal-reward, fourth/cube-root laws, combined (a,b) optimum, smooth-pasting threshold), named result band +-34.6m at USD 200/day, ledger 5 rows, 4 figures checked; 9 body pp + 1.6 sol |
| 11 | done 2026-09-24: `firm.estim` (own Nelder-Mead, numerical gradient/Hessian, MLE with Hessian/OPG/sandwich, Newey-West with the 4(n/100)^(2/9) rule, delta method, Sharpe with HAC se), named result t 3.38 -> 1.73 (coverage 62.5% iid vs 92.2% NW), years-to-t=2 chart added for length, ledger 7 rows, 4 figures checked; 9 body pp + 1.5 sol |
| 12 | done 2026-09-24: `firm.multitest` (Bonferroni, Holm, BH, BY adjusted p; max-t single-step and Romano-Wolf step-down with a `null_draws` hook for ch. 13; effective trials; expected max SR; deflated Sharpe), named result best of 200 correlated momentum rules: naive 0.00094, Bonferroni 0.187, max-t 0.030 (fresh histories 2.6%), 32 effective trials; seed 336 chosen by search and said so in the text; ledger 11 rows (Crossref API via curl after the WebSearch budget ran out), 4 figures checked; 11 body pp + 2 sol. Numbers test takes ~3 min |
| 13 | done 2026-09-24: `firm.resample` (iid/moving-block/stationary index generators, Politis-White block length with the PPW 2009 constants, percentile interval, permutation and circular-shift tests, jackknife), named result coverage of 95% Sharpe intervals for a volatility seller: iid 68.5%, stationary automatic 82.75% (40-day 84.0%); permutation test rejects 21.5% of independent pairs vs 2.5% circular shift; bootstrap Reality Check on ch. 12's family 0.0275 vs Gaussian 0.030 (imports ch. 12's teaching module). Brief deviation: hook strategy is a volatility seller (a constant-mean clustered-vol strategy has an iid-correct Sharpe interval). Ledger 6 rows, 4 figures checked |
| 14 | done 2026-09-24: `firm.bayes` (beta-binomial, normal-normal, NIG; EB normal means incl. unequal se by marginal-ML fixed point; positive-part James-Stein; random-walk Metropolis; Gibbs for the hierarchical normal model; Geyer ESS; R-hat), named result best of 50 managers 2.41 -> 1.14 posterior mean, out-of-sample MSE -31% (platform) / -32% (2,000 platforms); selection adds 1.08 on average and EB removes it; seed 203 chosen for the hook's 2.4 (said in the ledger). Ledger 8 rows, 4 figures checked |
| 15 | done 2026-09-24: `firm.robust` (MAD, Qn by bisection-count, Huber location, winsorise/trim, Spearman, Kendall (blocked), tail dependence, Hill, GPD fit (own Nelder-Mead) and quantile); data/methods/eur_fx_ecb_1999_2026.csv (ECB USD/JPY/GBP per EUR) + data/methods/LICENSES.md; named result 99.9% daily EUR/USD loss 1.80 (normal) / 2.74 (t, nu 4.7) / 2.47 (GPD u = 0.93%) and +27% / +6% / +15% from one transposed-digit print (1.5172 for 1.1572, 24 Mar 2026; x7 on the 250-day sd); copula: USD vs GBP rank correlations Gaussian, joint 5% tail 32% vs 20%. Brief deviation: hook uses the EUR/USD print, not a stock. Ledger 12 rows, 5 figures checked; 10 body pp |
| 16 | done 2026-09-24: `firm.linreg` (OLS with classical/HC/HAC/cluster SE, VIF, ridge via SVD, elastic net by coordinate descent, purged expanding folds, Fama-MacBeth with NW, TLS); collinear betas (rho 0.97, VIF 16.9; month 1->2 b1 0.52 -> -1.59, b2 0.84 -> 2.76); regularised prediction test R2 OLS 1.5% / ridge 3.5% / lasso 3.4% (oracle 5.0%); named result hedge ratio 0.85 attenuated by 0.80 to 0.68, Roll-corrected 0.85, weekly 0.80, residual 0.086 vs 0.049; Petersen panel: clustered 0.101 vs true 0.105, FM 0.023. Ledger 9 rows, 5 figures checked; 11 body pp |
| 17 | done 2026-09-24: `firm.tsa` (ACF/PACF, Yule-Walker, ARMA by CSS Gauss-Newton, AR(1) with half-life and Kendall correction, ADF with AIC lags and MacKinnon 2010 response surfaces n/c/ct N=1, periodogram, frac_diff, Hurst R/S and GPH); data/methods/ust_2y10y_daily_1976_2026.csv (FRED DGS2/DGS10); named result 2s10s AR(1) half-life 552 days, Kendall-corrected 739, DF -2.79 (5% -2.86), ADF -2.74/-3.13/-3.55 at 5/10/20 lags; MC with true 739: median 576, 57% fail to reject; GPH d(changes) -0.16. MacKinnon N=2 tau_c coefficients noted for ch. 20 (Table 2: 1% -3.89644 -10.9519 -22.527; 5% -3.33613 -6.1101 -6.823; 10% -3.04445 -4.2412 -2.720). Ledger 12 rows, 4 figures checked |
| 18 | done 2026-09-24: `firm.volfcst` (GARCH/GJR with normal or t, sandwich and Hessian SE, forecasts, EWMA, rolling window, HAR, QLIKE as proxy/h + ln h, MSE, MZ, DM); named result EUR/USD GARCH-t half-life 445 days (persistence 0.9984), ghost 2 Nov 2023: 250-day vol -7.8% when the 11 Nov 2022 +3.5% return left, GARCH +, EWMA +; OOS 2015-2026 QLIKE GARCH < EWMA < window (DM -2.76, -4.10); HAR on simulated RV (no intraday data) beats AR(1). Ledger 12 rows, 5 figures checked |
| 19 | done 2026-09-24: `firm.kalman` (filter with missing data and PED likelihood, RTS smoother with lag covariances, Shumway-Stoffer EM, MLE, local-level gain, bootstrap PF, HedgeTracker); data/methods/wti_brent_daily_2010_2026.csv (FRED/EIA); named result: vol-scaled MLE Kalman hedge ratio cuts Brent-on-WTI hedge-error variance by 0.7% vs 60-day regression, SNR 0.00047, half-response 30 days (= window); unscaled -1.4%; Q x100 follows in 3 days for +6.2% error. Brief deviation (hook) recorded in the ledger. SV particle filter on EUR/USD (phi 0.9, sigma 0.4, ESS min 23). Ledger 8 rows, 5 figures checked |
| 20 | done 2026-09-24: `firm.coint` (VAR, stability, IRF, FEVD, Granger F with own incomplete-beta tail, Engle-Granger with MacKinnon N=1..3, Johansen restricted-constant trace/max with critical values simulated by the module and re-simulated in tests); data/methods/ust_2y5y10y_daily_1976_2026.csv; named result Johansen fly (0.41, -1, 0.61) half-life 43 days vs one-two-one 63; rank 1 (trace 59.8/14.9/2.3); EG -10.04; 5-year windows: no cointegration in 20 of 46. Ledger 7 rows, 4 figures checked |
| 21 | done 2026-09-24: `firm.hfvol` (RV, subsampled, noise variance, TSRV, Parzen kernel, pre-averaging, bipower, Bandi-Russell n*, Roll spread, Hayashi-Yoshida, refresh times, previous tick); simulated market ($36, one-cent grid, trade each second at bid/ask, 25% vol): named result optimal interval 92 s (82 with true noise), 1-s RV 5.8x IV (60% vs 25%); kernel daily error 4.8%; Epps 0.03 at 1 s, HY 0.594. ABDL 2000 attribution removed (unverifiable). Ledger 8 rows, 4 figures checked |
| 22 | done 2026-09-24: `firm.covest` (sample, MP edges/density, LW identity (vectorised b2), LW constant correlation, analytical nonlinear shrinkage LW2020 (validated vs oracle), clipping, PCA factor, min-var); 200-stock factor truth; named result sample MV realised/predicted 1.68 at q = 0.4 (5.71% -> 9.58%, formula 1.67); LW-id 1.51, LW-cc 1.19, NL 1.12, clip 1.11, PCA6 1.17 (best 7.74% vs optimum 7.44%); bias curve and BBP checked. Brief deviation: 200 stocks (q = 0.4) not 500. Ledger 10 rows, 4 figures checked. Tests heavy (~2 min, multithreaded) |
| 23 | done 2026-09-24: `firm.portopt` (Mehrotra IPM for QP with KKT residuals and duals; phase-one Farkas certificate; OSQP-style ADMM with box and SOC projections; PortfolioProblem formulation layer with split variables for gross/turnover; Higham nearest correlation); named result turnover shadow price 0.0159 (1.6 bp utility per 1% turnover), ranking turnover 0.44% > gross 0.28% > positions 0.19% > sector 0.014% > dollar 0 (redundant); certificate: 40 min-position rows + sector-0 equation; 4% vol limit SOC = QP with gamma 25.8, multiplier 1.033. Trap: KKT residuals below 1e-9 vary run to run (BLAS threading) -> floor in CSV, claim '< 1e-9'. Ledger 9 rows, 4 figures checked. Tests ~2 min |
| 24 | done 2026-09-24: `firm.optim` (GD/Nesterov, Newton, L-BFGS with Wolfe, LM, prox_l1/FISTA, ADMM nearest correlation, SGD Robbins-Monro, Bounded transforms, multistart, identifiability, tikhonov); defines calibration; named result daily two-exponential kernel fit: tau2 day-to-day jump median 4.5 d (max 30.7, day 189 56.8 -> 87.6 with equal fit) vs 1.9 (max 9.5) with a 0.01 penalty toward yesterday, fit error +0.7%; multistart 28 best / 35 mirror / 26 boundary / 11 other. Brief deviation (hook = flat valley, mirror valley in multistart) in ledger. Ledger 9 rows, 5 figures checked |
| 25 | done 2026-09-24: `firm.fpkit` in Python, C++20 and Rust, bit-identical on 8 reference results (naive/pairwise/Neumaier sums, Welford mean/var, log-sum-exp, Thomas x0/xlast) asserted as hex in all three; named result Vancouver: 0.0005 x 2,400 x 480 = 576 vs documented 574.081 (sim: truncated ends 422.23, loss 676.7 = 576 x mean(E_n/E_k) 1.175; rounded 1098.57); Neumaier 2.2e-9 < ulp 7.5e-9 at n=1e6; textbook variance 86.84 vs 0.0819 at offset 1e8; NE vs QR 5.3e-3 vs 1.2e-10 at cond 1e7; Cholesky fails at pivot 6 (-0.14), min eig -1.42; CG 1,909 vs 102. JPMorgan task-force 'sum instead of average' quote verified from archived PDF (p. 128). Trap: firm-name gate is a substring match, 'Bitwise' (a firm) flagged the term 'Bitwise reproducibility' -> definition reworded. Ledger 11 rows, 5 figures checked |
| 26 | done 2026-09-24: `firm.mcengine` stage 3 appended (existing listing lines of ch2/ch4 untouched): Philox4x64-10 (matches NumPy's Philox block for block; C++20 unsigned __int128, Rust u128), counter-based philox_uniforms (split-invariant), Joe-Kuo Sobol (first 64 dims in data/ with BSD licence; published 10x3 points reproduced), hash-based Owen scrambling (bit-identical ints in Py/C++/Rust), Acklam norm_ppf, bridge_from_normals, geometric Asian closed form, control_variate, Giles mlmc driver. Named result: at 2^14 paths variance factors antithetic 1.8, CV 853 (rho 0.99941), RQMC time order ~34, RQMC bridge ~2,500, bridge+CV ~37,000 vs 16 needed; MLMC Milstein call eps 0.005: 3.2e7 vs 3.0e9 steps (x94); IS digital z*=3.67, theta 3.8 -> var factor ~1,000. Trap: a \label after \omcode does not label the listing (the macro wraps lstinputlisting in a group) -> never \cref{lst:...}; reported as style defect. Ledger 16 rows, 5 figures checked. Tests ~100 s |
| 27 | done 2026-09-24: `firm.pde` (non-uniform operator with upwinding, theta scheme with Dirichlet / zero-gamma ends, Rannacher, Richardson, amplification, cubic interp, Douglas ADI 2-D); 1-D kernel in C++20 and Rust matching Python to 1e-11. Named result: CN at lambda 32 gamma error 0.84 (doubling with refinement: 0.46/0.84/1.69/3.38); 2 implicit half steps -> first order, 4 -> second order (ratios 4.05, 4.07). Digital: strike on node first order, between nodes second order (Pooley-Vetzal-Forsyth). ADI exchange vs Margrabe first order (kink on diagonal). Ledger 12 rows, 4 figures checked |
| 28 | done 2026-09-24: `firm.aad` (Python reference Tape/Var/Dual/checkpointing; C++20 thread-local tape + Dual; Rust thread_local RefCell tape + Dual + own erfc) with a cross-language 400-input test function (value and 3 gradient components equal to 1e-9..1e-10). Teaching: COS from firm.levy (BS 7e-15 at 64 terms, Merton 2e-12 at 128), VG COS vs MC, Gil-Pelaez digital to 3e-10; UST 2023-07-03 curve (data/methods/ust_curve_2023-07-03.csv) natural spline forward 2.63% at 30y vs monotone rt 3.32-5.67%, linear jumps 0.43pp; implied vol root finders (Newton fails at K=400, Brent 18). Named result: adjoint 3.58 evaluations by op count vs 401 bumps; agreement 9e-6 (bump) / 2e-13 (forward). Trap: the chapter gate counts '' as closing quotes, so f'' in math breaks quote balance -> write f^{\prime\prime}. Ledger 13 rows, 3 figures checked |
| 29 | done 2026-09-24: `firm.bidding` (fp_bid closed and general, pab_bid unit demand, simulate first/second/english/dutch with reserve and clock ticks, multi-unit uniform vs pay-as-bid, Myerson reserve, common value). Named result: equal expected revenue (2/3 single unit n=5; 1 for 2 units, 5 dealers), shading 1/5, optimal reserve 0.5 adds 0.8% (n=5) / 25% (n=2); uniform format revenue sd 0.378 vs 0.160 (matches Treasury study's volatility finding, F2 verified from the Treasury PDF). Kelly: gain = MI 0.363 bits (sim 0.363 +- 0.002). Ledger 12 rows (F1 copied from Book 2 ch 4), 4 figures checked |
| Phase C | 2026-09-24: term config curated (STOP tape/Tape; EXTRA_PROTECT 'bootstrap filter'), linker unwrap+apply: 1,739 links (def 1,729, met 9, thm 1), 464 linkable terms; ch5 gained a definition of 'change of numeraire' (planned term that was only a theorem title); DEFINITIONS.md: all 402 indexed terms match the plan, no moves, the remaining 148 rows are named results (not indexed); tools/gates.sh book methods GREEN (0/0/0, 1,646 definitions series-wide, none twice); tools/figdata.sh methods: 126 CSVs byte-identical after regeneration (7m50s); ch24 ledger F9 lacked its access-date column (fixed). Restored with web search: Patriot/GAO (ch25 F12, with test), ABDL 2000 signature plot (ch21 F9), Cont 2001 tail indices (ch15), BLS CPI 10 Nov 2022 + ECB fixing time (ch18), EIA Cushing/negative WTI and ECB FSR Nov 2025 tariff episode (ch19), Griewank 2012 on Linnainmaa 1970 (ch28 F14). Book: 351 pages (budget ~406), 118 figures, 59 listings, 253 ledger rows; make test-code CH=methods 162 passed (after fixing a latent E501 in ch6 qm_jumps.py, figdata unchanged), all 27 firm components GREEN |
| Phase C | not started |
| Phase D | not started |

## Source verification after the WebSearch budget

The session's WebSearch budget (200 calls) ran out at ch. 12. Bibliographic facts are now checked with
the Crossref API (`curl https://api.crossref.org/works/<doi>`; helper in the scratchpad `qm_doi.py`),
Wikipedia raw citations (`action=raw`), and publishers' or authors' pages fetched with curl. FRED CSVs
come from `https://fred.stlouisfed.org/graph/fredgraph.csv?id=SERIES`.

## Trap: transient red from shared repo-wide checks

`make test-code CH=...` also runs repo-wide checks (module names, chart CSVs) over other books' files; while other agents write, a run can go red for reasons outside Book 4 and green on a rerun. Capture the log and grep before chasing it.

## Identifiers

Entry `one_quant_book_04_methods.tex`, slug `methods`, labels `qm`, teaching modules `qm_*.py`,
linker `--book 4`, figures `OQB_BOOK=4 .venv/bin/python tools/figcrop.py "Figure N.M." out.png`.

## Per-chapter cycle

Same as `sources/markets-1/PROGRESS.md`: sources -> lesson -> code with tests -> figures (charts
from script-generated CSVs, rendered and read) -> 8 exercises (3/3/2), weekend problem, 5-8
interview questions -> solutions with `test_solutions.py` -> chapter gates
(`tools/gates.sh chapter|sources|firms methods/NN-slug`, `make test-code CH=methods/NN-slug`,
`latexmk one_quant_book_04_methods.tex && tools/gates.sh log methods`).
Every simulation a named result leans on gets the time-step test (divide dt by four) and an
ablation of each mechanism the text credits (WRITING section 9).

Before each chapter's definitions: grep `\index{<term>}` over `parts/*/` and read
`sources/SERIES_DEFINITIONS.md`.

## Named results are not terms

The term linker harvests `\emph{term}\index{term}` in definitions; theorem names are results.
`tools/briefs/book4.py` carries a `results` key per chapter (ignored by `make_briefs.py`); the
ledger briefs and DEFINITIONS.md got a results line/table from a one-off script. Do not re-run
`make_briefs.py --book 4` after editing DEFINITIONS.md by hand (it regenerates it).

## Running-project components (proposed; reserved at the sync)

| ch | component | languages |
|---|---|---|
| 1 | mgtest | Python |
| 2, 4, 26 | mcengine (paths; SDE schemes; variance reduction, Sobol, Philox, MLMC) | Python, C++20, Rust |
| 3 | stochint | Python |
| 5 | numeraire | Python |
| 6 | levy | Python |
| 7 | hawkes | Python, C++20, Rust |
| 8 | queues | Python |
| 9 | dpsolve | Python |
| 10 | impulse | Python |
| 11 | estim | Python |
| 12 | multitest | Python |
| 13 | resample | Python |
| 14 | bayes | Python |
| 15 | robust | Python |
| 16 | linreg | Python |
| 17 | tsa | Python |
| 18 | volfcst | Python |
| 19 | kalman | Python |
| 20 | coint | Python |
| 21 | hfvol | Python |
| 22 | covest | Python |
| 23 | portopt | Python |
| 24 | optim | Python (renamed from calib: Book 5 ch. 24 plans `firm.calib`) |
| 25 | fpkit | Python, C++20, Rust |
| 27 | pde | Python; 1-D kernel also C++20 and Rust |
| 28 | aad | C++20, Rust, Python reference |
| 29 | bidding | Python |

## Environment constraints

- `.venv` has numpy and pandas only (no scipy). Plan: numpy-only implementations (own
  optimisers until `firm.optim` exists, special functions such as the Student t and chi-square
  CDFs from regularised incomplete beta/gamma, MacKinnon and Johansen critical values from the
  published tables with ledger rows). If the main session adds scipy, use it only in tests as
  an oracle, never as the implementation the book prints.
- Data: public-domain or attribution-licensed only (FRED H.15 yields, EIA spot oil prices via
  FRED, ECB reference rates). Intraday data are simulated (chapter 21), and say so.

## Calibration

- After ch. 3 (2026-09-24): chapters 1-3 = 12.9 / 11.5 / 10.8 pp all-in (body 11 / 10 / 9 pp from 548 / 498 / 455 lines; solutions ~1.5-1.9 pp from 117-135 lines): **11.7 pp average**, projection 29 x 11.7 + 20 = ~360 pp. Ch. 1 carries the notation tables. On budget; keep ~460-500 body lines.
- After ch. 10 (2026-09-24): body pages 11/10/9/9/9/9/8/8/8/9 = 90 for ten chapters, solutions 18 pp: **10.8 pp all-in per chapter**, projection 29 x 10.8 + 20 = ~333 pp, -5% against the 11-12 pp target (~350). Chapters 7-10 (358-403 body lines) came out at 8-9 body pages. From ch. 11 aim at 9.5-10 body pages (about 450-500 lines): a fifth section or a second worked example with numbers, and four figures in every chapter, not longer prose.

- Budget 11-12 pages all-in per chapter (~350 pp). Definition-dense chapters (15-19 terms: 11,
  12, 15, 16, 17, 25, 26, 29) group several terms per definition box, as Book 2 did.

## Traps met in Book 4 (for WRITING_A_QUANT_BOOK.md section 9 at delivery)

- (Phase A) Named theorems are not linker terms; keep them out of `defines`.
- (Phase A) Other batch books expect some terms at chapter numbers other than the ones planned
  here (characteristic function: ch. 1 as Book 5 expected; Euler scheme: ch. 4, not 26;
  shrinkage: ch. 14, not 22). The sync fixes the pointers.
