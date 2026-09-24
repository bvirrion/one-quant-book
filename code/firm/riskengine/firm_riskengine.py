"""The miniature firm's risk engine (build of One Quant Book 6, chapter 29).

Consumes the pricing library of Book 5 (code/firm/pricing, INTERFACES.md section 1) and registers the
rates instruments of this book with it: a pillar zero curve that bumps by pillar, spot-starting swaps and
European swaptions under a normal (Bachelier) model. The engine turns historical factor moves into
Scenarios, revalues a book of Trades in three ways (full revaluation, a revaluation grid per risk factor,
a delta-gamma approximation), counts the pricing calls each needs, and aggregates the P&L along the risk
hierarchy (the trade's book path) into VaR and ES per node, with Euler contributions of ES and limit
checks. The aggregation kernel has a C++20 twin (cpp/) and a Rust twin (rust/) on a shared fixture.
"""
import bisect
import datetime as dt
import math
import pathlib
import sys
from collections.abc import Sequence
from dataclasses import dataclass, replace

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
for _comp in ("pricing", "varmodel"):
    sys.path.insert(0, str(HERE.parent / _comp))
import firm_pricing as fp  # noqa: E402
from firm_varmodel import hs_var_es  # noqa: E402

TENORS = (1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0)
PILLARS = tuple(f"{int(t)}Y" for t in TENORS)


# ------------------------------------------------------------------------------------ market data
@dataclass(frozen=True)
class PillarCurve:
    """Continuously compounded zero rates at pillar tenors, linear between pillars, flat outside
    (a BumpableCurve with pillars, so the pricing library lists CURVE:<name>:<pillar> factors)."""
    asof: dt.date
    zeros: tuple[float, ...]
    tenors: tuple[float, ...] = TENORS

    def zero(self, t: float) -> float:
        ts, zs = self.tenors, self.zeros
        if t <= ts[0]:
            return zs[0]
        if t >= ts[-1]:
            return zs[-1]
        i = bisect.bisect_right(ts, t)
        w = (t - ts[i - 1]) / (ts[i] - ts[i - 1])
        return zs[i - 1] + w * (zs[i] - zs[i - 1])

    def df(self, d: dt.date) -> float:
        t = fp.year_fraction(self.asof, d)
        return math.exp(-self.zero(t) * t)

    def pillars(self) -> tuple[str, ...]:
        return tuple(f"{int(t)}Y" for t in self.tenors)

    def bumped(self, pillar: str | None, size: float) -> "PillarCurve":
        if pillar is None:
            return replace(self, zeros=tuple(z + size for z in self.zeros))
        i = self.pillars().index(pillar)
        return replace(self, zeros=tuple(z + size * (j == i) for j, z in enumerate(self.zeros)))

    def to_dict(self) -> dict:
        return {"type": "PillarCurve", "asof": self.asof.isoformat(), "zeros": list(self.zeros),
                "tenors": list(self.tenors)}


def add_years(d: dt.date, years: float) -> dt.date:
    return d + dt.timedelta(days=round(365.0 * years))


# ------------------------------------------------------------------------------------ rates instruments
@fp.instrument_type
@dataclass(frozen=True, kw_only=True)
class IRSwap(fp.Instrument):
    """Spot-starting swap, annual fixed against floating on one curve (single-curve, chapter 1)."""
    years: int
    fixed: float
    payer: bool = True


@fp.instrument_type
@dataclass(frozen=True, kw_only=True)
class Swaption(fp.Instrument):
    """European swaption into an annual swap of `tenor` years starting at expiry."""
    expiry: dt.date
    tenor: int
    strike: float
    payer: bool = True


@dataclass(frozen=True)
class NormalRates:
    """Bachelier model; the normal volatility is read from md.vols[underlying] unless fixed."""
    vol: float | None = None
    name: str = "NormalRates"

    def params(self) -> dict:
        return {} if self.vol is None else {"vol": self.vol}

    def calibrate(self, md: fp.MarketData, underlying: str) -> "NormalRates":
        return self

    def sigma(self, md: fp.MarketData, underlying: str, strike: float, expiry: dt.date) -> float:
        return self.vol if self.vol is not None else md.vols[underlying].implied_vol(strike, expiry)


@dataclass(frozen=True)
class SwapEngine:
    name: str = "SwapAnalytic"

    def supports(self, inst, model) -> bool:
        return isinstance(inst, IRSwap)

    def price(self, inst: IRSwap, model, md: fp.MarketData) -> float:
        c = inst.curve(md)
        dfs = [md.df(c, add_years(md.asof, i)) for i in range(1, inst.years + 1)]
        pv_payer = (1.0 - dfs[-1]) - inst.fixed * sum(dfs)
        return inst.notional * (pv_payer if inst.payer else -pv_payer)


def bachelier(fwd: float, strike: float, t: float, vol: float, payer: bool) -> float:
    if t <= 0.0 or vol <= 0.0:
        return max((fwd - strike) if payer else (strike - fwd), 0.0)
    s = vol * math.sqrt(t)
    d = (fwd - strike) / s
    n, cdf = math.exp(-0.5 * d * d) / math.sqrt(2.0 * math.pi), 0.5 * math.erfc(-d / math.sqrt(2.0))
    return (fwd - strike) * cdf + s * n if payer else (strike - fwd) * (1.0 - cdf) + s * n


@dataclass(frozen=True)
class SwaptionEngine:
    name: str = "Bachelier"

    def supports(self, inst, model) -> bool:
        return isinstance(inst, Swaption) and isinstance(model, NormalRates)

    def price(self, inst: Swaption, model: NormalRates, md: fp.MarketData) -> float:
        c = inst.curve(md)
        p0 = md.df(c, inst.expiry)
        dfs = [md.df(c, add_years(inst.expiry, i)) for i in range(1, inst.tenor + 1)]
        annuity = sum(dfs)
        fwd = (p0 - dfs[-1]) / annuity
        vol = model.sigma(md, inst.underlying, inst.strike, inst.expiry)
        return inst.notional * annuity * bachelier(fwd, inst.strike, md.t(inst.expiry), vol, inst.payer)


fp.register(IRSwap, NormalRates, SwapEngine())
fp.register(Swaption, NormalRates, SwaptionEngine())


def model_for(inst: fp.Instrument):
    return NormalRates() if isinstance(inst, IRSwap | Swaption) else fp.BlackScholes()


# ------------------------------------------------------------------------------------ trades, scenarios
@dataclass(frozen=True)
class Trade:
    """A position with the metadata the pricing library leaves out (INTERFACES.md rule 5)."""
    trade_id: str
    instrument: fp.Instrument
    quantity: float
    path: tuple[str, ...]          # risk hierarchy, e.g. ("Firm", "Rates", "Swaps")
    counterparty: str = ""


def historical_scenarios(names: Sequence[str], factors: Sequence[str], moves: np.ndarray,
                         relative: Sequence[bool]) -> list[fp.Scenario]:
    """One Scenario per row of `moves` (a day's change of every factor), as Bumps on the risk-factor ids."""
    return [fp.Scenario(n, tuple(fp.Bump(f, float(x), r) for f, x, r in zip(factors, row, relative, strict=True)))
            for n, row in zip(names, moves, strict=True)]


def dependencies(inst: fp.Instrument, factors: Sequence[str]) -> list[int]:
    """Indices of the factors a trade depends on: its curve's pillars, and its underlying's spot."""
    return [i for i, f in enumerate(factors)
            if f.startswith("CURVE:") or f == f"SPOT:{inst.underlying}"]


class Counter:
    def __init__(self):
        self.calls = 0
        self.errors: dict = {}

    def pv(self, inst, md) -> float:
        self.calls += 1
        return fp.price(inst, md, model_for(inst)).pv


# ------------------------------------------------------------------------------------ revaluation
def full_revaluation(trades: Sequence[Trade], md: fp.MarketData, scenarios: Sequence[fp.Scenario],
                     counter: Counter) -> np.ndarray:
    """P&L [scenario, trade] by repricing every trade in every snapshot through the library's price_batch
    (a failing trade gives NaN and an entry in counter.errors, never a stopped run)."""
    snaps = [md] + [md.apply(*s.bumps) for s in scenarios]
    res = fp.price_batch([(t.instrument, t.quantity) for t in trades], snaps, model_for=model_for)
    counter.calls += res.pv.size
    counter.errors.update(res.errors)
    return res.pv[1:] - res.pv[0]


def _moves(scenarios: Sequence[fp.Scenario]) -> np.ndarray:
    return np.array([[b.size for b in s.bumps] for s in scenarios])


def grid_revaluation(trades: Sequence[Trade], md: fp.MarketData, scenarios: Sequence[fp.Scenario],
                     counter: Counter, points: int = 7) -> np.ndarray:
    """Each trade repriced on a grid of `points` shifts of each factor it depends on, spanning the
    largest move in the scenarios; scenario P&L = sum over factors of the interpolated grid P&L."""
    x = _moves(scenarios)
    tmpl = scenarios[0].bumps
    out = np.zeros((len(scenarios), len(trades)))
    for j, tr in enumerate(trades):
        base = counter.pv(tr.instrument, md)
        for k in dependencies(tr.instrument, [b.factor for b in tmpl]):
            m = float(np.abs(x[:, k]).max())
            g = np.linspace(-m, m, points)
            pnl = np.array([0.0 if abs(s) < 1e-15 else
                            counter.pv(tr.instrument, md.apply(replace(tmpl[k], size=float(s)))) - base
                            for s in g])
            out[:, j] += tr.quantity * np.interp(x[:, k], g, pnl)
    return out


def delta_gamma_revaluation(trades: Sequence[Trade], md: fp.MarketData, scenarios: Sequence[fp.Scenario],
                            counter: Counter) -> np.ndarray:
    """Second-order Taylor expansion per factor (no cross terms), from central bumps of each factor."""
    x = _moves(scenarios)
    tmpl = scenarios[0].bumps
    out = np.zeros((len(scenarios), len(trades)))
    for j, tr in enumerate(trades):
        base = counter.pv(tr.instrument, md)
        for k in dependencies(tr.instrument, [b.factor for b in tmpl]):
            h = 0.01 if tmpl[k].relative else 1e-4
            up = counter.pv(tr.instrument, md.apply(replace(tmpl[k], size=h)))
            dn = counter.pv(tr.instrument, md.apply(replace(tmpl[k], size=-h)))
            d, g = (up - dn) / (2 * h), (up - 2 * base + dn) / (h * h)
            out[:, j] += tr.quantity * (d * x[:, k] + 0.5 * g * x[:, k] ** 2)
    return out


METHODS = {"full": full_revaluation, "grid": grid_revaluation, "delta-gamma": delta_gamma_revaluation}


def planned_revaluation(trades: Sequence[Trade], md: fp.MarketData, scenarios: Sequence[fp.Scenario],
                        counter: Counter, plan: dict[tuple[str, ...], str], default: str = "grid") -> np.ndarray:
    """Each trade revalued by the method its deepest planned node names (a revaluation plan by desk)."""
    def method(t: Trade) -> str:
        hits = [n for n in plan if t.path[:len(n)] == n]
        return plan[max(hits, key=len)] if hits else default
    out = np.zeros((len(scenarios), len(trades)))
    for name, f in METHODS.items():
        idx = [j for j, t in enumerate(trades) if method(t) == name]
        if idx:
            out[:, idx] = f([trades[j] for j in idx], md, scenarios, counter)
    return out


# ------------------------------------------------------------------------------------ aggregation
def nodes(paths: Sequence[tuple[str, ...]]) -> list[tuple[str, ...]]:
    """Every prefix of every path, parents before children."""
    out = sorted({p[:i] for p in paths for i in range(1, len(p) + 1)}, key=lambda n: (len(n), n))
    return out


def aggregate(pnl: np.ndarray, paths: Sequence[tuple[str, ...]]) -> dict[tuple[str, ...], np.ndarray]:
    """P&L vector of each node of the hierarchy: the sum of its trades' P&L in every scenario."""
    agg = {}
    for n in nodes(paths):
        cols = [j for j, p in enumerate(paths) if p[:len(n)] == n]
        agg[n] = pnl[:, cols].sum(axis=1)
    return agg


def risk_report(agg: dict, var_level: float = 0.99, es_level: float = 0.975) -> dict:
    """VaR and ES per node (positive losses, historical: k-th largest loss, k = ceil((1 - a) n))."""
    return {n: {"var": hs_var_es(v, var_level)[0], "es": hs_var_es(v, es_level)[1]} for n, v in agg.items()}


def euler_es(parent: np.ndarray, children: dict, level: float = 0.975) -> dict:
    """Euler contributions of historical ES: each child's average loss in the parent's tail scenarios."""
    k = max(1, math.ceil((1.0 - level) * len(parent) - 1e-9))
    tail = np.argsort(parent, kind="stable")[:k]
    return {c: float(-v[tail].mean()) for c, v in children.items()}


def check_limits(report: dict, limits: dict) -> list[tuple[tuple[str, ...], float, float]]:
    """(node, VaR, limit) for every node whose VaR exceeds its limit."""
    return [(n, report[n]["var"], lim) for n, lim in limits.items() if report[n]["var"] > lim]
