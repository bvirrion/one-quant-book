# Book 7 — progress and working conventions (resume here)

Written in the main session, no subagents (user ruling 2026-09-24): Book 7,
then Book 8, then Book 9, in order. Budget: **11–12.5 pages all-in per
chapter** (~350 pp); body 480–560 source lines where a chapter needs 10 body
pages.

## Status

| ch | state |
|---|---|
| Phase A | done 2026-09-24: 29 briefs (`tools/briefs/book7.py`), DEFINITIONS.md 263 terms, no collision with the 1,646-term harvest of Books 1–6, every `uses` owner resolved; skeleton 0/0/0; components reserved in `code/firm/INTERFACES.md` §3–4 |
| 29 | done 2026-09-25: firm.workflow (content_hash canonical, Stage, Pipeline with content-addressed pickle cache and keys from code/params/seed/input output hashes -> early cutoff, manifest with env, reproduce, diff, register in researchlog); reference study 8 stages on synthmkt (snapshot with revisions, liquid 500, momentum + reversal features, cards, blend, monthly book, level-1 with 10 bp, tear sheet with seeded block bootstrap): mom IC .0076 (t 1.39), reversal .0379 (t 16.05), book SR .08 (se .33, CI -.67..74), turnover 3.5%/day; revision outside universe re-runs 5 stages, 1 output changes; inside: all 8; blend weights: 4; tear-sheet code: 1; reproduce [] (unseeded: tearsheet); DAG TikZ + scenarios table, 3 listings, 4 ledger rows |
| 28 | done 2026-09-25: firm.capacity (capacity_curve, profit_maximising, size_at_fraction, avg_pairwise_corr, comomentum, overlap, unwind with square-root impact, permanent share, decay); A: ch27 book at 10 sizes $10m-$30bn: fixed rule (naive, 50-d smoothing) SR 1.79 -> halves at $2.02bn, profit max $3bn ($146m/yr); re-optimised (cost-aware, 1-d) SR peak 2.43 at $1bn, 1.36 at $30bn, profit $806m still rising; B: 5 funds x $2bn, gross 4, 100/side of 500, $200m ADV, 2% vol, one sells over 3 days, 30% permanent, half-life 1 d: others' peak loss .03%..3.07% (proportional to overlap .04/.18/.43/1, sqrt of fraction), peak on day 3, day 15 -1.30%; French daily factors Aug 6-9 2007 HML -2.28% (-10.6 sd), Mom -3.43% (-12.5), Mkt +1.39%, Aug 10 HML +1.42%, Mom +1.15% (derived stats in data/research/ff_aug2007.csv); comovement measure dropped (one seller's push is 0.18 sd, invisible); 2 figures + 1 table, 2 listings, 6 ledger rows |
| 27 | done 2026-09-25: firm.tcost (impact_bp, fit_impact binned log-log exponent + robust-se eta, trade_cost, prox_cost closed form, cost_aware FISTA, net_trades, netting_saving, smooth, breakeven_cost); A: 5,000 simulated parent orders from 2 bp + .7 sigma sqrt(Q/V) + price move: eta .71 (.08), exponent .48 (.03); 500 orders 1.09 (.24), 50,000 .67 (.03); B: ch26's 50 names daily, forecast = truth + 1.5x noise daily, gamma 72: naive $1bn gross 2.56 net -29.47 (costs 1,223%/yr, turnover 5.33/day); cost-aware net -.31/.06/1.80/1.76 at $10m/100m/1bn/10bn (small funds chase noise); smoothing at $1bn: naive peak 1.15 at 50 d, cost-aware 2.43 at 1 d; two-team netting 8.27+8.73 -> 16.04 (saving 5.7%, same-side +2.94 points); Almgren et al. 3/5 power vs Toth square root; 2 figures + 1 table, 2 listings, 4 ledger rows |
| 26 | done 2026-09-25: firm.allocation (mean_variance and robust_mv by majorisation over portopt.qp, implied_returns, black_litterman He-Litterman form, risk_contributions, risk_budget Newton, erc, hrp with single linkage + bisection, gp_trade_rate, gp_aim); A: 50 largest long-only <=10%, 95 months, gamma 20: per-bp turnover MV .029%/.33% max, sample .028/.24, robust (kappa 3) .028/.12, BL .031/.11, risk-based 0; redraw turnover 23.9/23.4/22.4/24.4% vs 0; net SR .57/.77/.61/.72/.65/.67/.66/.65 (se ~.4: none distinguishable); ERC vol 18.4 between MV 15.8 and EW 19.3; HRP max 5.8%; B: 50 names long-short daily, true signals (drift phi .00137, PEAD 1/60, reversal 1), gamma 72, quadratic costs: lambda 100 daily Markowitz 5.14 -> -.51 (costs 56.6%/yr) vs aim 4.74 -> 4.06 (rate .56, reversal weight .56), partial 3.36, monthly 2.96; lambda 1000 aim 3.15 vs daily -22.62; lambda 1e4 only aim positive 1.61; 2 figures + 2 tables, 3 listings, 8 ledger rows |
| 25 | done 2026-09-25: firm.portcons (Problem in factor form over firm.portopt.qp: equality/neutral_factors/bounds/liquidity/gross/turnover/turnover_penalty; split variables only when needed; duals, binding counts, per-constraint pull vectors with alpha - gamma Sigma w = sum; ir_decomposition exact; ir_ex_ante; trade_list); 100 largest synthmkt names, 95 monthly rebalances, alpha = stock-specific truth + 2x noise (new monthly), IC .05 scaled, ch24 model monthly, gamma 12, 10 bp costs: naive (sample cov 126 d, raw alpha) ex-ante 4.25 / realised .92 / net .43, gross 61, vol 36% vs 207%, turnover 84/month; dollar 1.64/1.89/1.39; factor 1.59/1.72/1.22; names 1.41/1.29/.83; gross 1.44/1.40/.94; liquidity ($1bn, 5% ADV, 28 bind) 1.23/.87/.46; turnover limit 1.00/1.94/1.77 (noise averaging; TC .97 -> .58); decomposition at level 6: turnover 44.0%, liquidity 39.4%, factor 7.0%, names 3.1%, gross 0; 3 figures + 1 table, 2 listings, 5 ledger rows |
| 24 | done 2026-09-25: firm.riskmodel (cs_regression WLS with KKT constraints, factor_returns, ewma_cov with Newey-West, vra from cross-sectional bias, specific_var EWMA with group shrinkage, portfolio_risk with contributions, pca_model, bias_stat, bias_band); firm.synthmkt gains point_in_time_styles (size at listing, log B/P from first-filed book rolled with returns, momentum z reset monthly; tested against the simulation); 15-factor model on PIT exposures (country + 10 industries cap-weighted constraint, beta, size, value, momentum; model from day 252), same without momentum, 15-PC statistical; R2 .19; vols country 17.8%, industries 8.0-8.7%, momentum 7.2%; exposed book (.5 mom + noise, 100/100, neutral to the no-momentum model): full 9.23/9.20 bias 1.04, no momentum 3.26/9.20 bias 2.86 (ratio 2.83), PCA 5.59 bias 1.68 (loadings reset monthly); random books 1.00, 92% in band (98% no VRA); market rolling .50-1.55 -> .56-1.32, outside 66% -> 44%; specific deciles 1.13..0.93 -> .97..1.04; 2 figures + 1 table, 3 listings, 5 ledger rows |
| 23 | done 2026-09-25: firm.markout (microprice, ref_at, markouts, curve with se by group, settle_horizon, fill_rate, hit_ratio, mm_decompose exact spread/adverse(H)/inventory/fees, shortfall delay/execution/opportunity/fees, vwap_slippage, tca_report); touch quoter vs imbalance-pull quoter as firm.tape agents, 12 one-hour sessions: 8,144/18,000 lots (45%) vs 3,309/16,391 (20%), informed 42%/40%, mark-out .43 -> -.67 at 20 s (settles by 2 se rule), informed -1.85/-2.71, uninformed +.18/+.52, microprice .19; decomposition +3,519/-8,977/-1,060/-407 = -6,925 (annualised x136.5: +480k/-1.23m/-145k/-56k = -945k); pull -2,685, 97% of the saving from fewer fills; executor 300 lots min 11-30: TCA dominated by market move (shortfall -2.00 se 2.73; paid vs mid +0.10 se 0.03), counterfactual impact +0.25 (tape V exogenous); Menkveld 1.55/-0.68/0.88; 3 figures + 2 tables, 3 listings, 3 ledger rows |
| 22 | done 2026-09-25: firm.perf (from_returns, sharpe via firm.estim, lo_sharpe, drawdown/max/spells/longest, calmar, sortino, omega, hit_rate, profit_factor = Omega(0), holding_period, alpha_beta via firm.linreg HAC, smoothing_profile with invertibility, unsmooth, tear_sheet); four synthetic streams (trend 15% vol SR .75; short 5% OTM puts on GJR-GARCH-t index, notional 3.4, long-run vol 17%; GLM-smoothed book (.5,.3,.2); market maker SR 4) + ch16 momentum BacktestResult; hook trend SR 1.00 DD -33.6% 791 d vs short vol 1.09 no losing quarter (9% of paths) DD -14.8%; named result P(30% DD in 5 y) 14% vs 41%, smoothed SR se .46 iid vs .63 HAC; Lo .61, unsmoothed .59, true .66, theta (.43,.36,.21); short vol skew +5.38 sample vs -1.23 long run; up/down beta .98/.71; momentum holding 48 d; 3 figures + 2 tables, 3 listings, 8 ledger rows |
| 21 | done 2026-09-25: firm.abtest (SHA-256 bucket/assign, diff_means, cuped with pooled OLS theta, stratified, cluster_diff order-weighted with cluster-robust se, demean_by, power, mde, sample_size, srm_pvalue, msprt, always_valid_p); simulated flow 2,400 orders/day in 500 Zipf stocks, sd 23.1 bp, direct saving -0.30, sibling spillover +0.25 (88% with siblings) -> rollout -0.08; hook 10% x 2 weeks -0.55 (se 0.48), SRM z 1.83; designs over 100 experiments x 60 days: order-level 77 days for 0.3 bp, CUPED (pre-trade + market move, R2 .51) 38, day 3,253, stock-day within day + CUPED 35 (estimates rollout; 503 days to detect it); peeking 29%/33%/38% at 38/60/120 looks vs mSPRT 46/62/82 of 4,000; stop median 38 d, harm +1 bp 6 d; canary 194/214/385 orders at 1/10/50%; Knight SEC order; stages TikZ; 3 figures + 1 table, 3 listings, 8 ledger rows |
| 20 | done 2026-09-25: firm.overfit (cscv by block sums with sampled splits -> pbo, logits, slope; purged_kfold with embargo; cpcv, cpcv_paths; walk_forward; min_backtest_length by bisection on firm_multitest.expected_max_sr); 1,000 MA trend systems on 25 synthetic years (20 search / 5 test), noise and planted persistent trend: IS best .44/.77 -> OOS -.32/.14 vs average .20/.26; PBO .82/.74, slopes -.89/-.91; ranking corr -.05/.33, top-50 OOS -.02/.29; walk-forward -.04/.29; systems' SR spread .076 -> expected max .25 (iid 0.77); MinBTL 42.4/10.6/3.3 y for SR .5/1/1.8 at 1,000 trials; label leak R2 shuffled .90, contiguous -.63, purged -.57, embargoed -.93; exercise 7 PBO .69 (100 correlated) vs .52 (100 independent); 3 figures, 2 listings, 4 ledger rows; 8 body pp |
| 19 | done 2026-09-25: firm.tape gains an agent (simulate(cfg, agent=...): the agent's orders are real orders, never background-cancelled, seen by others; delay_data/delay_entry/on_market/on_fill; Tape.own, Tape.agent_fills; default None, all earlier tapes unchanged); firm.simlive (FILL, as_fills, match_fills, parity, fill_pnl, waterfall, calibrate, implementation_shortfall); quoter live in 6 tape hours vs lobreplay: live 597 lots/h vs replay 305, parity 27%/54%; decomposition -50.5 -> -56.4 (latency) -> -112.8 (market, within chance 62.8) -> -431.2 (fills) -> -490.9 (fees); 68% of live lots from trades that stopped at the quoter, 21% alone at price (mark-out -0.85 vs -0.11); latency calibration cannot close the gap (1,898 vs 3,582 lots), front model 8,886 lots and +$2,207 vs live -$2,587; 2 figures, 2 listings, 1 ledger row; ~8 body pp |
| 18 | done 2026-09-25: firm.lobreplay (Book by oid, Shadow orders, QueueTracker front/fifo/prob, Replay with entry and data latency, Strategy.on_market/on_fill, track_fifo reference; C++20 core cpp/firm_lobreplay.hpp and Rust twin reproduce the 29 fills of the shared fixture: 8,513 msgs, 75 shadow orders, 50 ms); touch quoter on 2 tape hours: front $1,106/h (61% of volume) -> $192 at 5 s; fifo -$76 (10%), mark-out +0.008 -> -0.001 at 50 ms -> -0.115; prob -$49; impact bound $26/h; see late worse than act late; ch17's bar quoter at level 3: 344 lots/day, -$239, mark-out -0.77 (between touch and penetration); queue TikZ; 2 figures + 1 table, 2 listings (Python + C++), 3 ledger rows |
| 17 | done 2026-09-25: firm.evbt (Order/Fill, lifecycle pending->working->partial->filled/cancelled, TouchFill, PenetrationFill, VolumeCapFill, Strategy callbacks, Engine with heap (time, kind, seq), latency, conservative/optimistic live-in-bar policy, splits, BacktestResult); passive quoter on 4 tape days of 1-min bars: touch 523 lots/70%/+$17/-0.16 tick, penetration 290/41%/-$584/-2.00, capped 2.5% (Zipline default) 388/55%/+$20; 5 s latency: none (conservative), -$41/-$776/-$190 (optimistic); level-1 -$215; at-close orders 95%/70% fill; architecture TikZ; 2 figures + 1 table, 2 listings, 1 ledger row |
| 16 | done 2026-09-24: firm.vecbt (BacktestResult with turnover/gross/net exposure; signal_to_weights; backtest with lag 0/1/2, PIT universe, per-name caps, linear costs, borrow, cash and leverage financing, drift, compounding); reversal waterfall 7.17 -> 7.22 -> 6.95 -> -2.58 -> -2.64 -> -9.45 (lag0 -65), turnover 74%/day, break-even 7.3 bp, compounded .35 vs summed -.04; momentum 0.21 -> .44 (survivorship lowers it) -> .32 -> .21 -> .19 -> .17; smoothed reversal turnover 42%, SR 4.13, break-even 7.4 bp; fidelity-levels TikZ; 3 figures + 1 table, 2 listings, 2 ledger rows |
| 15 | done 2026-09-24: firm.forecast (scale_rule, binned, isotonic PAV, mincer_zarnowitz, effective_breadth, transfer_coefficient, law_ir, qian_hua_ir, ding_martin_ir, information_ratio); planted IC .05 on 704 synthmkt residual returns: score +2 -> 77 bp, IC hat .055, MZ slope .92 (R2 .24%), raw slope .0039; law 4.60 vs Gaussian book 4.92 (se .45), market IC sd .0424 vs .0331 -> 569 effective names, QH 4.13, book 4.26; long-only TE grid TC .98->.86, IR 3.91->3.00 (47% clipped), concentrated benchmark TC .59; named result 4.60 -> 4.13 -> 3.54 -> 3.00 (two thirds); prop. scaling rule + generalised law with proofs; 2 figures + 1 table, 2 listings, 5 ledger rows |
| 14 | done 2026-09-24: firm.combine (zscore, ic_series/matrix, equal, blend, ic_weights, max_icir with diagonal shrinkage, toward_equal, ridge, lasso, nnls, stack with time folds, orth_sequential, orth_symmetric, residualise_on); 40 planted signals in 8 themes on synthmkt monthly residual returns, two worlds (stable unequal quality / drifting equal quality); geometry prop. (measured .064 vs .065, ceiling .090); full-panel table (IC-w .099/.075 vs equal .064/.060, raw max-ICIR worst .064/.041); small universe (100 names, 12 m): stable lambda* .4 (.081), IC-w .086; drifting lambda* 1 (equal .069), OLS .005; stacking picks IC-w; symmetric orth = raw .064, sequential .050; 2 figures + 1 table, 2 listings, 5 ledger rows |
| 13 | done 2026-09-24: firm.decay (ic_decay single-day lags, grid least-squares half_life_fit, rank_autocorr, half_life_ar, turnover, block_bootstrap, BDE cusum with 0.948 boundary, vectorised sup_f, simulated and permutation p-values, decline_power); synthmkt gains pead_break/pead_after; decay table (reversal <1 d, surprise linear 60-d life fit 20 d, momentum/value no decay in 60 d; turnover 104%/1.7%/0.53%/0.05% a day); momentum planted constant fails both tests (sup-F p .023); planted removal: sup-F p .013 at month 53, CUSUM silent; power over 10 seeds (removal 10/5, 70% cut 7/3, 50% cut 3/1, none 1/1); French SMB/HML/Mom pre/post publication 97/55/56% declines, sup-F p .18/.15/.053; named result posterior .57/.72/.999; 4 figures + 2 tables, 2 listings, 8 ledger rows |
| 12 | done 2026-09-24: firm.vendoreval (coverage, backfill_share, fit_by_group, cusum_break, rank_ic, ic_by_group, residualise, incremental_ic, long_short, breakeven, tone); synthetic card-panel trial on synthmkt earnings (400 retailers, backfilled years 1-2 fitted to outcomes, provider change = live launch at year 3, owned signal): fit slope .92/.87 -> .37/.39/.35, CUSUM break year 3 (3.05), IC .38/.37 -> .12-.15, incremental IC .10 (t 4.0), spreads 10.4/3.4/2.9% a quarter, break-even $5.06m (pitch) / $1.59m / $1.35m at h=2y, $0.43m at 6 months; synthetic corpus (general list .74 vs finance .87, net .95, finance words 77% of general negatives); 1 dated box (App Annie, hiQ, GDPR), 3 figures, 3 listings, 8 ledger rows |
| 11 | done 2026-09-24: firm.fundpit (duration kinds into firm.pit Store, quarterly as-known with Q4 = FY - 9M, TTM, SUE seasonal RW, restated + split_ratio to the cent, revision, dispersion, days_to_event, in_window); EDGAR (10 companies, submissions + companyfacts, public domain) -> edgar_filings.csv / edgar_eps.csv: release 23 d / 10-Q 29 d median, 10-K 26/48, 16% same day; 31 changed EPS values (24 split ratios; Microsoft ASC 606 recast 2.71 -> 3.25); Apple first-reported TTM 28.82 vs annual 6.45; synthmkt: SUE IC 0.020 known vs 0.167 period end (x8), B/P within noise; 1 dated box (SEC deadlines), 4 figures + 1 table, 2 listings, 10 ledger rows |
| 10 | done 2026-09-24: firm.leadlag (HY ccf at lags normalised by 1-min RV, argmax + symmetric-centre lead, lead-lag ratio, directional corr, leave-one-out peers, linked_feature, lagged corr matrix, top_pairs); synthmkt gains link_share/link_beta/link_days + Panel.customer (own RNG, default off); French size quintiles (derived stats only, ff_size_leadlag.csv): weekly small<-big .31/.23/.06, own .37, partial t 1.9; planted links: event study 4.5% vs 0.39%, customer momentum IC .035 (t 5.6) vs truth .074, mining 8 of 133 in top 10k vs 2.7 random; tape pair: centre MAE 0.053 s vs argmax 0.19, slow pair fails, asymmetry .13/.17/.10/0 at 2/5/10/30 s; 4 figures + 2 tables, 3 listings, 8 ledger rows; 11 body pp |
| 9 | done 2026-09-24: firm.tradeflow (tick/quote/Lee-Ready, BVC, sign ACF, aggregated-variance Hurst, VPIN on volume buckets, Kyle's lambda, mark-out toxicity, order aggregation); tape gains news_noise; signing accuracy (quote 1 s late 96.3%, tick 95.2%, BVC 80.4%), sign ACF .20 -> .028, H .715 vs .75 predicted (LMF), signed-flow table (next sign 58.4%, corr with past 10 s twice the next), Hawkes 0.65 vs flat 0.403, named result VPIN +13% while mark-out -0.36 -> +0.96; 4 figures + 1 table, 2 listings, 9 ledger rows; 10 body pp |
| 8 | done 2026-09-24: firm.lobfeat (Python reference + C++20 hpp + Rust crate; shared fixture of 2,769 msgs, 2,766 rows matched in all three); up-move P by imbalance 0.245-0.736 vs birth-death race 0.017-0.979 (overconfident), OFI R2 10/53/79% at 1/10/60 s, one-step microprice vs weighted mid, stale-cancel feature corr .30; 4 figures, 3 listings, 3 cards, 5 ledger rows |
| 7 | done 2026-09-24: firm.features (rolling/past returns, vol and range estimators, volume/Amihud/turnover, MA crossover + filter weights, leakage_test); IC table of 12 features (non-overlapping), skip-month hook (synthmkt: 12 > 12-1 since reversal is 1 day), range race (eff. 5.2/7.6/5.7/7.5; discrete-monitoring bias 8-10%; drift, gaps), cards momentum 12-1 (half-life 260 d) and volume surprise (not planted); 3 figures + 1 table, 2 listings, 8 ledger rows |
| 6 | done 2026-09-24: firm.predictor (forward_return, residualise/neutralise, zscore, rank_transform, ic_series, ic_summary with HAC, quantile_spread, PredictorCard); horizon table (1d/1d .0385 vs 5d/5d .0074 = hook), neutralisation shown in an ind_vol=0.30 variant (IC .0043 -> .0086), overlap t 3.85 vs 2.39; first predictor card (one-day reversal); 3 figures, 2 listings, 5 ledger rows; ~9 body pp |
| 5 | done 2026-09-24: firm.synthmkt (GJR-GARCH-t market, industries, size/value/momentum styles, planted alphas momentum/value/pead/reversal stored at t for t+1, earnings jumps, delistings/mergers/splits/dividends, PIT fundamentals with restatements, secmaster; seed 1 default: mkt 6.3%/16.4%, kurt 20.5; rev IC .034, 12-1 mom IC .030); French data -> derived stats only (ff_*.csv, incl. 10-industry exceedance correlations); honest scorecard (misses lag-100 memory, monthly kurtosis, correlation asymmetry); 4 figures, 2 listings, 11 ledger rows; 10 body pp. Part I = 49 body pp (~12 pp/ch all-in) |
| 4 | done 2026-09-24: firm.secmaster (permanent ids, dated tickers, resolve/ticker as of, delist records, reused(), buffered_universe, churn); simulated listing history (splits, renames, reuse, merger and performance delistings); named result = 164 spliced ticker returns (mean 164%) + adjusted-price floor leak (dropped names +71% vs 15%); META (SEC 8-K) and GM (S-1/A) facts; 4 figures, 2 listings, 7 ledger rows; ~8.5 body pp |
| 3 | done 2026-09-24: firm.pit (bitemporal Store, Guard/LookAheadError, asof_join); real-time payrolls from the Philadelphia Fed RTDSM (ALFRED refuses scripts) -> data/research/ via rs_fetch_payrolls.py; survivorship simulation (bias 5.2 pts at 2.2%/yr delisting; identity w(rS-rF)); 4 figures, 2 listings, 0 dated, 10 ledger rows; ~9 body pp |
| 2 | done 2026-09-24: firm.tape (event-driven LOB simulator: efficient price, stale-quote cancels, Hawkes noise flow in metaorders, informed flow, OU activity level, U-shape, news; opening snapshot; Book replay; simulate_pair) + firm.bars (time/tick/volume/dollar/imbalance bars, asof, continuous futures); day = 1.56M msgs in ~10 s; WTI 2015-2024 continuous series from Book 3's EIA data; 4 figures, 2 listings, 1 dated box (ITCH sample sizes), 9 ledger rows; 9.5 body + 2.3 sol pp |
| 1 | done 2026-09-24: researchlog (hash-chained, post-hoc flag, deflation via multitest); 4 figures (PPV, best-of-n, stage gates TikZ, search + deflation), 2 listings, 0 dated, 7 ledger rows; 10 body + ~2.3 sol pp |

## Checkpoint after chapter 20 (2026-09-25)

Chapters 11-20 took 88 body pages (8-11 each, 8.8 average); with ~2.4 solution pages each that is ~11.2 pp per
chapter all-in, at the bottom of the budget. Projection: 184 body pp for ch. 1-20 + ~48 solutions + 9 x ~11.5 +
~12 matter = ~350 pp (outline ~398). Chapters 21-29 (live experiments, performance, markouts, risk model,
portfolio construction, allocation, cost models, capacity, workflow) carry the components Books 8-9 depend on:
aim at 9-10 body pages each rather than cutting.

## Checkpoint after chapter 10 (2026-09-24)

Body pages 96 for ch. 1-10 (8-11 each), solutions 24 pp (2.4 each): 12 pp per chapter all-in. Projection:
29 x 12 + ~12 front/back matter = ~360 pp, inside the 11-12.5 pp/chapter budget (outline ~398). No change of
plan; chapters with a C++/Rust build or a real-data study run to 11.

## Per-chapter cycle and commands

sources → lesson → code with tests → figures → 8 exercises (3/3/2), weekend
problem (~20 q., Parts I–IV), 6 interview questions → solutions with
`test_solutions.py` → gates.

```sh
make test-code CH=research/NN-slug
tools/gates.sh chapter research/NN-slug; tools/gates.sh sources research/NN-slug; tools/gates.sh firms research/NN-slug
latexmk one_quant_book_07_research.tex >/dev/null 2>&1; tools/gates.sh log research
OQB_BOOK=7 .venv/bin/python tools/figcrop.py "Figure N.M." <scratch>/b7/fN_M.png   # then Read the PNG
.venv/bin/python tools/omcode_ends.py research/NN
```

Crossref helper for bibliographic ledger rows: `<scratchpad>/cr.py <doi>` or
`cr.py -q "title author"` (no search budget used).

## Conventions of this book

- Teaching modules `rs_*.py`; running project `code/firm/<component>/firm_<component>.py`.
- Predictor cards (`pred:` labels) do not define strategy names as terms; Books
  8–9 own the strategies.
- Data licences: FRED/ALFRED, SEC EDGAR, ECB, EIA are public; the Kenneth
  French data library carries a copyright notice and no licence, so only
  derived summary statistics go into `data/research/` (raw series never
  redistributed), fetch script kept for provenance.
- Stage-gate schematic: `text width` on nodes; `scriptsize`; the text width of
  the page is ~14 cm (a 7-box row at 2.1 cm spacing fits).

## Traps met in this book

- (ch 27) A homoskedastic standard error for eta was 2.9 se off the planted value at 500 orders: the price noise grows
  with the order's size; use a robust (White) standard error (z-scores then have sd .84 over 40 seeds).

- (ch 26) The brief's hook (a third of the gross turned over for one basis point) is not what a well-scaled book does:
  0.03% on average. The meaningful perturbation is a redrawn forecast (24%). HRP bisects by position in the dendrogram's
  order, not by cluster: a test expecting equal weights inside a block was wrong. Quadratic costs make scale matter: with
  the book at 0.36% volatility no rule paid costs; set gamma for a realistic volatility first.

- (ch 25) The planned hook (45% of a book in two names) did not happen: with Grinold-scaled alphas and a factor model the
  top two hold 8%; with a sample covariance the errors spread over hedged combinations (gross 61x, vol 36% forecast vs
  207%). Report the pathology the simulation produces. A fig script that imports numpy before the rs module escapes the
  BLAS-thread pin (4 minutes, 86 CPU-minutes): tools/test_code.sh and tools/figdata.sh now export
  OPENBLAS_NUM_THREADS=1. Solver timings are machine-dependent: never print them as numbers.

- (ch 24) firm.synthmkt's Panel.style_x holds the exposures of the LAST day (value moves daily, momentum monthly, in
  place). A risk model on them looked calibrated (bias 1.02) with a momentum factor of 3.3% volatility; on point-in-time
  exposures the factor is 7.2%, the truth. Use firm_synthmkt.point_in_time_styles; never read style_x as history.

- (ch 24) BLAS threads on many small matrices turned a 12-second model into 6.5 minutes (135 CPU-minutes): pin
  OPENBLAS_NUM_THREADS=1 before numpy's import in modules that loop over days. A style whose exposure is constant during
  a warm-up (estimated beta = 1) has a zero-variance factor, and the regime multiplier divides by it (lambda^2 = 2.5e7):
  start the model when every exposure exists. A book not neutralised to included factors correlated with the omitted
  one (value vs momentum, -0.64) hides the omission: build the demonstration book neutral to the model's factors.

- (ch 23) Twelve tape seeds had a mean mid move of -10 ticks over the order's window and +2.9 in the delay minute with no
  order at all: arrival-price TCA over a few orders measures the market. Run the counterfactual session (same seed,
  no agent) before attributing anything. firm.tape's efficient price ignores the agent: permanent impact is nil by
  construction; say so. A fixed tolerance for 'the curve has settled' is fragile: use two standard errors of the
  last horizon.

- (ch 22) An MA smoothing profile and its time reversal have the same autocorrelations: restrict to invertible profiles
  or the estimate comes out reversed. A calm history chosen for 'no losing quarter' shows positive skew (+5.4) for a
  short-put stream whose long-run skew is -1.2: say which sample a shape statistic describes. Crash-dominated volatility
  differs across long paths (15% at one seed, 17% at another): do not claim two streams have equal volatility.

- (ch 21) The unweighted mean of cluster means estimated a different quantity (-0.18) from the rollout (-0.08) when clusters
  are unequal (Zipf stocks): weight by orders. And a common day shock across clusters made the cluster-robust se 11% too
  small until the analysis was within day (demean by day). One simulated experiment per design was 2.7 se off its truth:
  print designs as the mean and spread over many experiments.

- (ch 20) The winner of a search over correlated systems on a common trend earned less out of sample than the average
  system, although the in-sample/out-of-sample ranking correlated at 0.33: say both (the ranking carries information,
  the single argmax concentrates noise) or the lesson overclaims.
- (ch 20) An edit script that asserts each replacement aborts on the first miss and writes nothing: rerun after
  fixing, and check the file really changed before testing.

- (ch 8) `repr(np.float64(x))` is 'np.float64(x)' in NumPy 2: fixture files for C++/Rust must write float(x).
- (ch 8) C++ std::map with std::greater and std::map are different types: one accessor cannot return both
  (use a generic lambda).

- (ch 7) A momentum IC series is dominated by a few factor days: sampling every 5th date gave means from 0.004 to 0.020
  by offset. Use all dates for means (HAC for errors), never a thinned sample for a mean.
- (ch 7) Rogers-Satchell looked 'biased' under drift until the benchmark was fixed: close-to-close measures
  sigma^2 + mu^2; range estimators target sigma^2. Say which quantity an estimator targets before scoring it.

- (ch 5) A seed's market path can be 2.7 SE off its intended mean (seed 7: -10.8%/yr): scan seeds for a typical path
  before freezing a default, and say which seed.
- (ch 5) Stationary GARCH cannot give autocorrelation of |r| at lag 100 on a 10-year path; persistence 1 (IGARCH)
  gives memory but no variance level (vol wandered 1.7%-23.6%). Downside betas flip correlation asymmetry only
  with a compensating drift, else the mean return collapses (-20%/yr). Report misses; don't hide them.
- (ch 19) A replay of the live session without the strategy's own messages is structurally blind: trades that stopped
  at the strategy vanish, and levels it was left alone at empty. Measure these (vanished volume, alone-at-price) before
  calibrating; calibrating fill counts with an optimistic model inverts the P&L.
- (ch 18) Module names must be unique across code/: a second make_fixture.py failed the gate; name fixture scripts
  after their component (make_lobreplay_fixture.py).
- (ch 18) C++ tests locate fixtures via __FILE__, which is relative when compiled from inside cpp/: build from the repo
  root with an absolute path, as tools/test_code.sh does.
- (ch 18) Never run git mv (or any git write) even on untracked files; use mv.
- (ch 17) A bar-level fill check at bar end cannot see an order live for part of a bar: with latency and cancel-replace
  every bar nothing ever fills (conservative). Make the policy explicit (conservative/optimistic) rather than hide it.
- (ch 17) Python's round(-41.5) is -42 but the mean was -41.4999: print from the test's rounding, always.
- (ch 15) Two different synthmkt panels in this book: the default (seed 1) lists 704 names for all ten years; the
  chapter-10 panel with link_share=0.3 lists 698. Chapter 14 printed 698 for the default panel until the chapter-15
  check caught it: assert N in every test.
- (ch 15) Average pairwise correlation of cross-sectionally demeaned residuals is about -1/(N-1): useless as a breadth
  measure. Use the IC's dispersion, (mu_IC / sd_IC)^2 / IC^2, instead.
- (ch 14) With 698 names x 60 months, 40 blend weights are estimated almost exactly: the forecast-combination puzzle
  needs a small sample (100 names, a year) and equal-quality, drifting information to show. Plant the world the
  lesson needs, and say which world it is.
- (ch 14) `L\"owdin` trips the straight-quote gate: write the literal character (Löwdin).
- (ch 13) Changing MarketConfig.days (or any size) reruns the whole random stream: a longer market is a different
  market. To study power, vary seeds at a fixed length.
- (ch 13) One simulated market is one draw: a planted 70% cut was invisible in seed 1 and found in 7 of 10 seeds. Report
  detection rates over seeds, not one outcome.
- (ch 13) The `\end{solution>` slip happened a third time: grep every new solutions file for it before building.
- (ch 13) Rounding at the third decimal: 0.0535 -> 0.053, 0.0135 -> 0.013 (binary floats); always print from the test.

- (ch 12) EUR-Lex HTML is behind a WAF challenge; the Publications Office Cellar serves the same act as XHTML:
  `curl -L -H "Accept: application/xhtml+xml" http://publications.europa.eu/resource/celex/<CELEX>`. eCFR's API
  needs `--compressed`.
- (ch 12) In a pgfplots axis with `ybar` in the axis options, every later line plot gets a bar legend image: put
  `ybar,area legend` on the bar plot only.
- (ch 12) Never hard-code a fitted value in a figure (a fit line's slope): write it to a chart CSV.

- (ch 11) `ytick={0,...,9}` trips the drafty-ellipsis gate: write the list out.
- (ch 11) A dated box needs a ledger row whose "used in" names its `dat:` label, not "dated box".
- (ch 11) A synthetic value IC differed by 0.034 between two keyings and was pure noise (se 0.038): each quarterly
  cross-section's IC is dominated by the factor's realised return in its window. Print standard errors with every
  IC comparison.
- (ch 11) SEC EDGAR, Crossref: use a descriptive project User-Agent (no personal email in headers); Crossref without
  mailto rate-limits bursts (429): sleep 3-5 s between queries.
- (ch 10) A flat-topped cross-correlation (both series react to one price with a spread of delays) makes the argmax
  noisy (0.15 s for a planted 0.5); the centre of symmetry (among lags at >= half the max) recovers it within 0.05 s.
  Restrict the centre's candidates, or the zero tails far from the peak are "perfectly symmetric".
- (ch 10) firm.tape mids trend at short intervals (own lag-1 correlation 0.44 at 2 s with v_rate=1): any lead-lag or
  short-horizon study on the tape must compare against the follower's own past and the reverse direction.
- (ch 10) Written twice now: a solutions file closed with `\end{solution>`; grep the last line before building.
- (ch 10) 0.0825 rounds to 0.082 in float: print from the test's rounding, never from a glance at 4 digits.

- (ch 9) A TikZ style named `out` collides with the `out=` angle key ("key '/tikz/out' requires a value", fatal): never
  name styles out/in/left/right; use `res`.
- (ch 9) Two stacked axes in separate tikzpictures misalign when their tick labels differ in width, even with
  `scale only axis`: put both in one tikzpicture, the second `at={(top.south west)},anchor=north west`.
- (ch 9) A plotted rolling mark-out left its axis at ymax 2.2 while the series reached 2.83: read the CSV's min/max
  before fixing an axis range.

- (ch 5) Tests that import a firm module directly need its sys.path entry in the test itself: ruff sorts
  `from firm_x import` above `from rs_y import`, and rs_y is what added the path.

- (ch 4) A ticker-join momentum test showed nothing: the market had no momentum and freed tickers were reused only
  after 12 months, so no 12-month window straddled two holders. Check that a planned demonstration can show the
  effect before writing it into a brief; keep only effects that are stable across seeds (here: spliced-return counts
  and the adjusted-floor leak, checked on four seeds).
- (ch 4) Printed ratios from rounded prices: 39.55/4.23 - 1 = 835%, the unrounded ratio also rounds to 835 — but the
  first draft said 836. Test the printed arithmetic on the printed inputs.

- (ch 3) figcrop's caption search matched a *reference* ("drawn in Figure 3.3.") on an earlier page:
  search with the caption's first words ("Figure 3.3. The US payroll").
- (ch 3) Code in `\texttt{}` with string literals trips the straight-quote gate: describe the call in prose.
- (ch 3) Rounding: 3.849 prints 3.8, not 3.9 — take every printed value from the test's rounding.

- (ch 2) Tick-imbalance bars with balanced flow: the threshold E[T]|2P-1| collapses to ~0 and every
  trade closes a bar (50,460 one-trade bars); floor at sqrt(E[T]). With autocorrelated signs the bars
  then shrink through the day (142 -> 16 trades): a result, kept as exercise 7.
- (ch 2) Without a random activity level the simulator's time bars were barely heavier-tailed than
  volume bars (3.30 vs 3.27): volatility must co-move with volume (OU activity multiplying every rate).
- (ch 2) `np.arange(t0, t1 + 1e-12, w)` dropped the last edge (23400 + 1e-12 == 23400): build edges
  from an integer count.
- (ch 2) A thin red line looked black in the 110-dpi figcrop render; at 300 dpi it is red
  (`pdftoppm -r 300 -x -y -W -H` crop). Check colour doubts at 300 dpi before editing.
- (ch 2) A futures month cut off before the 25th in the data (April 2024) got a false expiry: require the
  month's data to reach past the 25th.

- (ch 1) A drafted sentence gave 9.4% for the best of 1,000 five-year
  backtests reaching SR 2; the formula gives 0.39%. Every number in the prose
  goes into `test_solutions.py`, including those not in the solutions.
