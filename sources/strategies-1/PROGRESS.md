# Book 8 — progress and working conventions (resume here)

Written in the main session, no subagents (user ruling 2026-09-24): Book 7 is done; Book 8 now, then Book 9. Budget:
**11–12.5 pages all-in per chapter** (Book 7 measured 11.4); a chapter's strategy files count toward its pages
(~0.5–0.75 page each).

## Status

| ch | state |
|---|---|
| Phase A | done 2026-09-25: 29 briefs (`tools/briefs/book8.py`), DEFINITIONS.md 109 terms, checked against the 1,910-term harvest of Books 1–7 (8 collisions moved to `uses`: borrow fee, utilisation, short squeeze, recall, fire sale, index reconstitution, collar, price limit; near-synonyms of B1 terms avoided: index effect, buffer rule, rebate rate, order imbalance, Stock Connect); every `uses` owner resolved; 113 strategy files (outline brackets); skeleton 0/0/0 (41 pp) |
| 1 | done 2026-09-25: firm.statbook (4 tests), s1_statbook on B7.24's PIT risk model (5 tests); 2 figures, 2 listings, 1 dated, 5 ledger rows; ~9 pp; no strategy files (outline 0) |
| 2 | done 2026-09-25: firm.reversal (5 tests), s1_reversal (5 tests), s1_fetch_strev (French ST_Rev derived stats; data/strategies-1/LICENSES.md started); 3 figures, 2 listings, 9 ledger rows, 4 strategy files; ~12 pp |
| 3 | done 2026-09-25: firm.residarb (4 tests); firm.synthmkt gained MarketConfig.ou_share/ou_tau/ou_disp (off by default, own RNG, alpha['ou']; test added); s1_residarb (4 tests, ~1m45 with pinned threads); 3 figures, 2 listings, 4 ledger rows (Avellaneda-Lee PDF read in full for the method), 4 strategy files; ETF + PCA only (the brief's 'ch. 24 factors' variant replaced by the sector-index version the paper uses); ~11 pp |
| 4 | done 2026-09-25: firm.pairsel (6 tests); firm.synthmkt gained MarketConfig.twin_share/twin_tau/twin_sd (planted substitutes, off by default, own RNG, Panel.twin, alpha['twin']; test added); s1_pairs (4 tests, ~40 s); 3 figures, 2 listings, 5 ledger rows (GGR method from the NBER w7032 PDF), 4 strategy files; ~11 pp |
| 5 | done 2026-09-25: firm.momstrat (3 tests); s1_momentum (3 tests) + s1_fetch_mom (French Mom monthly+daily, derived stats, raw and 126-day vol-scaled to 12%); 2 figures, 2 listings, 7 ledger rows, 5 strategy files; ~10 pp |
| 6 | done 2026-09-25: firm.factorlib (3 tests); s1_factors (3 tests, imports ch5's s1_momentum) + s1_fetch_value (FF5 2x3, Mom, beta portfolios: derived stats); 2 figures, 2 listings, 8 ledger rows, 6 strategy files; ~11 pp |
| 7 | done 2026-09-25: firm.earnstrat (2 tests); s1_earnings (3 tests; default and pead_break panels); 2 figures, 2 listings, 6 ledger rows (Martineau 2022 and Chordia et al. 2009 replace the brief's '1968 to 2010s' hook), 5 strategy files; ~10 pp |
| 8 | done 2026-09-25: firm.lendsig (3 tests; synthetic lending market); s1_lending (4 tests); 2 figures, 2 listings, 1 dated (FINRA 4560), 5 ledger rows (SEC staff report 2021 read for the GME facts), 4 strategy files; ~10 pp |
| 9 | done 2026-09-25: firm.flowpress (3 tests; simulated funds, flows, FIT, pressure overlay); s1_flows (4 tests); 1 figure, 2 listings, 1 dated (Form 13F), 5 ledger rows, 4 strategy files; ~9 pp |
| 10 | done 2026-09-25: firm.indexevent (3 tests); s1_index (3 tests); 1 figure, 2 listings, 1 dated (Russell 2026 semi-annual calendar, LSEG releases), 5 ledger rows, 4 strategy files; ~9 pp. CHECKPOINT: 144 pp with 19 stubs left; ch1-10 add ~10.3 pp each over their stubs (11.3 all-in) -> projected ~340 pp |
| 11 | done 2026-09-25: firm.mergerarb (3 tests); s1_mergerarb (3 tests); 1 figure, 2 listings, 1 dated (HSR waiting periods, FTC), 3 ledger rows, 4 strategy files; ~9 pp |
| 12 | done 2026-09-25: firm.structrv (3 tests); s1_structrv (3 tests; Monte Carlo); 1 figure, 2 listings, 1 dated (SEC SPAC rules 2024), 4 ledger rows, 5 strategy files; ~11 pp |
| 13 | done 2026-09-25: firm.intraday (2 tests; half-hour day model with hedging flow and close imbalance); s1_intraday (2 tests); 1 figure, 2 listings, 1 dated (Nasdaq closing cross, 2019 FAQ), 5 ledger rows (Bondarenko-Muravyev replaces the '1993' overnight hook), 5 strategy files; ~9 pp |
| 14 | done 2026-09-25: firm.intraml (3 tests; causal features, ridge, NumPy GBM, aggressive/passive execution); s1_intraml (3 tests, ~35 s, 20 tape sessions); 1 figure, 2 listings, 4 ledger rows, 4 strategy files; ~9 pp |
| 15 | done 2026-09-25: firm.optsignal (1 test; options layer with informed demand before announcements); s1_options (3 tests); 1 figure, 1 listing, 5 ledger rows, 4 strategy files; ~9 pp. First impact setting (0.01) gave a net Sharpe of 7 in the all-stock book: toned to 0.003 so all-stock ICs are ~0.02 |
| 16 | done 2026-09-25: firm.altstrat (3 tests; panel, nowcast, diffusion, pre-event book); s1_altstrat (3 tests); 1 figure, 1 listing, 4 ledger rows, 4 strategy files; ~8 pp. Full coverage with a 0.71-correlated panel gave a Sharpe of 18: toned to 10% coverage, noise 2 |
| 17 | done 2026-09-25: firm.newsevent (2 tests; news stream with tone, attention by news load, sub-second machine reaction, halts); s1_news (5 tests); 1 figure, 2 listings, 1 dated (Nasdaq halt codes), 4 ledger rows, 4 strategy files; ~9 pp. A perfect tone reading gave a daily Sharpe of 7.6: the daily trader reads with noise 1.5x the tone (68.9% right, keeps the correlation 0.555 of the drift) |
| 18 | done 2026-09-25: firm.limitmkt (4 tests; daily-limit layer over synthmkt: backlog, attention premium, magnet push, queue fills; northbound flows + publication schedule); s1_asia (6 tests); 2 figures, 2 listings, 1 dated (2023 stamp duty, HKEX 2024 northbound-data change), 7 ledger rows, 3 strategy files; ~10 pp. synthmkt returns are SIMPLE: compound with log1p (log-summing scaled simple returns gave high-vol names a variance-drag drift that looked like reversal) |
| 19 | done 2026-09-25: firm.synthfut (4 tests; 40 futures x 4 classes x 30 years, AR(1) drifts hl 252 at 0.5 vol, carry with 0.5 premium, class log-vol AR(1), 3 crashes of 100 days, seasonal curves, curve/contracts) + firm.trendfollow (3 tests); s1_trend (8 tests, incl. WTI via rs_marketdata.wti_series); 3 figures, 3 listings, 4 ledger rows, 6 strategy files; ~13 pp. Crash drift must beat noise: first crash realised only -6.8% (said so in text). Portfolio vol targeting LOWERS the trend blend Sharpe here (levers up when markets disagree) |
| 20 | done 2026-09-25: firm.carrystrat (3 tests); s1_carry (7 tests; carry read from synthfut curves, 12-month slope for seasonal commodities; lambda = 0.5 default and 1.0 variant; WTI carry from EIA c2/c3); 3 figures, 2 listings, 1 dated (BIS Sep 2024 yen unwind), 5 ledger rows, 5 strategy files; ~11 pp. CHECKPOINT: 244 pp with 9 stubs left; ch11-20 added ~10 pp each all-in -> projected ~340 pp (outline 388) |
| 21 | done 2026-09-25: firm.curvestrat (2 tests; contract identity via serial numbers, pair P&L through expiries, z-score, band rule with storage filter); s1_curve (7 tests; EIA WTI c1-c4 real data + synthfut 1-12 commodity spreads); 2 figures, 2 listings, 4 ledger rows (CFTC 2020 report, GHR 2013, Simon-Campasano via EFMA PDF since OpenAlex abstract was wrong), 4 strategy files; ~10 pp. WTI spread MR: gross 0.30 / net 0.05 (0.47 in 1986-2004, -0.32 in 2005-19), -42.7% in 2020; best filter chosen in hindsight, said so |
| 22 | done 2026-09-25: firm.xasset (3 tests; planted diffusion, lag scan + Bonferroni, signals, intraday pair + latency trades on firm.leadlag HY); s1_xasset (4 tests); 2 figures, 2 listings, 4 ledger rows (HTV 2007 + 2014 note, Menzly-Ozbas, Hou), 4 strategy files; ~9 pp. beta 0.2 gave OOS Sharpe 4-6: toned to 0.08 (window scan finds 2/3, lag scan 1/3, no false); intraday Sharpe per day is meaningless (~500): report per-trade bp and sessions up |
| 23 | done 2026-09-25: firm.seasonal (3 tests; stylised calendar, 100 rules, Welch score_rules -- NOT named test_* or pytest collects it, profile, same_month); s1_seasonal (5 tests; synthfut equity class + planted TOM 8bp / pre-holiday 15bp, 4 corrections via firm.multitest; synthmkt same-month plant; WTI months; Henry Hub profile); 2 figures, 2 listings, 5 ledger rows (Ariel and STW specifics excluded: no abstract anywhere), 4 strategy files; ~10 pp. pgfplots xtick={1,...,12} trips the drafty gate: list ticks |
| 24 | done 2026-09-25: firm.posisig (3 tests; published(Tuesday+lag), hedging_market planted premium + trend-chasing speculators, forward, ic with overlap correction, zscore); s1_posisig (5 tests; synthfut commodities; real CFTC corn COT vs IMF maize, skip-a-month); 2 figures, 2 listings, 1 dated (COT Friday 3:30 pm schedule), 6 ledger rows, 3 strategy files; ~10 pp. Hook claim (record longs precede falls) unsourced AND contradicted by corn data: rewritten. IC must be evaluated daily or lag 0 and lag 3 coincide on a weekly grid |
| 25 | done 2026-09-25: firm.futintraday (2 tests; one-minute bar sessions, U-shape, bounce, trend day, planted pre-announcement drift + crowding; orb, fade, pre_announcement); s1_futures (5 tests; cost = half the time-weighted spread of one firm.tape session, 0.54 bp); 2 figures, 2 listings, 1 dated (FOMC 2026 calendar), 2 ledger rows, 5 strategy files; ~10 pp. Message-level tape too slow for 10 years: bars + tape-derived cost, said so. MA(1) bounce shrinks daily vol by 0.926 |
| 26 | done 2026-09-25: firm.voltarget (3 tests; realised/EWMA variance, weights 1/sigma and 1/var, band, run, spike_flows with impact feedback); s1_voltarget (5 tests; 20 synthmkt seeds, ~20 s; synthfut classes; spike scenario); 2 figures, 2 listings, 3 ledger rows, 3 strategy files; ~9 pp. Fund share 5% gave flows of 360% of volume and unstable feedback: 0.2% share; large share + impact makes funds generate their own volatility (exercise) |
| 27 | done 2026-09-25: firm.cryptomf (3 tests; carry_return, basis_carry, coin universe with planted drift + flows, momentum_book, flow_ic, venue_losses); s1_crypto (6 tests; real Binance funding by year + FTX Doc 792-1 balances/flows from Book 3 data; synthetic coins; venue diversification incl. contagion); 2 figures, 2 listings, 1 dated (Binance funding schedule), 6 ledger rows, 6 strategy files; ~11 pp. Expected venue loss pL is independent of the number of venues: diversification only reshapes it |
| 28 | done 2026-09-25: firm.multistrat (3 tests; pods with hidden shared crash factors + dead pod, allocate with factor cap, run_firm with drawdown stops, stop_rate, netting); s1_multistrat (4 tests); 2 figures, 2 listings, 3 ledger rows (Khandani-Lo, Grossman-Zhou, Pedersen metadata), 2 strategy files (outline gives none; ledger labels kept); ~10 pp. Pod-model thresholds only from blogs/Substack (firms named "reportedly"): excluded, no firm named |
| 29 | done 2026-09-25: firm.assetmgr (3 tests; cap weights, covariance, sampled QP on firm.portopt, drift_active, tilt, transition on firm.tcost); s1_assetmgr (5 tests, ~11 s; truth-based risk model with point-in-time styles; NaN size fixed with a floor); 2 figures, 2 listings, 3 ledger rows, 3 strategy files; ~10 pp. Value tilt earns ~0: pit book-to-price is short planted momentum (ch6 trap again) |

## Per-chapter cycle and commands

sources → lesson → code with tests → figures → strategy files → 8 exercises (3/3/2), weekend problem (~20 q.,
Parts I–IV), 6 interview questions → solutions with `test_solutions.py` → gates.

```sh
make test-code CH=strategies-1/NN-slug
tools/gates.sh chapter strategies-1/NN-slug; tools/gates.sh sources strategies-1/NN-slug; tools/gates.sh firms strategies-1/NN-slug
latexmk one_quant_book_08_strategies_1.tex >/dev/null 2>&1; tools/gates.sh log strategies-1
OQB_BOOK=8 .venv/bin/python tools/figcrop.py "Figure N.M." <scratch>/b8/fN_M.png   # then Read the PNG
.venv/bin/python tools/omcode_ends.py strategies-1/NN
```

## Conventions of this book

- Teaching modules `s1_*.py`; running project `code/firm/<component>/firm_<component>.py` (names in the briefs'
  docstring, all checked unique).
- Strategy files: `\begin{strategyfile}{Title}\label{strat:s1:<chapter>:<key>}` with the nine `\sfield`s of
  WRITING_A_QUANT_BOOK.md section 6.3, in order: Who pays you, and why; Instruments and venues; Signal; Sizing and
  execution; Costs; How it dies; Horizon, capacity, infrastructure; Backtest honestly; Sources. No Sharpe ratio
  without its source, period and cost assumptions; say plainly when the public record shows decay.
- Book 7's lessons apply: report simulated effects over seeds; point-in-time exposures via
  `firm_synthmkt.point_in_time_styles`; pin BLAS threads; print from the test's rounding.

## Traps met in this book
- A book neutral only to beta and industries was 99.7% momentum: always neutralise to every style the signal loads
  on, or say what the book is.
- The 1% cap must be iterated (clip, rescale) and clipped once more at the end, or rescaling breaks it.
- A daily reversal book's inherited positions carry the planted post-earnings drift: skip announcement days (scheduled,
  public) or the cost-aware book loses. Neutralise to the model's factors inside the optimiser, not only the signal.
- Grinold's rule needs a per-name score (residual / own specific vol), or high-vol names get their alpha squared.
- Break-even cost is g / (2 tau) with firm_vecbt's one-way turnover (Book 7 ch. 16 proposition); dividing by tau is
  off by two.
- `listed[t + 1]` is known at close t in firm.synthmkt (the delisting return is booked on the last listed day).
- Run chapter tests through `make test-code` (it pins BLAS threads): a test file that imports numpy before the
  module's `os.environ.setdefault` gets multithreaded BLAS and ran 4x slower here.
- The s-score speed filter (kappa > 8.4) passes ~99% of 60-day fits even with no mean reversion: the AR(1) on a path
  pinned at zero is biased toward fast reversion. Say so rather than presenting the filter as a selector.
- Pairs on a market without substitutes: every method loses and the Engle-Granger p-values from a Gaussian random-walk
  null are anti-conservative (7.4% at 5%, 3x at 0.1%) under fat tails and GARCH; BH then keeps 97% false pairs. The
  twin panel was needed to have anything true to find. A planted spread of 5% loses its twins to low-volatility
  coincidences under the distance method; 2% over 10 days is found (311/320).
- The synthetic market has bear markets on only 6.7% of days (two-year window): no momentum-crash mechanism; crash
  material comes from the French factor. Industry momentum is zero by construction (iid industry factors).
- Synthetic value with today's price rebuilt monthly is short the planted momentum (corr -0.56) and loses; FF timing
  (stale price) wins alone; the composite with momentum wins overall. The synthetic SML is steep (CAPM + planted
  premia), so BAB loses there: say so, and use French's beta portfolios for the anomaly.
- pandas MultiIndex to_csv writes empty header names: name the index levels, or csv.DictReader collapses them.
- Event books entered at the announcement's close eat the planted one-day reversal of the jump: enter a day later.
- Simulated funds: style tilts make FIT a style-premium bet (69% over 3 years, no reversal); letting fund sizes follow
  flows explodes FIT (a few funds own everything); flows chasing 4 quarters make FIT persistent. Chapter defaults:
  random holdings, 25% quarterly turnover, fixed sizes. Always compare with an impact-0 control run.
- `make test-code CH=<chapter>` lints only the chapter: run `ruff check code/firm` after adding components (B008
  config-object defaults and long docstring lines slipped through for three chapters). Re-point listing ranges
  after lint fixes.
