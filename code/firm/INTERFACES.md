# Running-project interfaces fixed across books

Frozen at the Books 3–6 batch sync (2026-09-24) by the main session. A book
that **implements** an interface below may add to it; it may not rename or
remove anything. A book that **consumes** one codes against it as written.

Cross-component imports follow the existing convention: a component that
depends on another inserts `code/firm/<other>` on `sys.path` (as every
`tests/test_firm_*.py` already does for its own component) and imports
`firm_<other>`. Earlier components (`curve`, `normalvol`, `parity`, `fxsmile`,
`cds`, …) are wrapped by adapters, never edited.

## 1. `firm_pricing`: the pricing library (implemented by Book 5 ch. 28, consumed by Book 6 ch. 29)

Location: `code/firm/pricing/firm_pricing.py` (Python, numpy only). The core
types and the analytic and finite-difference engines also get a C++20 twin
(`cpp/pricing.hpp`) and a Rust twin (`rust/`), which the Python library does
not depend on.

### Market data

```python
class DiscountCurve(Protocol):           # Book 2's firm_curve.Curve already conforms
    def df(self, d: date) -> float: ...
class BumpableCurve(DiscountCurve, Protocol):
    def bumped(self, pillar: str | None, size: float) -> "BumpableCurve": ...   # None = parallel; size in rate units (1e-4 = 1 bp)
class VolSurface(Protocol):
    def implied_vol(self, strike: float, expiry: date) -> float: ...
    def total_variance(self, k: float, t: float) -> float: ...

@dataclass(frozen=True)
class Dividends: cash: tuple[tuple[date, float], ...] = (); proportional: tuple[tuple[date, float], ...] = (); borrow: float = 0.0

@dataclass(frozen=True)
class RiskFactor: id: str; kind: str; unit: str; shift: Literal["abs", "rel"]

@dataclass(frozen=True)
class MarketData:
    asof: date
    spots: Mapping[str, float]
    curves: Mapping[str, DiscountCurve]                  # keyed by curve name, e.g. "USD-SOFR"
    dividends: Mapping[str, Dividends]
    vols: Mapping[str, VolSurface]
    correlations: Mapping[frozenset[str], float]
    fixings: Mapping[str, Mapping[date, float]]
    fx: Mapping[str, float]                              # "EURUSD" -> USD per EUR (Book 2 convention)
    def t(self, d: date) -> float: ...                   # ACT/365F from asof
    def df(self, curve: str, d: date) -> float: ...
    def forward(self, underlying: str, d: date) -> float: ...
    def fx_rate(self, ccy_from: str, ccy_to: str) -> float: ...
    def risk_factors(self) -> tuple[RiskFactor, ...]: ...
    def apply(self, *bumps: "Bump") -> "MarketData": ...  # new snapshot, never mutates
    def rolled(self, new_asof: date) -> "MarketData": ...  # time roll: spots, curves, surfaces held (sticky strike)
```

**Risk-factor ids** (stable strings, the key shared by bumps, Greeks and Book
6's risk engine):

| id | kind | unit | shift |
|---|---|---|---|
| `SPOT:<und>` | spot | price | rel |
| `VOL:<und>` (parallel) / `VOL:<und>:<expiry ISO>:<strike>` | vol | vol (0.01 = 1 point) | abs |
| `CURVE:<name>` (parallel) / `CURVE:<name>:<pillar>` | rate | rate (1e-4 = 1 bp) | abs |
| `DIV:<und>`, `BORROW:<und>` | dividend yield / borrow | rate | abs |
| `CORR:<a>|<b>` (names sorted) | correlation | — | abs |
| `FX:<PAIR>` | fx | price | rel |
| `CREDIT:<name>` / `CREDIT:<name>:<tenor>` | credit spread | rate | abs |
| `TIME` | valuation date | days | abs |

A book may add kinds (Book 6: inflation, basis, SABR parameters); it registers
them by giving its market objects a `bumped` method for them.

### Instruments, models, engines

```python
@dataclass(frozen=True)
class Instrument:
    id: str; underlying: str; currency: str; notional: float; discount_curve: str
    def to_dict(self) -> dict: ...
def instrument_from_dict(d: dict) -> Instrument: ...     # JSON round-trip, all subclasses

# Book 5 subclasses: EuropeanOption(strike, expiry, right: "C"|"P", exercise: "european"|"american"|"bermudan", exercise_dates=()),
# DigitalOption, BarrierOption(strike, expiry, right, barrier, kind: "DO"|"UO"|"DI"|"UI", rebate=0.0,
# monitoring: "continuous"|"daily"), AsianOption, ForwardStart, Cliquet, VarianceSwap(strike_vol, expiry,
# vega_notional, obs_dates), BasketOption, WorstOf, Autocallable(term_sheet), TARF, ConvertibleBond.

class Model(Protocol):
    name: str
    def params(self) -> Mapping[str, float]: ...
    def calibrate(self, md: MarketData, underlying: str) -> "Model": ...   # returns a copy

class Engine(Protocol):
    name: str
    def supports(self, inst: Instrument, model: Model) -> bool: ...
    def price(self, inst: Instrument, model: Model, md: MarketData) -> float: ...   # PV in inst.currency
    # optional: def greeks(self, inst, model, md, which) -> dict[str, float]  (analytic / AAD override)

def register(inst_type: type, model_type: type, engine: Engine) -> None: ...   # Book 6 registers its rates instruments here
```

### Top-level calls

```python
@dataclass(frozen=True)
class Bump: factor: str; size: float; relative: bool = False      # factor = a risk-factor id
@dataclass(frozen=True)
class Scenario: name: str; bumps: tuple[Bump, ...]
Position = tuple[Instrument, float]                               # (instrument, quantity)

def price(inst, md, model=None, engine=None) -> PriceResult: ...  # PriceResult(pv, currency, model, engine, diagnostics)
def greeks(inst, md, model=None, engine=None, which=("delta", "gamma", "vega", "theta", "rho"),
           bumps=GreekBumps(spot_rel=0.01, vol_abs=0.01, rate_abs=1e-4, theta_days=1),
           recalibrate=False) -> dict[str, float]: ...
    # units: delta in underlying units; gamma = cash gamma per 1 % move; vega per vol point; rho per bp; theta per day
def sensitivities(inst, md, factors: Sequence[str], model=None, engine=None) -> dict[str, float]: ...
    # PV change per unit shift of each risk factor, keyed by factor id (engine override if it has one, else bump-and-reprice)
def bucketed_vega(inst, md, expiries, strikes, model=None, engine=None) -> dict[tuple[date, float], float]: ...
def reprice(book: Sequence[Position], md, scenarios: Sequence[Scenario],
            model_for=None, engine_for=None) -> dict[str, float]: ...   # scenario name -> PV change of the book
def price_batch(book: Sequence[Position], snapshots: Sequence[MarketData],
                model_for=None, engine_for=None) -> BatchResult: ...
    # BatchResult.pv: np.ndarray[len(snapshots), len(book)] in each instrument's currency (NaN on failure);
    # BatchResult.errors: dict[(i, j), str] -- one failing trade never kills the batch
class PricingError(ValueError): ...
```

**Binding rules**

1. **Pure and deterministic.** `price` has no side effects and no global mutable
   state other than the registry filled at import. Safe to call from threads.
2. **Common random numbers.** Every Monte Carlo reprice of one instrument uses
   the same seed, derived as `zlib.crc32(inst.id.encode())` (never Python's
   salted `hash()`), and the same grid, so bumps and scenarios difference on
   common random numbers.
3. **Snapshots are immutable.** `apply` and `rolled` return new objects.
4. **JSON.** `Instrument.to_dict`/`instrument_from_dict`, `Scenario`, `Bump`
   and the plain fields of `MarketData` (spots, dividends, correlations, fx,
   fixings, asof) serialise to JSON; curve and surface objects serialise
   through their own `to_dict` where they provide one.
5. Trade metadata (trade id, book path, counterparty, netting set) is **not**
   part of `Instrument`: Book 6 wraps positions in its own `Trade` type.

### Book 6's side

Book 6 ch. 29 (`firm_riskengine`, Python with a C++20 and Rust aggregation
kernel) builds `Scenario`s from its scenario generators, calls `price_batch`,
`reprice` and `sensitivities`, and aggregates by its own `Trade` hierarchy. It
registers its rates instruments and engines (swaps, swaptions, caps; built on
its `curvebuild` / `multicurve` / `capfloor` components) with `register`.
**Book 6 writes ch. 29 last.** If `code/firm/pricing/` is not present or not
green at that time, Book 6 writes `code/firm/riskengine/pricing_stub.py`
conforming to this section, says so in its report, and the main session wires
the real library in afterwards.

## 2. Reuse between parallel books (optional, not binding)

Books 4 and 5 are written at the same time, so no component of one may
**require** a component of the other, except §1. Later integration
candidates, noted for the reconciliation: Book 5 `mcpricer` → Book 4
`mcengine`; `fdpricer` → `pde`; `calib` → `optim`; Greeks → `aad`; Book 6
`varmodel` → Book 4 `volfcst`, `robust`; `riskengine` → `aad`, `covest`.

## 3. Components reserved at the sync (all new, all unique)

- **Book 3** (`markets-3`): physdeal crude cracks lngarb dayahead balancing carbon prompts cot commcurve degreeday hedgeprog nominate gasfee ratelimit triarb perp liquidation cryptoopt amm blockbook sandwich lendpool tokenloan mmprogram wsbook odds marginspiral marketmap
- **Book 4** (`methods`): mgtest mcengine stochint numeraire levy hawkes queues dpsolve impulse estim multitest resample bayes robust linreg tsa volfcst kalman coint hfvol covest portopt optim fpkit pde aad bidding
- **Book 5** (`derivatives`): arbcheck binomial bs greeks divfwd american volsurface svi localvol heston sabr fwdvar jumps varswap barrier pathdep multiasset autocall termsheet fxvol convertible fdpricer mcpricer calib volpnl optmm reserves pricing
- **Book 6** (`rates-credit-risk`): curvebuild multicurve ratesrisk capfloor sabrcube cms shortrate lmm bermudan rfrcaplet inflopt mbsoas cdscurve structural portcredit energymodel exposure cva xvafund xvaquote varmodel stresstest frtb alm initmargin modelval pnlexplain tradecontrol riskengine
- **Book 7** (`research`, reserved 2026-09-24, Phase A): researchlog tape bars pit secmaster synthmkt predictor features lobfeat tradeflow leadlag fundpit vendoreval decay combine forecast vecbt evbt lobreplay simlive overfit abtest perf markout riskmodel portcons allocation tcost capacity workflow

## 4. The research core (implemented by Book 7, consumed by Books 8 and 9)

Books 7, 8 and 9 are written in sequence (user ruling, 2026-09-24), so this
section is written by Book 7 as each component lands and is frozen when Book 7
is delivered. Books 8 and 9 code their strategy tutorials against it.

Planned contracts (Book 7 fills in the signatures):

- `firm_synthmkt` (ch. 5, **landed**): `simulate(MarketConfig(n, days, seed, ...)) -> Panel`.
  Panel arrays are days x listings (column = permanent id), NaN where not
  listed: `ret` (daily total return, delisting return on the delisting day),
  `price`, `volume`, `shares`, `listed`; per listing `start`, `end`,
  `industry`, `beta`, `style_x` (size, value, momentum), `spec_vol`; factor
  paths `mkt`, `h` (market conditional variance), `ind`, `style`; `alpha`
  {momentum, value, pead, reversal}: expected return of day t+1 stored at day
  t (the truth to score signals against); `delist`, `splits`, `dividends`,
  `earnings` (true surprises), `fundamentals` (book and eps with filing and
  restatement days) and `fundamentals_store()` (a `firm_pit.Store`),
  `secmaster`. Defaults (seed 1): 1,000 names listed every day, 2,520 days,
  market 6.3%/16.4% a year, daily kurtosis 20.5; reversal IC 0.034 (1 day),
  12-1 momentum IC 0.030 (21 days); performance delistings 1.5% a year.
- `firm_tape` (ch. 2, **landed**): `simulate(TapeConfig(...)) -> Tape` with
  structured arrays `msgs` (t, kind A/X/E, oid, side, price ticks, qty, agg,
  trade), `trades` (t, price, qty, sign, informed, trade), `top` after every
  message, efficient price `v_t`, `v`, activity `act`, `n_open` snapshot
  rows; `simulate_pair(cfg, latency)`; `Book().apply(msg)`. One 6.5-hour day
  with defaults and u_shape=1.5: about 1.5 million messages in ~10 s.
  `firm_bars` (ch. 2): time/tick/volume/dollar/imbalance bars, `asof`,
  `continuous` futures. `firm_pit` (ch. 3): bitemporal `Store`, `Guard`,
  `asof_join`. `firm_secmaster` (ch. 4): `SecurityMaster`,
  `buffered_universe`, `churn`.
- `firm_predictor` (ch. 6, **landed**): `PredictorCard`, `forward_return`,
  `excess`, `residualise`/`neutralise`, `zscore`, `rank_transform`,
  `ic_series`, `ic_summary` (HAC t with h-1 lags), `quantile_spread`.
  `firm_features` (ch. 7): return, volatility and range estimators, volume,
  Amihud, turnover, crossover, `leakage_test`. `firm_lobfeat` (ch. 8):
  streaming `Engine(levels, g).on(kind, oid, side, price, qty) -> Features`
  (imbalances, OFI, weighted mid, microprice), Python + C++20 + Rust on one
  fixture. `firm_tradeflow` (ch. 9): `tick_rule`, `quote_rule`, `lee_ready`,
  `bvc`, `sign_acf`, `hurst_aggvar`, `vpin`, `kyle_lambda`,
  `markout_toxicity`, `aggregate_orders`. `TapeConfig.news_noise` (ch. 9,
  default 3.0) scales noise flow during the news window; 1.0 makes the
  episode toxic (informed share 15% -> 45%). Known property: with
  `v_rate=1.0` the tape's mids trend over a few seconds (lag-1 correlation
  of 2-second mid returns 0.44), so short-horizon studies must control for
  the target's own past. `firm_leadlag` (ch. 10): `hy_ccf`,
  `lead_estimate`, `lead_symmetric`, `lead_lag_ratio`, `directional_corr`,
  `peer_relative` (leave-one-out), `linked_feature`, `lagged_corr_matrix`,
  `top_pairs`. `MarketConfig.link_share/link_beta/link_days` (ch. 10,
  default off, own RNG so default panels are unchanged): suppliers get
  link_beta of their customer's specific shocks spread over link_days;
  `Panel.customer`, `alpha["link"]`. `firm_fundpit` (ch. 11):
  `duration_kind`, `load(facts, field)` into a `firm_pit.Store` (field
  `eps_Q`/`_H`/`_9M`/`_FY`, valid = period end, known = filing),
  `quarterly(store, entity, field, known)`, `ttm`, `sue`, `restated`,
  `split_ratio`, `revision`, `dispersion`, `days_to_event`, `in_window`.
  Real EDGAR extracts for ten companies: `data/research/edgar_*.csv`.
  `firm_vendoreval` (ch. 12): `coverage`, `backfill_share`, `fit_by_group`,
  `cusum_break`, `rank_ic`, `ic_by_group`, `residualise(f, X, group)`,
  `incremental_ic`, `long_short(f, y, group, q)`, `breakeven(annual,
  capital, cost, half_life, years)`, `tone`. `firm_decay` (ch. 13):
  `ic_decay`, `half_life_fit`, `rank_autocorr`, `half_life_ar`, `turnover`,
  `block_bootstrap`, `cusum`, `sup_f`, `sup_f_critical`, `sup_f_pvalue`,
  `decline_power`. `MarketConfig.pead_break/pead_after` (ch. 13, default
  off): the post-earnings drift multiplied by pead_after from that day.
  `firm_combine` (ch. 14): signals as X (T, N, K), target y (T, N);
  `zscore`, `ic_series`, `ic_matrix`, `equal`, `blend(X, w)`, `ic_weights`,
  `max_icir(ic, shrink)`, `toward_equal(w, lam)`, `ridge`, `lasso`, `nnls`,
  `stack(preds, y, folds)`, `time_folds`, `orth_sequential`,
  `orth_symmetric`, `residualise_on`. `firm_forecast` (ch. 15):
  `scale_rule(z, ic, vol)`, `binned`, `isotonic`, `mincer_zarnowitz`,
  `effective_breadth`, `transfer_coefficient(w, alpha, vol)`,
  `law_ir(ic, breadth, tc)`, `qian_hua_ir`, `ding_martin_ir`,
  `information_ratio(pnl, periods)`.
- `BacktestResult` (ch. 16, **landed** in `firm_vecbt`, shared by `firm_evbt`
  and `firm_lobreplay`): `dates`, `names`, `weights (T, N)` held over each
  period as a fraction of capital, `trades (T, N)` from the drifted book,
  `gross (T,)`, `costs {'trading', 'borrow', 'financing'}: (T,)`, `net (T,)`,
  `capital (T,)`, `meta {lag, compound, periods, ...}`; properties
  `turnover`, `gross_exposure`, `net_exposure`. `firm_vecbt.backtest(weights,
  returns, lag, universe, cost, borrow, cash_rate, borrow_spread, cap,
  compound, periods)`, `signal_to_weights(signal, universe, gross, neutral)`.
  `firm_perf` (ch. 22) reads only this type. `firm_evbt` (ch. 17, **landed**):
  one instrument on bars; `Engine(bars, strategy, fill_model, latency, fee,
  capital, splits, policy).run() -> (BacktestResult, orders, fills)`;
  `Strategy.on_bar(ctx, i, bar)`, `on_fill(ctx, fill)`; ctx `submit(side,
  qty, kind, price)`, `cancel(oid)`, `position`, `cash`, `working()`, `now`;
  fill models `TouchFill`, `PenetrationFill(ticks)`, `VolumeCapFill(inner,
  participation)`; policy 'conservative' or 'optimistic'. `firm_lobreplay`
  (ch. 18, **landed**): `Replay(msgs, strategy, model, entry_latency,
  data_latency).run() -> ReplayResult` (shadows, fills (t, vid, side, qty,
  price), position, cash, mid path, `pnl()`); `Strategy.on_market(ctx, t,
  snapshot)`, `on_fill`; ctx `send(side, price, qty)`, `cancel(vid)`,
  `working()`, `position`, `shadows`; models 'front', 'fifo', 'prob';
  `track_fifo(msgs, orders)` with C++20 (`cpp/firm_lobreplay.hpp`) and Rust
  twins checked on `data/fixture_*.csv`. Book 10's exchange simulator plugs
  in here as a reactive replacement for the shadow-order replay.
  `firm_tape.simulate(cfg, v_path=None, agent=None)` (ch. 19): an agent
  trades inside the simulated market (delay_data(), delay_entry(),
  on_market(t, top), on_fill(t, cid, side, price, qty, passive) returning
  ('limit', cid, side, price, qty) / ('cancel', cid) / ('market', cid,
  side, qty)); `Tape.own`, `Tape.agent_fills`. `firm_simlive` (ch. 19):
  `match_fills`, `parity`, `fill_pnl`, `waterfall`, `calibrate`,
  `implementation_shortfall`.
  `firm_overfit` (ch. 20, **landed**): `cscv(M, n_blocks, max_splits,
  seed) -> {pbo, logits, is_best, oos_of_best, slope}`, `purged_kfold(start,
  end, k, embargo)` (label spans), `cpcv`, `cpcv_paths(n, k)`,
  `walk_forward(n, train, test, step, anchored)`,
  `min_backtest_length(n_trials, sr_target)`.
  `firm_abtest` (ch. 21, **landed**): `bucket(unit, experiment, salt)`,
  `assign(units, experiment, share, salt)`, `diff_means(y, t)`,
  `cuped(y, X, t) -> (d, se, theta)`, `stratified(y, t, strata)`,
  `cluster_diff(y, t, cluster)`, `demean_by(v, group)`, `power`, `mde`,
  `sample_size`, `srm_pvalue`, `msprt(d, se, tau)`, `always_valid_p`.
  `firm_perf` (ch. 22, **landed**): reads `BacktestResult.net` (or any
  return array); `from_returns(r, periods)`, `sharpe` (firm.estim),
  `lo_sharpe(r, q, lags)`, `drawdown`, `max_drawdown`, `drawdown_spells`,
  `longest_drawdown`, `calmar`, `sortino(r, periods, mar)`, `omega`,
  `hit_rate`, `profit_factor`, `holding_period(res)`, `alpha_beta(r, bench,
  periods, lags)` (firm.linreg HAC), `smoothing_profile`, `unsmooth`,
  `tear_sheet(res, bench, name, periods) -> (dict, text)`.
  `firm_markout` (ch. 23, **landed**): `microprice`, `ref_at(ref_t, ref_px,
  t)`, `markouts(t, side, px, ref_t, ref_px, horizons)`, `curve(M, qty,
  groups) -> {g: (mean, se)}`, `settle_horizon`, `fill_rate`, `hit_ratio`,
  `mm_decompose(t, side, px, qty, ref_t, ref_px, H, fee, t_end)` (exact),
  `shortfall(side, target, decision_px, arrival_px, fills, end_px, fee)`,
  `vwap_slippage`, `tca_report`.
  `firm_riskmodel` (ch. 24, **landed**): `cs_regression(r, X, w, C)`,
  `factor_returns(R, exposures, W, C)`, `ewma_cov(F, half_life, nw_lags)`,
  `vra(F, covs, half_life)`, `specific_var(E, half_life, groups, shrink)`,
  `portfolio_risk(w, X, Fcov, spec) -> {total, factor, specific, contrib,
  exposure}`, `pca_model(R, k)`, `bias_stat`, `bias_band`. The chapter's
  synthmkt model (15 factors) is `rs_riskmodel.fundamental()` with
  `exposures(t)`; Books 8-9 may reuse it through that module or rebuild it.
  `firm_synthmkt.point_in_time_styles(P)` (added ch. 24): size, log
  book-to-price and momentum as known point in time; `Panel.style_x` holds
  the last day's exposures only.
  `firm_portcons` (ch. 25, **landed**): `Problem(alpha, X, F, spec, gamma,
  w0)` with `.equality`, `.neutral_factors`, `.bounds`, `.liquidity(adv,
  participation, capital)`, `.gross`, `.turnover`, `.turnover_penalty`;
  `.solve() -> {w, objective, alpha, risk, ir, gross, turnover, duals,
  binding, pull, status}`; `.ir_decomposition(result)`; `ir_ex_ante`;
  `trade_list`. Dense QP: fine to a few hundred names.
  `firm_allocation` (ch. 26, **landed**): `mean_variance(alpha, Sigma, gamma,
  lo, hi, budget)`, `robust_mv(..., Omega, kappa, ...)`, `implied_returns`,
  `black_litterman(pi, Sigma, P, q, Omega, tau)`, `risk_contributions`,
  `risk_budget(Sigma, b)`, `erc`, `hrp`, `gp_trade_rate(gamma, lam, rho)`,
  `gp_aim(Sigma, signals, phis, gamma, a)`.
  `firm_tcost` (ch. 27, **landed**): `impact_bp`, `fit_impact(cost, sigma,
  participation, half_spread)`, `trade_cost(dw, aum, sigma, adv, half_spread,
  eta, fee)`, `prox_cost`, `cost_aware(alpha, Sigma, w0, aum, sigma, adv,
  half_spread, eta, gamma, neutral)`, `net_trades`, `netting_saving`,
  `smooth(signal, half_life)`, `breakeven_cost`.
  `firm_capacity` (ch. 28, **landed**): `capacity_curve(sizes, net_returns,
  vols)`, `profit_maximising`, `size_at_fraction(curve, frac, key)`,
  `avg_pairwise_corr`, `comomentum`, `overlap`, `unwind(books, capitals,
  seller, fraction, days, adv, sigma, eta, permanent, half_life, horizon)`.
  `firm_workflow` (ch. 29, **landed**): `content_hash`, `Stage(name, fn, deps,
  params, seed)`, `Pipeline(stages, cache_dir).run(target) -> (outputs,
  manifest)`, `environment`, `reproduce`, `diff`, `register`.

## 5. Book 8's strategy components (reserved 2026-09-25, all new and unique; all **landed** 2026-09-25)

statbook (ch1), reversal (ch2), residarb (ch3), pairsel (ch4), momstrat (ch5), factorlib (ch6), earnstrat (ch7),
lendsig (ch8), flowpress (ch9), indexevent (ch10), mergerarb (ch11), structrv (ch12), intraday (ch13), intraml (ch14),
optsignal (ch15), altstrat (ch16), newsevent (ch17), limitmkt (ch18), synthfut and trendfollow (ch19), carrystrat
(ch20), curvestrat (ch21), xasset (ch22), seasonal (ch23), posisig (ch24), futintraday (ch25), voltarget (ch26),
cryptomf (ch27), multistrat (ch28), assetmgr (ch29). They run on section 4's research core; `synthfut` (the synthetic
futures universe) is what Book 9's macro and relative-value chapters reuse.

For Book 9 the reusable ones are:
  `firm_synthfut` (ch. 19): `FutConfig(years, per_class, seed, vol, within, trend_sr, trend_half_life, carry_sd,
  carry_half_life, carry_premium, vol_persist, vol_sd, t_df, crashes, crash_days, crash_move, carry_crash, crash_vol,
  seasonal, season_amp)`, `simulate_futures(cfg) -> {names, cls, r, carry, drift, vol, x, amp, phase, crashes}`,
  `season`, `curve(F, t, taus)`, `contracts(F, t, n, every)`; four classes (`CLASSES`), 30 years of 252 days.
  `firm_trendfollow` (ch. 19): `ewma_vol`, `tsmom`, `ma_cross`, `breakout`, `positions`, `run`, `vol_target`.
  `firm_carrystrat` (ch. 20): `curve_carry`, `forward_discount`, `dividend_carry`, `rank_weights(x, groups)`, `book`,
  `scale`, `windows`, `skew_monthly`.
  `firm_curvestrat` (ch. 21): `serials(expiry)`, `pair_pnl(C, m, near, days_before, expiry)` (spreads by contract
  identity through expiries), `zscore`, `positions`, `band`, `spread_carry`.
  `firm_voltarget` (ch. 26): `realised_var`, `ewma_var`, `weights`, `banded`, `run`, `spike_flows`.
  `firm_multistrat` (ch. 28): `PodConfig`, `simulate_pods`, `allocate`, `run_firm`, `stop_rate`, `netting`.

## 6. Book 9's strategy components (reserved 2026-09-25, all new and unique; all **landed** 2026-09-25)

synthvol and shortvol (ch1), dispersion (ch2), volrv (ch3), eventvol (ch4), vixetp (ch5), gammaflow (ch6), tailhedge
(ch7), convarb (ch8), capstruct (ch9), bondrv (ch10), basistrade (ch11), swapspread (ch12), supplytrade (ch13), fxcarry
(ch14), fxflows (ch15), sysmacro (ch16), macrobook (ch17), creditrv (ch18), syscredit (ch19), mbsrv (ch20), commspread
(ch21), physopt (ch22), powergas (ch23), flowmm (ch24), crbook (ch25), deltaone (ch26), qis (ch27), sphedge (ch28),
surveil (ch29). Each module's docstring holds its stable API; the reusable ones and their dependencies:

  `firm_synthvol` (ch. 1): `VolConfig`, `simulate_vol(cfg) -> {r, v, R, spec, crashes}` (an index with stochastic
  variance, crashes and 30 members), `expected_var`, `atm_iv`, `smile_iv`, `bs_price`, `bs_delta`; the volatility
  market that chapters 2-7 trade.
  `firm_shortvol` (ch. 1): `short_variance`, `hedged_straddle`, `overwrite`, `put_write`, `lever`.
  `firm_dispersion` (ch. 2): `average_corr`, `realised_var`, `dispersion_pnl`, `corr_swap_pnl`.
  `firm_volrv` (ch. 3): `SurfaceConfig`, `surface_path`, `features`, `trade_pnl`, `attribution`.
  `firm_eventvol` (ch. 4): `event_variance`, `implied_move`, `windows`, `straddle_pnl`.
  `firm_vixetp` (ch. 5): `vix_index`, `future`, `curve_path`, `etp`, `flow`.
  `firm_gammaflow` (ch. 6): `dealer_gamma`, `simulate_days`, `flip_level`.
  `firm_tailhedge` (ch. 7): `put_vol`, `put_programme`, `static_mix`, `trend_overlay`, `evaluate`.
  `firm_convarb` (ch. 8, on Book 5's `firm_convertible`): `value_tables`, `mark`, `delta`, `scenario`, `run_book`.
  `firm_capstruct` (ch. 9): `implied_spread` (first passage), `hedge_ratio`, `simulate_firms`, `trades`.
  `firm_bondrv` (ch. 10): `loadings` (Nelson-Siegel), `simulate_market`, `fit_residuals`, `neutralise`, `book`.
  `firm_basistrade` (ch. 11): `simulate_basis`, `run_book(sim, cfg, leverage)` with haircuts and forced sales.
  `firm_swapspread` (ch. 12), `firm_supplytrade` (ch. 13), `firm_fxcarry` (ch. 14), `firm_fxflows` (ch. 15).
  `firm_sysmacro` (ch. 16): `macro_market`, `signal`, `portfolio`, `combine` (equal-risk).
  `firm_macrobook` (ch. 17): `rate_paths`, `bachelier_receiver`, `expressions`, `stopped_correct`.
  `firm_creditrv` (ch. 18): `simulate_credit`, `negative_basis`, `index_arbitrage`, `curve_trade`.
  `firm_syscredit` (ch. 19): `simulate_bonds` (stale prices, NAV, ETF price), `factor_book`, `ap_arbitrage`.
  `firm_mbsrv` (ch. 20, on Book 6's `firm_mbsoas` and Book 2's `firm_tranche`): `FlatCurve`, `strip_paths`,
  `io_trade(cfg, market, truth, side, shifts)`, `coupon_stack`, `tranche_rv`.
  `firm_commspread` (ch. 21): `crack_321`, `spark`, `board_crush`, `simulate_spreads`, `fade(x, cfg, month, delay)`,
  `seasonal`.
  `firm_physopt` (ch. 22, on Book 6's `firm_energymodel`): `plans(fac, prices, inv)` (vectorised full-plan dynamic
  programme), `hedge_programme(fac, model, F0, T, paths, seed, cost, roll, gate)` (static and rolling intrinsic path
  by path), `spread_option_pairs`, `transport`, `diversion`.
  `firm_powergas` (ch. 23): `intraday(da, cfg)`, `forecast_trade`, `battery(prices, cfg, committed)`.
  `firm_flowmm` (ch. 24): `simulate_flow` (mid path common to all policies), `run_desk(flow, cfg, half_spread, skew,
  start, end)`, `client_markouts`, `client_hits`, `price_clients`.
  `firm_crbook` (ch. 25, on Book 7's `firm_tcost`): `simulate_desks`, `hedge_cost`, `desk_by_desk`, `pooled`,
  `central(sim, cfg, rate, futures)`.
  `firm_deltaone` (ch. 26, on Book 5's `firm_autocall`): `simulate_financing`, `index_arb(sim, cfg, lag)`,
  `financing_trade(sim, cfg, offset)`, `issuer_dividend_exposure`, `dividend_market`.
  `firm_qis` (ch. 27, on Book 4's `firm_multitest`): `simulate_teams` (Sharpe estimates with correlated 1/sqrt(T)
  errors), `launch(sim, cfg, k)`, `deflated`, `example_path`.
  `firm_sphedge` (ch. 28, on Book 5's `firm_autocall`): `Note`, `BOOK`, `MarketState`, `note_value(note, mkt, paths,
  seed, spot)` (monthly paths), `book_exposures`, `spot_profile`, `recycling_impact`.
  `firm_surveil` (ch. 29): `spoofing_days`, `close_days`, `wash_days`, their `*_scores`, `tpr_at_fpr(score, label,
  fpr)`, `flagged_by_type`. Account-day features only; no manipulation's profit is modelled.

## 7. The exchange simulator `firm_exchsim` (frozen at the Books 10–13 sync, 2026-09-25)

Implemented by **Book 10 ch. 26** (`code/firm/exchsim/`), consumed by Books 11 (every market-making
tutorial), 12 (ch. 16, 18, 29) and 13 (ch. 16–26). Book 10 implements it **first** in Phase B, before its
chapter 1 prose, in this order: `lob`, `ordertypes`, `auctionsim`, `halts`, then `exchsim` (Python
reference), then `PROTOCOL.md` + `schema.json` + golden fixtures, then the C++20 engine and localhost
server, then the Rust engine and codecs. Book 10 records what has landed, with the date, in
`code/firm/exchsim/STATUS.md` (Book 10 writes it; consumers read it before each chapter that needs the
simulator). Until a piece lands, consumers use Book 7's `firm_tape` agent API or `firm_lobreplay`, through
an adapter, never a private simulator. Book 10 may **add** to this contract; renaming or removing
anything needs the main session.

**Reuse, not duplication.** Allocation calls Book 1's `firm_match` (FIFO, pro-rata, top-order, LMM);
the uncross uses Book 1's `firm_auction`; the consolidated feed uses `firm_nbbo`; tiers use
`firm_feesched`; LULD monitors come from `firm_replay`. Book 7's `firm_tape` supplies background flow
(`TapeBackground`) and `res.tape()` exports its `msgs/trades/top` arrays so `firm_lobreplay`,
`firm_lobfeat`, `firm_tradeflow` and `firm_markout` run unchanged; `ReplayStrategyAdapter` runs one
Strategy on replay and on the simulator with a parity test; `TapeAgentAdapter` runs Book 7 agents.

**(a) In-process Python API** (names binding; defaults are Book 10's):
`ExchangeConfig(venue, instruments=(InstrumentSpec(symbol, locate, tick, lot, start_price,
matching='fifo'|'pro_rata'|'configurable', alloc, band),), fees=FeeSchedule(make, take, tiers),
phases=Phases(...), halts, throttle=Throttle(rate, burst), engine_ns, speed_bump_ns=0,
asymmetric_delay=False, batch_interval_ns=0 (frequent batch auction when > 0), feed=FeedConfig(lines=('A','B'),
loss, burst_loss (Gilbert–Elliott), dup, reorder_window, jitter, outages, snapshot_every_ns), faults=(), seed)`;
`Simulator(venues, inter_venue_ns, sip, seed)`; `add_background(...)`; `add_agent(agent,
SessionSpec(firm, venue, latency=LatencyModel(entry_ns, ack_ns, data_ns, jitter, spikes), cod, stp_group,
drop_copy=False))`; `add_events(...)` for scheduled exogenous jumps of the efficient price and for
scripted orders; `schedule_call(t_ns, fn, *args)` (added ch. 25: a venue-side process called among the controls;
`firm.halts` policies `LULD(pct, window_s, limit_state_s, pause_s, check_s, locate, shadow, update_pct)`,
`MarketWide(levels, halt_s, check_s, reference)`, `Velocity(ticks, window_s, pause_s, check_s)`, `Combined(...)` are
passed as `ExchangeConfig(halts=...)` and act only through controls R and P; client order ids are numbered per
session, so a multi-venue agent sets `Order.cl_ord_id` itself); `res = sim.run(until_ns)` with `res.feed_bytes(venue, line)`, `res.tape(venue, locate)`,
`res.reports(firm)`, `res.journal` (every inbound message with its engine-arrival ns), `res.truth`
(efficient price path, aggressor class and informed flag per trade: evaluation only, never in the feed).
Agent protocol: `on_start`, `on_feed(ctx, msg)`, `on_book(ctx, locate, top)`, `on_report(ctx, rep)`,
`on_timer(ctx, tag)`; `ctx`: `now_ns`, `send(Order) -> cl_ord_id`, `replace`, `cancel`, `mass_cancel`,
`quote` (two-sided mass quote), `set_timer`, `book(locate)` (built from the agent's own feed), `position`,
`cash`, `working()` (with orders ahead in queue), `compute(ns)` (declared decision time that delays the
next sends: Book 12 ch. 29 charges inference latency with it).
Presets (Book 10 ch. 26–29, added as they land): US-equity lit venue, pro-rata futures (with top order and,
as a stretch, implied-in calendar spreads), midpoint dark pool, speed-bumped venue, periodic batch
auction, opening/closing auctions with indicative-price and imbalance messages and MOC/LOC and cut-offs,
and a crypto profile (24-hour session, fees in bp, request-weight rate limit) before Book 11 ch. 24 needs it.
Performance targets: a 6.5-hour single-instrument day with one agent and default background in tens of
seconds of Python; one simulated minute with light background in well under a second (Book 12's RL).

**(b) Market-data feed** (big-endian throughout, prices in 1/10,000 currency unit, timestamps 48-bit ns
since midnight). Payload messages keep Book 1 `firm_feed`'s A 36 / E 31 / X 23 / D 19 / P 44 byte for
byte (a test decodes an A/E/X/D/P-only stream with `firm_feed`), plus ITCH-5.0-length U replace 35
(new order ref, loses priority), C executed-with-price 36, Q cross 40, I imbalance 50, S system event 12,
H trading action 25, and own layouts R instrument directory (locate, symbol, tick, lot), G/W snapshot
begin/end (W carries the last applied incremental seq and a CRC32). Each message is framed by a u16
length. **Packets are MoldUDP64**: session (10 bytes ASCII) | sequence number of the first message (u64) |
count (u16); count 0 is a heartbeat, 0xFFFF end of session. The feed's order ref is the exchange order
id returned in the Accepted report. Lines A and B carry identical packets with independent seeded
impairments. A snapshot channel publishes each instrument's full MBO book in priority order, tagged with
the incremental seq it reflects; a retransmission service answers (session, seq, count) from a bounded
window with a maximum count and a rate limit; beyond the window a client recovers from the snapshot.
**Recorded files**: per line and for the snapshot channel, records of (u64 send_ns, u32 len, packet bytes);
golden decoded CSVs per message type; a deterministic recorded day of at least one million messages is
*regenerated by a script*, not committed. **`schema.json`** describes every message of both protocols
(fields, types, offsets, enums) and is the single source from which Book 13 ch. 16 generates its client
codecs; a test checks it against the Python codec.

**(c) Order-entry protocol.** Session layer **SoupBinTCP 4.0**-style (`u16 len | u8 type`; login with
username, password, requested session and requested sequence; login accepted / rejected; server and
client heartbeats; logout; end of session; sequenced server messages, unsequenced client messages;
re-login from a sequence number replays missed reports). Application messages OUCH-style, big-endian.
Inbound: O Enter (`cl_ord_id u64`, locate, side, qty, price with 0 = market, tif D/I/F/G/open/close,
display visible/hidden/midpoint peg/primary peg, post_only, display_qty for icebergs, min_qty, stp_group,
stp_mode none/cancel-oldest/cancel-newest/both/decrement, stop_price), U Replace (a size decrease at the
same price keeps priority and is published as a partial X; any other change loses it and is published as
U), X Cancel (with leave-qty), M Mass cancel (all or per instrument), Q Mass quote (two-sided, atomically
replaces the previous). Outbound: A Accepted (with order ref), U Replaced (priority kept or not), C
Canceled (user, IOC remainder, self-trade prevention, disconnect, halt, mass, expired), E Executed (qty,
price, match id, liquidity flag added/removed/cross, fee, leaves), J Rejected (throttle, bad tick, bad
qty, halted, unknown symbol, duplicate id, post-only would cross, price band, too late to cancel), S
system events. Order states on the venue: Live → PartiallyFilled → Filled | Canceled | Expired; Replace
yields a new id; Rejected is terminal; PendingNew/PendingCancel exist only in the client (Book 13's
gateway). The cancel–fill race is real: a cancel arriving after the final fill gets J(too late). Per
session: token-bucket throttle, self-trade prevention per group, cancel on disconnect, and an optional
read-only **drop-copy** session carrying all the firm's executions and cancels.
**Scheduled faults** (for Book 13 ch. 24–25): session drops, login refusals over a window, an engine
pause-and-resume standing in for a failover, halts; plus scripted orders at set times.

**(d) Clock and determinism.** Integer-ns simulated clock; events ordered by `(t_ns, class, seq)`; the
engine charges `engine_ns` per message, so bursts queue. Latency per session and direction: base +
lognormal jitter + optional spikes; TCP stays FIFO, UDP lines may reorder. Randomness is counter-based
(SplitMix64 keyed on seed, session, direction, counter), identical in Python, C++ and Rust, so adding a
participant never changes anyone else's draws (common random numbers with and without an agent, disjoint
seed streams for train/validation/test). Same config, seed and inputs give byte-identical feeds and
reports (tested by SHA-256).

**(e) Transport.** A framed byte-stream abstraction: in-memory pipe (default, simulated time) or real
sockets. Live mode: feed over **UDP multicast on loopback** (tested to work under WSL2) with UDP unicast
on two ports as the fallback; order entry and retransmission over TCP. `python -m firm_exchsim serve`
(slow, reference) and `cpp/bin/exchsim_server --config cfg.json` (C++20, real time; journals its inputs
so any run replays exactly). Book 13 ch. 26 measures only the client's internal path.

**(f) Twins.** C++20: `exchsim_codec.hpp` (allocation-free decode), `exchsim_engine.hpp`,
`exchsim_server.cpp`; Rust crate with `codec` and `engine`. The three engines produce byte-identical feeds
and reports on the shared fixtures. Client-side handler, book builder and gateway belong to Book 13;
Book 10 ships only a minimal test client. `PROTOCOL.md` documents every byte, state and reason code.

**(g) Populations and the firm's algorithm on the simulator** (added Book 10 ch. 27–28). `firm.agentmkt`:
`session(cfg, seconds, seed, agents=(), venue=None) -> (Result, Population)` runs a reacting population as one
Agent with zero latency (`PopulationConfig`: providers, noise takers with Pareto sign runs, fundamentalists on a
hidden value, chartists `chart`/`chart_window` off by default, activity `curve`); other agents join with 20 µs
latency; `MarketMaker(lots, skew, max_lots, refresh_s)`; `facts(tape, sample_s)` (stylised facts of any
firm.tape-format tape), `distance`, `msm`. Chapter 27's calibrated population is `PopulationConfig(lo_rate=3,
near=0.5, cancel=0.02, depth=10, mo_lots=2, fund=0.2, v_rate=0.1, noise=1.2, run_tail=2.5, chart=0.05)` with
`MarketMaker(skew=0.1)`. `firm.execalgo`: `ISAlgo(Params(...), name, venues)` is an ordinary Agent (states new,
working, paused, done, expired, killed; `.log`, `.fills`; `.kill(t_ns)` for `schedule_call`); it pauses on any
trading-action message other than T and resumes on T.

## 8. Books 10–13 components (reserved 2026-09-25 at the sync, all new and unique; all **landed** 2026-09-26)

- **Book 10** (`microstructure`): lob ordertypes lobstats spreadmodels spreaddecomp queuevalue venuefees consolidated darkpool auctionsim impactfit propagator crossimpact acexec execcontrol algos placement sor tca algowheel xexec riskbid otcsearch mktquality halts exchsim agentmkt execalgo
- **Book 11** (`hft`): mmharness mmecon fairprice invmm multimm qreactive toxicity hfalpha xvenue latrace quoteengine mmhedge etfmm basketarb drarb futmm auctionmm rebatemm newsrace optquoter optarb fxlp rfqmm wholesale cryptohft searcher sportsmm riskctl mmattrib venueprofile
- **Book 12** (`ml`): mlsynth labeling cvsplit mlbase gbdt featimp nettab lobseq xsnet represent uncert onlinelearn textml llmeval altdata genmkt rlcore rltrade deephedge regimes modelcard e2eport mltrain featstore exptrack mlinfer mlmonitor modelpkg lobmodel
- **Book 13** (`low-latency`): latbudget ubench memkit coreplan lathist arena pipeline flagbench affinity gcwatch mpmcq ring tuneaudit simdscan fixengine wirecodec wsclient feedhandler bookbuilder stratengine ordergw riskgate binlog sequencer perfgate ticktotrade (`coreplan` = Book 13 ch. 4's core-placement plan; `placement` is Book 10 ch. 17's child-order placement)

Cross-book contracts inside the batch (each implementer documents its API in the module docstring and
here when it lands): Book 11 `mmharness` (`Quoter` protocol over `firm_tape` now, `firm_exchsim` later);
Book 11 `riskctl` limits schema + fixtures, which Book 13 `riskgate` replays in nanoseconds (policy in
Book 11, implementation in Book 13); Book 10 `acexec`/`execalgo` schedules as Book 12 `rltrade`
baselines; Book 10 `agentmkt` stylised-fact checks callable on any message stream (Book 12 `genmkt`);
Book 13 `wirecodec` generated from `exchsim/schema.json`. When two batch books are written at the same
time, a consumer that reaches its chapter first writes against this contract and a thin adapter, and the
main session wires them together at the reconciliation.
