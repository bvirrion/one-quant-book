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
