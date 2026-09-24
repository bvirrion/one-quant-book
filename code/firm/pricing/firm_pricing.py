"""The miniature firm's pricing library (built across Book 5, completed in Chapter 28).

Interface frozen in code/firm/INTERFACES.md, section 1 (Book 5 implements, Book 6's risk engine
consumes). Instruments, models and engines are separate concepts; market data is an immutable
snapshot; every Greek, sensitivity, scenario and batch goes through one repricing function, so any
engine that can price can be risk-managed. Numpy only.

The core (market data, bumps, European and American options, Black-Scholes model, analytic and tree
engines, price / greeks / sensitivities / bucketed_vega / reprice / price_batch) landed with
Chapter 4; later chapters register further instruments, models and engines.
"""
import dataclasses
import datetime as dt
import math
import pathlib
import sys
import zlib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Literal, Protocol, runtime_checkable

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
for _comp in ("bs", "binomial"):
    sys.path.insert(0, str(HERE.parent / _comp))
from firm_binomial import price as _tree_price  # noqa: E402
from firm_bs import black  # noqa: E402


class PricingError(ValueError):
    """Raised for an unsupported instrument/model/engine combination or inconsistent market data."""


# ------------------------------------------------------------------------------------ market objects
@runtime_checkable
class DiscountCurve(Protocol):
    def df(self, d: dt.date) -> float: ...


@runtime_checkable
class BumpableCurve(DiscountCurve, Protocol):
    def bumped(self, pillar: str | None, size: float) -> "BumpableCurve": ...


@runtime_checkable
class VolSurface(Protocol):
    def implied_vol(self, strike: float, expiry: dt.date) -> float: ...
    def total_variance(self, k: float, t: float) -> float: ...


def year_fraction(a: dt.date, b: dt.date) -> float:
    """ACT/365F."""
    return (b - a).days / 365.0


@dataclass(frozen=True)
class FlatCurve:
    """Continuously compounded flat rate from `asof` (a BumpableCurve without pillars)."""
    rate: float
    asof: dt.date

    def df(self, d: dt.date) -> float:
        return math.exp(-self.rate * year_fraction(self.asof, d))

    def bumped(self, pillar: str | None, size: float) -> "FlatCurve":
        if pillar is not None:
            raise PricingError("a flat curve has no pillars")
        return FlatCurve(self.rate + size, self.asof)

    def to_dict(self) -> dict:
        return {"type": "FlatCurve", "rate": self.rate, "asof": self.asof.isoformat()}


@dataclass(frozen=True)
class ShiftedCurve:
    """Parallel zero-rate shift of any DiscountCurve that cannot bump itself."""
    base: DiscountCurve
    shift: float
    asof: dt.date

    def df(self, d: dt.date) -> float:
        return self.base.df(d) * math.exp(-self.shift * year_fraction(self.asof, d))


@dataclass(frozen=True)
class FlatVol:
    vol: float

    def implied_vol(self, strike: float, expiry: dt.date) -> float:
        return self.vol

    def total_variance(self, k: float, t: float) -> float:
        return self.vol * self.vol * t

    def to_dict(self) -> dict:
        return {"type": "FlatVol", "vol": self.vol}


@dataclass(frozen=True)
class ShiftedSurface:
    """Parallel shift of implied volatility, in volatility units."""
    base: VolSurface
    shift: float

    def implied_vol(self, strike: float, expiry: dt.date) -> float:
        return self.base.implied_vol(strike, expiry) + self.shift

    def total_variance(self, k: float, t: float) -> float:
        return (math.sqrt(self.base.total_variance(k, t) / t) + self.shift) ** 2 * t if t > 0 else 0.0


@dataclass(frozen=True)
class GridSurface:
    """Implied volatilities on an expiry x strike grid (sticky strike). Linear in log-strike within an
    expiry (flat beyond the wings), linear in total variance between expiries at fixed strike (flat
    volatility beyond the last). Its nodes are risk factors VOL:<und>:<expiry>:<strike>."""
    asof: dt.date
    expiries: tuple[dt.date, ...]
    strikes: tuple[float, ...]
    vols: tuple[tuple[float, ...], ...]          # vols[i][j] at expiries[i], strikes[j]
    forwards: tuple[float, ...]                  # forward per expiry, for total_variance(k, t)

    def _slice(self, i: int, strike: float) -> float:
        x, row = math.log(strike), self.vols[i]
        xs = [math.log(k) for k in self.strikes]
        if x <= xs[0]:
            return row[0]
        if x >= xs[-1]:
            return row[-1]
        j = next(j for j in range(1, len(xs)) if x <= xs[j])
        w = (x - xs[j - 1]) / (xs[j] - xs[j - 1])
        return row[j - 1] + w * (row[j] - row[j - 1])

    def implied_vol(self, strike: float, expiry: dt.date) -> float:
        t = year_fraction(self.asof, expiry)
        ts = [year_fraction(self.asof, e) for e in self.expiries]
        if t <= ts[0]:
            return self._slice(0, strike)
        if t >= ts[-1]:
            return self._slice(len(ts) - 1, strike)
        i = next(i for i in range(1, len(ts)) if t <= ts[i])
        w0, w1 = self._slice(i - 1, strike) ** 2 * ts[i - 1], self._slice(i, strike) ** 2 * ts[i]
        w = w0 + (t - ts[i - 1]) / (ts[i] - ts[i - 1]) * (w1 - w0)
        return math.sqrt(w / t)

    def _forward(self, t: float) -> float:
        ts = [year_fraction(self.asof, e) for e in self.expiries]
        lf = [math.log(f) for f in self.forwards]
        return math.exp(float(np.interp(t, ts, lf)))

    def total_variance(self, k: float, t: float) -> float:
        expiry = self.asof + dt.timedelta(days=round(t * 365.0))
        return self.implied_vol(self._forward(t) * math.exp(k), expiry) ** 2 * t

    def nodes(self) -> list[tuple[dt.date, float]]:
        return [(e, k) for e in self.expiries for k in self.strikes]

    def bumped_node(self, expiry: dt.date, strike: float, size: float) -> "GridSurface":
        i, j = self.expiries.index(expiry), self.strikes.index(strike)
        rows = [list(r) for r in self.vols]
        rows[i][j] += size
        return replace(self, vols=tuple(tuple(r) for r in rows))


@dataclass(frozen=True)
class Dividends:
    cash: tuple[tuple[dt.date, float], ...] = ()
    proportional: tuple[tuple[dt.date, float], ...] = ()
    borrow: float = 0.0
    div_yield: float = 0.0          # continuous yield (added by Book 5 for the DIV:<und> risk factor)


@dataclass(frozen=True)
class RiskFactor:
    id: str
    kind: str
    unit: str
    shift: Literal["abs", "rel"]


@dataclass(frozen=True)
class Bump:
    factor: str
    size: float
    relative: bool = False

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class Scenario:
    name: str
    bumps: tuple[Bump, ...]

    def to_dict(self) -> dict:
        return {"name": self.name, "bumps": [b.to_dict() for b in self.bumps]}

    @staticmethod
    def from_dict(d: dict) -> "Scenario":
        return Scenario(d["name"], tuple(Bump(**b) for b in d["bumps"]))


# Standard shift per factor kind: (size, relative, unit). Sensitivities are PV changes per this shift.
STANDARD_SHIFT = {"SPOT": (0.01, True, "price"), "VOL": (0.01, False, "vol"), "CURVE": (1e-4, False, "rate"),
                  "DIV": (1e-4, False, "rate"), "BORROW": (1e-4, False, "rate"), "CORR": (0.01, False, "-"),
                  "FX": (0.01, True, "price"), "CREDIT": (1e-4, False, "rate"), "TIME": (1.0, False, "days")}
_BUMP_HANDLERS: dict[str, Callable[["MarketData", Bump], "MarketData"]] = {}


def register_bump(kind: str, handler: Callable[["MarketData", Bump], "MarketData"],
                  standard: tuple[float, bool, str] = (1e-4, False, "rate")) -> None:
    """Let another book add a risk-factor kind (Book 6: inflation, basis, SABR parameters, credit)."""
    _BUMP_HANDLERS[kind] = handler
    STANDARD_SHIFT.setdefault(kind, standard)


def _plus(mapping: Mapping, key, value) -> dict:
    out = dict(mapping)
    out[key] = value
    return out


@dataclass(frozen=True)
class MarketData:
    asof: dt.date
    spots: Mapping[str, float]
    curves: Mapping[str, DiscountCurve]
    dividends: Mapping[str, Dividends] = field(default_factory=dict)
    vols: Mapping[str, VolSurface] = field(default_factory=dict)
    correlations: Mapping[frozenset, float] = field(default_factory=dict)
    fixings: Mapping[str, Mapping[dt.date, float]] = field(default_factory=dict)
    fx: Mapping[str, float] = field(default_factory=dict)
    funding: Mapping[str, str] = field(default_factory=dict)   # underlying -> curve used for its forward

    def t(self, d: dt.date) -> float:
        return year_fraction(self.asof, d)

    def df(self, curve: str, d: dt.date) -> float:
        """Discount factor from asof to d; curves are held (forward rates unchanged) when rolled."""
        c = self.curves[curve]
        return c.df(d) / c.df(self.asof)

    def funding_curve(self, underlying: str) -> str:
        if underlying in self.funding:
            return self.funding[underlying]
        if len(self.curves) == 1:
            return next(iter(self.curves))
        raise PricingError(f"no funding curve for {underlying}: set MarketData.funding")

    def forward(self, underlying: str, d: dt.date) -> float:
        """(S - PV of cash dividends) x prod(1 - proportional) x exp(-(borrow + yield) T) / P(T)."""
        c, t = self.funding_curve(underlying), self.t(d)
        div = self.dividends.get(underlying, Dividends())
        pv_cash = sum(a * self.df(c, ti) for ti, a in div.cash if self.asof < ti <= d)
        prop = math.prod(1.0 - y for ti, y in div.proportional if self.asof < ti <= d)
        return ((self.spots[underlying] - pv_cash) * prop * math.exp(-(div.borrow + div.div_yield) * t)
                / self.df(c, d))

    def fx_rate(self, ccy_from: str, ccy_to: str) -> float:
        """Units of ccy_to per unit of ccy_from, from pairs quoted BASEQUOTE (quote per base)."""
        if ccy_from == ccy_to:
            return 1.0
        if ccy_from + ccy_to in self.fx:
            return self.fx[ccy_from + ccy_to]
        if ccy_to + ccy_from in self.fx:
            return 1.0 / self.fx[ccy_to + ccy_from]
        raise PricingError(f"no FX rate {ccy_from}{ccy_to}")

    def risk_factors(self) -> tuple[RiskFactor, ...]:
        out = [RiskFactor(f"SPOT:{u}", "SPOT", "price", "rel") for u in self.spots]
        for u, s in self.vols.items():
            out.append(RiskFactor(f"VOL:{u}", "VOL", "vol", "abs"))
            if hasattr(s, "nodes"):
                out += [RiskFactor(f"VOL:{u}:{e.isoformat()}:{k:g}", "VOL", "vol", "abs")
                        for e, k in s.nodes()]
        for name, c in self.curves.items():
            out.append(RiskFactor(f"CURVE:{name}", "CURVE", "rate", "abs"))
            if hasattr(c, "pillars"):
                out += [RiskFactor(f"CURVE:{name}:{p}", "CURVE", "rate", "abs") for p in c.pillars()]
        for u in self.dividends:
            out += [RiskFactor(f"DIV:{u}", "DIV", "rate", "abs"), RiskFactor(f"BORROW:{u}", "BORROW", "rate", "abs")]
        out += [RiskFactor("CORR:" + "|".join(sorted(p)), "CORR", "-", "abs") for p in self.correlations]
        out += [RiskFactor(f"FX:{p}", "FX", "price", "rel") for p in self.fx]
        out.append(RiskFactor("TIME", "TIME", "days", "abs"))
        return tuple(out)

    def apply(self, *bumps: Bump) -> "MarketData":
        md = self
        for b in bumps:
            md = md._apply_one(b)
        return md

    def _apply_one(self, b: Bump) -> "MarketData":
        parts = b.factor.split(":")
        kind = parts[0]

        def shifted(x: float) -> float:
            return x * (1.0 + b.size) if b.relative else x + b.size
        if kind == "SPOT":
            return replace(self, spots=_plus(self.spots, parts[1], shifted(self.spots[parts[1]])))
        if kind == "FX":
            return replace(self, fx=_plus(self.fx, parts[1], shifted(self.fx[parts[1]])))
        if kind == "VOL":
            s = self.vols[parts[1]]
            if len(parts) == 2:
                return replace(self, vols=_plus(self.vols, parts[1], ShiftedSurface(s, b.size)))
            if not hasattr(s, "bumped_node"):
                raise PricingError(f"surface of {parts[1]} has no nodes: use bucketed_vega")
            expiry, strike = dt.date.fromisoformat(parts[2]), float(parts[3])
            return replace(self, vols=_plus(self.vols, parts[1], s.bumped_node(expiry, strike, b.size)))
        if kind == "CURVE":
            c, pillar = self.curves[parts[1]], (parts[2] if len(parts) > 2 else None)
            if isinstance(c, BumpableCurve) and hasattr(c, "bumped"):
                new = c.bumped(pillar, b.size)
            elif pillar is None:
                new = ShiftedCurve(c, b.size, self.asof)
            else:
                raise PricingError(f"curve {parts[1]} cannot bump pillar {pillar}")
            return replace(self, curves=_plus(self.curves, parts[1], new))
        if kind in ("DIV", "BORROW"):
            d = self.dividends.get(parts[1], Dividends())
            d = replace(d, div_yield=d.div_yield + b.size) if kind == "DIV" else replace(d, borrow=d.borrow + b.size)
            return replace(self, dividends=_plus(self.dividends, parts[1], d))
        if kind == "CORR":
            key = frozenset(parts[1].split("|"))
            return replace(self, correlations=_plus(self.correlations, key,
                                                    min(1.0, max(-1.0, self.correlations.get(key, 0.0) + b.size))))
        if kind == "TIME":
            return self.rolled(self.asof + dt.timedelta(days=round(b.size)))
        if kind in _BUMP_HANDLERS:
            return _BUMP_HANDLERS[kind](self, b)
        raise PricingError(f"unknown risk factor {b.factor}")

    def rolled(self, new_asof: dt.date) -> "MarketData":
        """Move the valuation date; spots, curves (forward rates) and surfaces (by strike and expiry
        date) are held."""
        return replace(self, asof=new_asof)

    def to_dict(self) -> dict:
        """The plain fields (curve and surface objects serialise through their own to_dict when they have one)."""
        def obj(x):
            return x.to_dict() if hasattr(x, "to_dict") else None
        return {"asof": self.asof.isoformat(), "spots": dict(self.spots),
                "dividends": {u: {"cash": [[d.isoformat(), a] for d, a in v.cash],
                                  "proportional": [[d.isoformat(), y] for d, y in v.proportional],
                                  "borrow": v.borrow, "div_yield": v.div_yield} for u, v in self.dividends.items()},
                "correlations": {"|".join(sorted(k)): v for k, v in self.correlations.items()},
                "fixings": {u: {d.isoformat(): x for d, x in v.items()} for u, v in self.fixings.items()},
                "fx": dict(self.fx), "funding": dict(self.funding),
                "curves": {k: obj(c) for k, c in self.curves.items()},
                "vols": {k: obj(s) for k, s in self.vols.items()}}


# ------------------------------------------------------------------------------------ instruments
_INSTRUMENTS: dict[str, type] = {}


def instrument_type(cls):
    """Class decorator: make an Instrument subclass JSON-round-trippable."""
    _INSTRUMENTS[cls.__name__] = cls
    return cls


def _to_json(x):
    if isinstance(x, dt.date):
        return {"date": x.isoformat()}
    if isinstance(x, tuple | list):
        return [_to_json(v) for v in x]
    if isinstance(x, dict):
        return {k: _to_json(v) for k, v in x.items()}
    return x


def _from_json(x):
    if isinstance(x, dict) and set(x) == {"date"}:
        return dt.date.fromisoformat(x["date"])
    if isinstance(x, list):
        return tuple(_from_json(v) for v in x)
    if isinstance(x, dict):
        return {k: _from_json(v) for k, v in x.items()}
    return x


@dataclass(frozen=True, kw_only=True)
class Instrument:
    id: str
    underlying: str
    currency: str
    notional: float = 1.0
    discount_curve: str = ""          # "" = the curve named after the currency, or the only curve

    def to_dict(self) -> dict:
        return {"type": type(self).__name__,
                **{f.name: _to_json(getattr(self, f.name)) for f in dataclasses.fields(self)}}

    def curve(self, md: MarketData) -> str:
        if self.discount_curve:
            return self.discount_curve
        if self.currency in md.curves:
            return self.currency
        if len(md.curves) == 1:
            return next(iter(md.curves))
        raise PricingError(f"{self.id}: no discount curve")


def instrument_from_dict(d: dict) -> Instrument:
    d = dict(d)
    cls = _INSTRUMENTS[d.pop("type")]
    return cls(**{k: _from_json(v) for k, v in d.items()})


@instrument_type
@dataclass(frozen=True, kw_only=True)
class EuropeanOption(Instrument):
    strike: float
    expiry: dt.date
    right: Literal["C", "P"]
    exercise: Literal["european", "american", "bermudan"] = "european"
    exercise_dates: tuple[dt.date, ...] = ()


def seed_for(inst: Instrument) -> int:
    """Common random numbers: one fixed seed per instrument (never the salted hash())."""
    return zlib.crc32(inst.id.encode())


# ------------------------------------------------------------------------------------ models, engines
class Model(Protocol):
    name: str
    def params(self) -> Mapping[str, float]: ...
    def calibrate(self, md: MarketData, underlying: str) -> "Model": ...


class Engine(Protocol):
    name: str
    def supports(self, inst: Instrument, model: Model) -> bool: ...
    def price(self, inst: Instrument, model: Model, md: MarketData) -> float: ...


@dataclass(frozen=True)
class BlackScholes:
    """Lognormal model with the volatility read from the surface at the option's strike and expiry
    (sticky strike), or a fixed volatility when `vol` is given."""
    vol: float | None = None
    name: str = "BlackScholes"

    def params(self) -> Mapping[str, float]:
        return {} if self.vol is None else {"vol": self.vol}

    def calibrate(self, md: MarketData, underlying: str) -> "BlackScholes":
        return self

    def sigma(self, md: MarketData, underlying: str, strike: float, expiry: dt.date) -> float:
        return self.vol if self.vol is not None else md.vols[underlying].implied_vol(strike, expiry)


@dataclass(frozen=True)
class AnalyticEngine:
    """Black's formula on the forward, discounted on the instrument's curve."""
    name: str = "Analytic"

    def supports(self, inst: Instrument, model: Model) -> bool:
        return isinstance(inst, EuropeanOption) and inst.exercise == "european" and isinstance(model, BlackScholes)

    def price(self, inst: EuropeanOption, model: BlackScholes, md: MarketData) -> float:
        t = md.t(inst.expiry)
        if t < 0:
            return 0.0
        fwd = md.forward(inst.underlying, inst.expiry)
        vol = model.sigma(md, inst.underlying, inst.strike, inst.expiry)
        return inst.notional * black(fwd, inst.strike, t, md.df(inst.curve(md), inst.expiry), vol, inst.right)


@dataclass(frozen=True)
class TreeEngine:
    """Leisen-Reimer tree (chapter 2): European or American exercise, cash dividends escrowed."""
    steps: int = 501
    name: str = "Tree"

    def supports(self, inst: Instrument, model: Model) -> bool:
        return (isinstance(inst, EuropeanOption) and inst.exercise in ("european", "american")
                and isinstance(model, BlackScholes))

    def price(self, inst: EuropeanOption, model: BlackScholes, md: MarketData) -> float:
        t = md.t(inst.expiry)
        if t <= 0:
            s = md.spots[inst.underlying]
            return inst.notional * max((s - inst.strike) if inst.right == "C" else (inst.strike - s), 0.0) * (t == 0)
        c = md.funding_curve(inst.underlying)
        r = -math.log(md.df(c, inst.expiry)) / t
        div = md.dividends.get(inst.underlying, Dividends())
        cash = tuple((md.t(d), a) for d, a in div.cash if md.asof < d <= inst.expiry)
        prop = math.prod(1.0 - y for d, y in div.proportional if md.asof < d <= inst.expiry)
        q = div.borrow + div.div_yield - math.log(prop) / t
        vol = model.sigma(md, inst.underlying, inst.strike, inst.expiry)
        v = _tree_price(md.spots[inst.underlying], inst.strike, t, r, vol, self.steps, inst.right,
                        american=inst.exercise == "american", q=q, method="lr", dividends=cash)
        return inst.notional * v * md.df(inst.curve(md), inst.expiry) / md.df(c, inst.expiry)


_REGISTRY: dict[tuple[type, type], list] = {}


def register(inst_type: type, model_type: type, engine) -> None:
    """Add an engine for (instrument type, model type); the first registered that supports is the default."""
    _REGISTRY.setdefault((inst_type, model_type), []).append(engine)


register(EuropeanOption, BlackScholes, AnalyticEngine())
register(EuropeanOption, BlackScholes, TreeEngine())


def default_engine(inst: Instrument, model: Model):
    for it in type(inst).__mro__:
        for mt in type(model).__mro__:
            for e in _REGISTRY.get((it, mt), []):
                if e.supports(inst, model):
                    return e
    raise PricingError(f"no engine for {type(inst).__name__} under {getattr(model, 'name', model)}")


# ------------------------------------------------------------------------------------ top-level calls
@dataclass(frozen=True)
class PriceResult:
    pv: float
    currency: str
    model: str
    engine: str
    diagnostics: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class GreekBumps:
    spot_rel: float = 0.01
    vol_abs: float = 0.01
    rate_abs: float = 1e-4
    theta_days: int = 1


DEFAULT_BUMPS = GreekBumps()
Position = tuple[Instrument, float]


def _resolve(inst: Instrument, model, engine):
    model = model if model is not None else BlackScholes()
    engine = engine if engine is not None else default_engine(inst, model)
    if not engine.supports(inst, model):
        raise PricingError(f"engine {engine.name} does not support {type(inst).__name__} under {model.name}")
    return model, engine


def _pv(inst: Instrument, md: MarketData, model, engine, recalibrate: bool = False) -> float:
    if recalibrate:
        model = model.calibrate(md, inst.underlying)
    return engine.price(inst, model, md)


def price(inst: Instrument, md: MarketData, model=None, engine=None) -> PriceResult:
    model, engine = _resolve(inst, model, engine)
    return PriceResult(engine.price(inst, model, md), inst.currency, model.name, engine.name, {})


def greeks(inst: Instrument, md: MarketData, model=None, engine=None,
           which: Sequence[str] = ("delta", "gamma", "vega", "theta", "rho"),
           bumps: GreekBumps = DEFAULT_BUMPS, recalibrate: bool = False) -> dict[str, float]:
    """Desk-unit Greeks by central bump-and-reprice (an engine's own `greeks` overrides when present):
    delta in underlying units; gamma = change of cash delta for a +1 % move (Gamma S^2 / 100); vega per
    volatility point; theta per day (valuation date rolled); rho per basis point on every curve;
    vanna (delta per vol point) and volga (vega per vol point) on request."""
    model, engine = _resolve(inst, model, engine)
    if hasattr(engine, "greeks"):
        return engine.greeks(inst, model, md, which)
    u, s = inst.underlying, md.spots[inst.underlying]
    h = bumps.spot_rel

    def pv(m: MarketData) -> float:
        return _pv(inst, m, model, engine, recalibrate)

    def spot(m: MarketData, x: float) -> MarketData:
        return m.apply(Bump(f"SPOT:{u}", x, True))

    def vol(m: MarketData, x: float) -> MarketData:
        return m.apply(Bump(f"VOL:{u}", x))
    out, base = {}, pv(md)
    if {"delta", "gamma"} & set(which):
        up, dn = pv(spot(md, h)), pv(spot(md, -h))
        out["delta"] = (up - dn) / (2 * h * s)
        out["gamma"] = (up - 2 * base + dn) / (h * s) ** 2 * s * s / 100.0
    if "vega" in which:
        out["vega"] = (pv(vol(md, bumps.vol_abs)) - pv(vol(md, -bumps.vol_abs))) / 2 * (0.01 / bumps.vol_abs)
    if "theta" in which:
        out["theta"] = (pv(md.rolled(md.asof + dt.timedelta(days=bumps.theta_days))) - base) / bumps.theta_days
    if "rho" in which:
        up_c = md.apply(*[Bump(f"CURVE:{c}", bumps.rate_abs) for c in md.curves])
        dn_c = md.apply(*[Bump(f"CURVE:{c}", -bumps.rate_abs) for c in md.curves])
        out["rho"] = (pv(up_c) - pv(dn_c)) / 2 * (1e-4 / bumps.rate_abs)
    if "vanna" in which:
        d_up = (pv(spot(vol(md, 0.01), h)) - pv(spot(vol(md, 0.01), -h))) / (2 * h * s)
        d_dn = (pv(spot(vol(md, -0.01), h)) - pv(spot(vol(md, -0.01), -h))) / (2 * h * s)
        out["vanna"] = (d_up - d_dn) / 2
    if "volga" in which:
        out["volga"] = pv(vol(md, 0.01)) - 2 * base + pv(vol(md, -0.01))
    return out


def sensitivities(inst: Instrument, md: MarketData, factors: Sequence[str], model=None,
                  engine=None) -> dict[str, float]:
    """PV change per standard shift of each risk factor (STANDARD_SHIFT: 1 % for spots and FX, one vol
    point, one basis point, 0.01 of correlation, one day), by central difference (forward for TIME)."""
    model, engine = _resolve(inst, model, engine)
    if hasattr(engine, "sensitivities"):
        return engine.sensitivities(inst, model, md, factors)
    out = {}
    for f in factors:
        size, rel, _ = STANDARD_SHIFT.get(f.split(":")[0], (1e-4, False, "rate"))
        if f == "TIME":
            out[f] = _pv(inst, md.apply(Bump(f, size)), model, engine) - _pv(inst, md, model, engine)
        else:
            up = _pv(inst, md.apply(Bump(f, size, rel)), model, engine)
            dn = _pv(inst, md.apply(Bump(f, -size, rel)), model, engine)
            out[f] = (up - dn) / 2
    return out


def grid_from(md: MarketData, underlying: str, expiries: Sequence[dt.date],
              strikes: Sequence[float]) -> GridSurface:
    """Sample any surface of the snapshot on a grid, so that its nodes can be bumped."""
    s = md.vols[underlying]
    return GridSurface(md.asof, tuple(expiries), tuple(strikes),
                       tuple(tuple(s.implied_vol(k, e) for k in strikes) for e in expiries),
                       tuple(md.forward(underlying, e) for e in expiries))


def bucketed_vega(inst: Instrument, md: MarketData, expiries: Sequence[dt.date], strikes: Sequence[float],
                  model=None, engine=None) -> dict[tuple[dt.date, float], float]:
    """Vega per volatility point to each node of an expiry x strike grid (interpolation spreads a node
    bump to its neighbours). The sum over nodes approximates the parallel vega."""
    model, engine = _resolve(inst, model, engine)
    u = inst.underlying
    md0 = replace(md, vols=_plus(md.vols, u, grid_from(md, u, expiries, strikes)))
    out = {}
    for e in expiries:
        for k in strikes:
            f = f"VOL:{u}:{e.isoformat()}:{k:g}"
            out[(e, k)] = (_pv(inst, md0.apply(Bump(f, 0.01)), model, engine)
                           - _pv(inst, md0.apply(Bump(f, -0.01)), model, engine)) / 2
    return out


def reprice(book: Sequence[Position], md: MarketData, scenarios: Sequence[Scenario],
            model_for: Callable[[Instrument], object] | None = None,
            engine_for: Callable[[Instrument], object] | None = None) -> dict[str, float]:
    """Scenario name -> PV change of the book (quantity-weighted, each in its own currency)."""
    resolved = [(_resolve(i, model_for(i) if model_for else None, engine_for(i) if engine_for else None), i, q)
                for i, q in book]
    base = sum(q * _pv(i, md, m, e) for (m, e), i, q in resolved)
    out = {}
    for sc in scenarios:
        m_s = md.apply(*sc.bumps)
        out[sc.name] = sum(q * _pv(i, m_s, m, e) for (m, e), i, q in resolved) - base
    return out


@dataclass(frozen=True)
class BatchResult:
    pv: np.ndarray                                  # [len(snapshots), len(book)], NaN on failure
    errors: dict[tuple[int, int], str]


def price_batch(book: Sequence[Position], snapshots: Sequence[MarketData],
                model_for: Callable[[Instrument], object] | None = None,
                engine_for: Callable[[Instrument], object] | None = None) -> BatchResult:
    """PV of every position (quantity-weighted, own currency) in every snapshot; one failing trade never
    kills the batch."""
    pv = np.full((len(snapshots), len(book)), np.nan)
    errors: dict[tuple[int, int], str] = {}
    for j, (inst, q) in enumerate(book):
        try:
            model, engine = _resolve(inst, model_for(inst) if model_for else None,
                                     engine_for(inst) if engine_for else None)
        except Exception as exc:  # noqa: BLE001 -- recorded per trade
            for i in range(len(snapshots)):
                errors[(i, j)] = f"{type(exc).__name__}: {exc}"
            continue
        for i, m in enumerate(snapshots):
            try:
                pv[i, j] = q * _pv(inst, m, model, engine)
            except Exception as exc:  # noqa: BLE001
                errors[(i, j)] = f"{type(exc).__name__}: {exc}"
    return BatchResult(pv, errors)


# ==================================================================================== Chapter 28
# Further instruments, models and engines: the rest of Book 5 behind the same interface. Every engine reads its
# market from the snapshot (spots, forwards, curves, surfaces, correlations, fixings), so every bump, Greek and
# scenario above applies to it unchanged.
for _comp in ("barrier", "autocall", "calib", "varswap", "convertible"):
    sys.path.insert(0, str(HERE.parent / _comp))
from firm_autocall import TermSheet as _TermSheet  # noqa: E402
from firm_autocall import cashflows as _autocall_cashflows  # noqa: E402
from firm_barrier import barrier as _barrier  # noqa: E402
from firm_barrier import bgk_shift as _bgk_shift  # noqa: E402
from firm_calib import cos_calls as _cos_calls  # noqa: E402
from firm_convertible import Convertible as _Convertible  # noqa: E402
from firm_convertible import power_hazard as _power_hazard  # noqa: E402
from firm_convertible import price_grid as _cb_grid  # noqa: E402
from firm_convertible import value_at as _cb_value_at  # noqa: E402
from firm_heston import Heston as _HestonCF  # noqa: E402
from firm_varswap import index_variance as _index_variance  # noqa: E402


@instrument_type
@dataclass(frozen=True, kw_only=True)
class DigitalOption(Instrument):
    """Cash-or-nothing: pays `payout` per unit of notional at expiry if the underlying ends beyond the strike."""
    strike: float
    expiry: dt.date
    right: Literal["C", "P"]
    payout: float = 1.0


@instrument_type
@dataclass(frozen=True, kw_only=True)
class BarrierOption(Instrument):
    """Single barrier; kind DO, UO, DI, UI; rebate paid at the hit (knock-outs) or at expiry (knock-ins)."""
    strike: float
    expiry: dt.date
    right: Literal["C", "P"]
    barrier: float
    kind: Literal["DO", "UO", "DI", "UI"]
    rebate: float = 0.0
    monitoring: Literal["continuous", "daily"] = "continuous"


@instrument_type
@dataclass(frozen=True, kw_only=True)
class AsianOption(Instrument):
    """Arithmetic average of the fixings on `fixing_dates` (past ones read from MarketData.fixings) against a strike."""
    strike: float
    expiry: dt.date
    right: Literal["C", "P"]
    fixing_dates: tuple[dt.date, ...]


@instrument_type
@dataclass(frozen=True, kw_only=True)
class ForwardStart(Instrument):
    """An option whose strike is set at `start` to `moneyness` times the spot then."""
    start: dt.date
    expiry: dt.date
    right: Literal["C", "P"]
    moneyness: float = 1.0


@instrument_type
@dataclass(frozen=True, kw_only=True)
class Cliquet(Instrument):
    """Pays notional x clip(sum of clip(period returns, local_floor, local_cap), global_floor, global_cap) at the last
    reset date; the first reset date is the start."""
    reset_dates: tuple[dt.date, ...]
    local_floor: float = -1.0
    local_cap: float = 1.0
    global_floor: float = 0.0
    global_cap: float = 10.0


@instrument_type
@dataclass(frozen=True, kw_only=True)
class VarianceSwap(Instrument):
    """Long realised variance: pays vega_notional / (2 K) x (realised variance - K^2) at expiry (volatility units)."""
    strike_vol: float
    expiry: dt.date
    vega_notional: float
    obs_dates: tuple[dt.date, ...] = ()


@instrument_type
@dataclass(frozen=True, kw_only=True)
class BasketOption(Instrument):
    """Option on sum w_i S_i(T) / initial_i against a strike in the same units; `underlying` is the first name."""
    underlyings: tuple[str, ...]
    weights: tuple[float, ...]
    initial: tuple[float, ...]
    strike: float
    expiry: dt.date
    right: Literal["C", "P"]


@instrument_type
@dataclass(frozen=True, kw_only=True)
class WorstOf(Instrument):
    """Option on the worst performance min_i S_i(T) / initial_i against a strike (a fraction)."""
    underlyings: tuple[str, ...]
    initial: tuple[float, ...]
    strike: float
    expiry: dt.date
    right: Literal["C", "P"]


@instrument_type
@dataclass(frozen=True, kw_only=True)
class Autocallable(Instrument):
    """Phoenix autocallable on the worst of `underlyings` (chapter 18's term sheet), value per notional (100 = par)."""
    underlyings: tuple[str, ...]
    initial: tuple[float, ...]
    obs_dates: tuple[dt.date, ...]
    trigger: float = 1.0
    coupon: float = 0.0              # per observation, per 100
    coupon_barrier: float = 0.7
    memory: bool = True
    protection: float = 0.6


@instrument_type
@dataclass(frozen=True, kw_only=True)
class TARF(Instrument):
    """Target redemption forward (holder's side, chapter 20): at each fixing the holder gains strike - S per unit when
    the spot is below the strike and loses leverage x (S - strike) above it, until the accumulated gain reaches
    `target` (that fixing's gain capped)."""
    strike: float
    target: float
    leverage: float
    fixing_dates: tuple[dt.date, ...]


@instrument_type
@dataclass(frozen=True, kw_only=True)
class ConvertibleBond(Instrument):
    """Chapter 21's convertible: face, coupon paid `freq` times a year, `ratio` shares per bond, recovery of face at
    default, soft call from `call_start` at `call_price` above `call_trigger`; notional = number of bonds."""
    maturity: dt.date
    face: float = 100.0
    coupon: float = 0.02
    freq: int = 1
    ratio: float = 2.5
    recovery: float = 0.4
    call_start: dt.date | None = None
    call_price: float = 100.0
    call_trigger: float = 1e9


# ------------------------------------------------------------------------------------ models
@dataclass(frozen=True)
class HestonModel:
    """Chapter 10's Heston model: the pricer takes the forward and discount factor from the snapshot."""
    v0: float
    kappa: float
    vbar: float
    eta: float
    rho: float
    name: str = "Heston"

    def params(self) -> Mapping[str, float]:
        return {"v0": self.v0, "kappa": self.kappa, "vbar": self.vbar, "eta": self.eta, "rho": self.rho}

    def calibrate(self, md: MarketData, underlying: str) -> "HestonModel":
        return self

    def cf_model(self) -> _HestonCF:
        return _HestonCF(self.v0, self.kappa, self.vbar, self.eta, self.rho)


@dataclass(frozen=True)
class CreditBlackScholes(BlackScholes):
    """Black-Scholes plus a hazard rate lambda(S) = hazard (S / S0)^(-power), capped at 2 (chapter 21)."""
    hazard: float = 0.02
    power: float = 1.0
    name: str = "CreditBlackScholes"

    def params(self) -> Mapping[str, float]:
        return {**super().params(), "hazard": self.hazard, "power": self.power}

    def calibrate(self, md: MarketData, underlying: str) -> "CreditBlackScholes":
        return self


# ------------------------------------------------------------------------------------ engine helpers
def _rate(md: MarketData, curve: str, d: dt.date) -> float:
    t = md.t(d)
    return -math.log(md.df(curve, d)) / t if t > 0 else 0.0


def _carry(md: MarketData, underlying: str, d: dt.date) -> tuple[float, float]:
    """(r, q): the funding rate and the carry yield implied by the forward (cash dividends become a yield)."""
    t = md.t(d)
    r = _rate(md, md.funding_curve(underlying), d)
    q = r - math.log(md.forward(underlying, d) / md.spots[underlying]) / t if t > 0 else 0.0
    return r, q


def _fixing(md: MarketData, underlying: str, d: dt.date) -> float:
    try:
        return md.fixings[underlying][d]
    except KeyError as exc:
        raise PricingError(f"missing fixing {underlying} {d.isoformat()}") from exc


# ------------------------------------------------------------------------------------ closed-form engine
@dataclass(frozen=True)
class ClosedFormEngine:
    """Closed forms under Black-Scholes on the snapshot: smile-consistent digitals (minus the strike derivative of the
    call), continuous barriers (and daily ones by the Broadie-Glasserman-Kou shift), forward-starts, and variance
    swaps by replication of the log contract on the surface."""
    name: str = "ClosedForm"

    def supports(self, inst: Instrument, model: Model) -> bool:
        return isinstance(inst, DigitalOption | BarrierOption | ForwardStart | VarianceSwap) and isinstance(
            model, BlackScholes)

    def price(self, inst: Instrument, model: BlackScholes, md: MarketData) -> float:
        if isinstance(inst, DigitalOption):
            return self._digital(inst, model, md)
        if isinstance(inst, BarrierOption):
            return self._barrier(inst, model, md)
        if isinstance(inst, ForwardStart):
            return self._forward_start(inst, model, md)
        return self._variance_swap(inst, model, md)

    @staticmethod
    def _digital(o: DigitalOption, model: BlackScholes, md: MarketData) -> float:
        t = md.t(o.expiry)
        if t <= 0:
            s = md.spots[o.underlying]
            return o.notional * o.payout * float((s > o.strike) if o.right == "C" else (s < o.strike)) * (t == 0)
        fwd, df = md.forward(o.underlying, o.expiry), md.df(o.curve(md), o.expiry)
        h = 1e-4 * o.strike

        def call(k: float) -> float:
            return black(fwd, k, t, df, model.sigma(md, o.underlying, k, o.expiry), "C")
        dig_call = -(call(o.strike + h) - call(o.strike - h)) / (2 * h)
        return o.notional * o.payout * (dig_call if o.right == "C" else df - dig_call)

    @staticmethod
    def _barrier(o: BarrierOption, model: BlackScholes, md: MarketData) -> float:
        t = md.t(o.expiry)
        s = md.spots[o.underlying]
        if t <= 0:
            return 0.0
        r, q = _carry(md, o.underlying, o.expiry)
        vol = model.sigma(md, o.underlying, o.strike, o.expiry)
        h = o.barrier if o.monitoring == "continuous" else _bgk_shift(o.barrier, s, vol, 1.0 / 252.0)
        kind = {"DO": "down-out", "UO": "up-out", "DI": "down-in", "UI": "up-in"}[o.kind]
        v = _barrier(s, o.strike, h, t, r, q, vol, kind, o.right, o.rebate)
        return o.notional * v * md.df(o.curve(md), o.expiry) / md.df(md.funding_curve(o.underlying), o.expiry)

    @staticmethod
    def _forward_start(o: ForwardStart, model: BlackScholes, md: MarketData) -> float:
        t, t1 = md.t(o.expiry), md.t(o.start)
        df = md.df(o.curve(md), o.expiry)
        f_t = md.forward(o.underlying, o.expiry)
        if t1 <= 0:                                            # the strike is set: a vanilla
            k = o.moneyness * _fixing(md, o.underlying, o.start) if t1 < 0 else o.moneyness * md.spots[o.underlying]
            return o.notional * black(f_t, k, t, df, model.sigma(md, o.underlying, k, o.expiry), o.right)
        f_1 = md.forward(o.underlying, o.start)
        vol = model.sigma(md, o.underlying, o.moneyness * md.spots[o.underlying], o.expiry)
        return o.notional * f_1 * black(f_t / f_1, o.moneyness, t - t1, df, vol, o.right)

    @staticmethod
    def _variance_swap(o: VarianceSwap, model: BlackScholes, md: MarketData) -> float:
        t = md.t(o.expiry)
        df = md.df(o.curve(md), o.expiry)
        k_var = o.strike_vol ** 2
        fwd = md.forward(o.underlying, o.expiry)
        if model.vol is not None:
            fair = model.vol ** 2
        else:
            ks = fwd * np.exp(np.linspace(-6, 6, 481) * 0.2 * math.sqrt(t))
            calls = np.array([black(fwd, k, t, 1.0, model.sigma(md, o.underlying, k, o.expiry), "C") for k in ks])
            fair = _index_variance(ks, calls, calls - (fwd - ks), fwd, t)
        past = [d for d in o.obs_dates if d <= md.asof]
        if len(past) > 1:
            x = np.log([_fixing(md, o.underlying, d) for d in past])
            n_all = len(o.obs_dates) - 1
            realised_sum = float(np.sum(np.diff(x) ** 2)) * 252.0
            expected = (realised_sum + (n_all - (len(past) - 1)) * fair) / n_all
        else:
            expected = fair
        return o.vega_notional / (2 * o.strike_vol) * (expected - k_var) * df


# ------------------------------------------------------------------------------------ Monte Carlo engine
@dataclass(frozen=True)
class MonteCarloEngine:
    """Lognormal paths on the dates an instrument needs (daily for daily barriers), exact between dates, drifted to the
    forwards, correlated by the snapshot. Each asset's variance between two dates is the increase of its total implied
    variance at the instrument's reference strike (the strike; for an autocallable, the midpoint of protection and
    trigger), so every expiry of the surface up to the last date matters. Seeds follow the binding rule
    (seed_for(inst) + seed_offset); with crn=False the seed also depends on the snapshot, so that bumps no longer share
    random numbers (for demonstration only)."""
    n_paths: int = 100_000
    seed_offset: int = 0
    crn: bool = True
    name: str = "MonteCarlo"

    def supports(self, inst: Instrument, model: Model) -> bool:
        return type(model) is BlackScholes and isinstance(
            inst, EuropeanOption | DigitalOption | BarrierOption | AsianOption | Cliquet | BasketOption | WorstOf
            | Autocallable | TARF) and not (isinstance(inst, EuropeanOption) and inst.exercise != "european")

    def _seed(self, inst: Instrument, md: MarketData) -> int:
        seed = seed_for(inst) + self.seed_offset
        if not self.crn:
            import json  # noqa: PLC0415
            state = json.dumps({"s": md.spots, "v": [repr(v) for v in md.vols.values()],
                                "c": [repr(c) for c in md.curves.values()]}, sort_keys=True, default=str)
            seed = zlib.crc32((str(seed) + state).encode())
        return seed

    def paths(self, inst: Instrument, md: MarketData, names: Sequence[str], dates: Sequence[dt.date],
              ref_strikes: Sequence[float], model: BlackScholes) -> np.ndarray:
        """Spots of `names` at future `dates`: array (n_paths, len(dates), len(names))."""
        ts = np.array([md.t(d) for d in dates])
        total = np.array([[model.sigma(md, u, k, d) ** 2 * t for u, k in zip(names, ref_strikes, strict=True)]
                          for d, t in zip(dates, ts, strict=True)])
        seg = np.maximum(np.diff(np.vstack([np.zeros(len(names)), total]), axis=0), 0.0)     # (dates, names)
        fwds = np.array([[md.forward(u, d) for u in names] for d in dates])
        m = len(names)
        corr = np.eye(m)
        for i in range(m):
            for j in range(i + 1, m):
                corr[i, j] = corr[j, i] = md.correlations.get(frozenset((names[i], names[j])), 0.0)
        low = np.linalg.cholesky(corr)
        rng = np.random.default_rng(self._seed(inst, md))
        half = self.n_paths // 2
        z = rng.standard_normal((half, len(ts), m)) @ low.T
        z = np.concatenate([z, -z])
        x = np.cumsum(z * np.sqrt(seg)[None, :, :] - 0.5 * seg[None, :, :], axis=1)
        return fwds[None, :, :] * np.exp(x)

    def price(self, inst: Instrument, model: BlackScholes, md: MarketData) -> float:
        df_end = md.df(inst.curve(md), getattr(inst, "expiry", None) or self._last_date(inst))
        if isinstance(inst, EuropeanOption | DigitalOption):
            s = self.paths(inst, md, [inst.underlying], [inst.expiry], [inst.strike], model)[:, -1, 0]
            itm = s > inst.strike if inst.right == "C" else s < inst.strike
            pay = (np.maximum(s - inst.strike, 0.0) if inst.right == "C" else np.maximum(inst.strike - s, 0.0)) \
                if isinstance(inst, EuropeanOption) else inst.payout * itm
            return inst.notional * df_end * float(pay.mean())
        if isinstance(inst, BarrierOption):
            return self._barrier(inst, model, md, df_end)
        if isinstance(inst, AsianOption):
            future = [d for d in inst.fixing_dates if d > md.asof]
            past = [_fixing(md, inst.underlying, d) for d in inst.fixing_dates if d <= md.asof]
            s = self.paths(inst, md, [inst.underlying], future, [inst.strike], model)[:, :, 0]
            avg = (sum(past) + s.sum(axis=1)) / len(inst.fixing_dates)
            pay = np.maximum(avg - inst.strike, 0.0) if inst.right == "C" else np.maximum(inst.strike - avg, 0.0)
            return inst.notional * df_end * float(pay.mean())
        if isinstance(inst, Cliquet):
            return self._cliquet(inst, model, md)
        if isinstance(inst, BasketOption | WorstOf):
            s0 = md.spots
            refs = [inst.strike * s0[u] for u in inst.underlyings]
            s = self.paths(inst, md, inst.underlyings, [inst.expiry], refs, model)[:, -1, :] / np.array(inst.initial)
            level = s @ np.array(inst.weights) if isinstance(inst, BasketOption) else s.min(axis=1)
            pay = np.maximum(level - inst.strike, 0.0) if inst.right == "C" else np.maximum(inst.strike - level, 0.0)
            return inst.notional * df_end * float(pay.mean())
        if isinstance(inst, Autocallable):
            return self._autocall(inst, model, md)
        return self._tarf(inst, model, md)

    @staticmethod
    def _last_date(inst: Instrument) -> dt.date:
        for name in ("reset_dates", "obs_dates", "fixing_dates"):
            if hasattr(inst, name):
                return getattr(inst, name)[-1]
        raise PricingError(f"{inst.id}: no last date")

    def _barrier(self, o: BarrierOption, model: BlackScholes, md: MarketData, df_end: float) -> float:
        if o.monitoring != "daily":
            raise PricingError("the Monte Carlo engine prices daily-monitored barriers only")
        n_days = max(1, round(md.t(o.expiry) * 252))
        dates = [md.asof + dt.timedelta(days=round(365.0 * (i + 1) / 252.0)) for i in range(n_days - 1)] + [o.expiry]
        s = self.paths(o, md, [o.underlying], dates, [o.strike], model)[:, :, 0]
        hit = (s.min(axis=1) <= o.barrier) if o.kind[0] == "D" else (s.max(axis=1) >= o.barrier)
        vanilla = np.maximum(s[:, -1] - o.strike, 0.0) if o.right == "C" else np.maximum(o.strike - s[:, -1], 0.0)
        alive = ~hit if o.kind[1] == "O" else hit
        pay = np.where(alive, vanilla, o.rebate)          # rebates paid at expiry here
        return o.notional * df_end * float(pay.mean())

    def _cliquet(self, o: Cliquet, model: BlackScholes, md: MarketData) -> float:
        if o.reset_dates[0] <= md.asof:
            raise PricingError("started cliquets are not supported")
        s = self.paths(o, md, [o.underlying], list(o.reset_dates), [md.spots[o.underlying]], model)[:, :, 0]
        ret = np.clip(s[:, 1:] / s[:, :-1] - 1.0, o.local_floor, o.local_cap).sum(axis=1)
        pay = np.clip(ret, o.global_floor, o.global_cap)
        return o.notional * md.df(o.curve(md), o.reset_dates[-1]) * float(pay.mean())

    def _autocall(self, o: Autocallable, model: BlackScholes, md: MarketData) -> float:
        future = [d for d in o.obs_dates if d > md.asof]
        if len(future) != len(o.obs_dates):
            raise PricingError("seasoned autocallables are not supported")
        refs = [0.5 * (o.protection + o.trigger) * md.spots[u] for u in o.underlyings]
        s = self.paths(o, md, o.underlyings, future, refs, model) / np.array(o.initial)[None, None, :]
        times = np.array([md.t(d) for d in future])
        ts = _TermSheet(obs_times=tuple(times), trigger=o.trigger, coupon=o.coupon, coupon_barrier=o.coupon_barrier,
                        memory=o.memory, protection=o.protection)
        r = _rate(md, o.curve(md), future[-1])
        return o.notional / 100.0 * float(_autocall_cashflows(ts, times, s, r)["pv"].mean())

    def _tarf(self, o: TARF, model: BlackScholes, md: MarketData) -> float:
        future = [d for d in o.fixing_dates if d > md.asof]
        s = self.paths(o, md, [o.underlying], future, [o.strike], model)[:, :, 0]
        dfs = np.array([md.df(o.curve(md), d) for d in future])
        alive = np.ones(len(s), bool)
        gained = np.zeros(len(s))
        pv = np.zeros(len(s))
        for j in range(len(future)):
            gain = np.minimum(np.maximum(o.strike - s[:, j], 0.0), np.maximum(o.target - gained, 0.0))
            loss = o.leverage * np.maximum(s[:, j] - o.strike, 0.0)
            pv += np.where(alive, dfs[j] * (gain - loss), 0.0)
            gained += np.where(alive, gain, 0.0)
            alive &= gained < o.target - 1e-12
        return o.notional * float(pv.mean())


# ------------------------------------------------------------------------------------ finite-difference engine
def _thomas_solve(a, b, c, d):
    n = len(d)
    cp, dp = [0.0] * n, [0.0] * n
    cp[0], dp[0] = c[0] / b[0], d[0] / b[0]
    for i in range(1, n):
        m = b[i] - a[i] * cp[i - 1]
        cp[i] = c[i] / m
        dp[i] = (d[i] - a[i] * dp[i - 1]) / m
    out = [0.0] * n
    out[-1] = dp[-1]
    for i in range(n - 2, -1, -1):
        out[i] = dp[i] - cp[i] * out[i + 1]
    return out


def _projected_solve(a, b, c, d, g, put: bool):
    """Brennan-Schwartz with V >= g: exercise region at low spots for a put (eliminate downwards from the top), at
    high spots for a call (the mirror image)."""
    if not put:
        return _projected_solve(c[::-1], b[::-1], a[::-1], d[::-1], g[::-1], True)[::-1]
    n = len(d)
    bp, dp = [0.0] * n, [0.0] * n
    bp[-1], dp[-1] = b[-1], d[-1]
    for i in range(n - 2, -1, -1):
        f = c[i] / bp[i + 1]
        bp[i] = b[i] - f * a[i + 1]
        dp[i] = d[i] - f * dp[i + 1]
    out = [0.0] * n
    out[0] = max(dp[0] / bp[0], g[0])
    for i in range(1, n):
        out[i] = max((dp[i] - a[i] * out[i - 1]) / bp[i], g[i])
    return out


def fd_vanilla(s0: float, k: float, t: float, r: float, q: float, vol: float, right: str, american: bool,
               m: int = 200, n_t: int = 200, rannacher: int = 2, width: float = 5.0) -> float:
    """Crank-Nicolson in log-spot on a uniform grid of m + 1 nodes, `width` standard deviations either side, with
    `rannacher` pairs of implicit half steps at the start; Thomas (European) or Brennan-Schwartz (American); Dirichlet
    ends at the discounted forward intrinsic value (or the intrinsic value if larger, when American); the value at s0
    by quadratic interpolation. The C++20 and Rust twins run the same arithmetic."""
    half = width * vol * math.sqrt(t)
    x = [math.log(s0) - half + 2.0 * half * i / m for i in range(m + 1)]
    s = [math.exp(xi) for xi in x]
    sign = 1.0 if right == "C" else -1.0
    g = [max(sign * (si - k), 0.0) for si in s]
    v = list(g)
    nu, d2 = r - q - 0.5 * vol * vol, vol * vol
    lo, di, up = [], [], []
    for i in range(1, m):
        hm, hp = x[i] - x[i - 1], x[i + 1] - x[i]
        lo.append(d2 / (hm * (hm + hp)) - nu * hp / (hm * (hm + hp)))
        di.append(-d2 / (hm * hp) + nu * (hp - hm) / (hm * hp) - r)
        up.append(d2 / (hp * (hm + hp)) + nu * hm / (hp * (hm + hp)))
    dt_ = t / n_t
    tau, step, implicit_half = 0.0, 0, 2 * rannacher
    ni = m - 1
    while step < n_t:
        if implicit_half > 0:
            h, theta = 0.5 * dt_, 1.0
            implicit_half -= 1
        else:
            h, theta = dt_, 0.5
        tau += h
        rhs = [v[i + 1] + (1 - theta) * h * (lo[i] * v[i] + di[i] * v[i + 1] + up[i] * v[i + 2]) for i in range(ni)]
        a = [-theta * h * lo[i] for i in range(ni)]
        b = [1 - theta * h * di[i] for i in range(ni)]
        c = [-theta * h * up[i] for i in range(ni)]
        ends = [max(sign * (sj * math.exp(-q * tau) - k * math.exp(-r * tau)), 0.0) for sj in (s[0], s[-1])]
        if american:
            ends = [max(e, gj) for e, gj in zip(ends, (g[0], g[-1]), strict=True)]
        rhs[0] -= a[0] * ends[0]
        rhs[-1] -= c[-1] * ends[1]
        a[0], c[-1] = 0.0, 0.0
        inner = _projected_solve(a, b, c, rhs, g[1:-1], right == "P") if american else _thomas_solve(a, b, c, rhs)
        v = [ends[0], *inner, ends[1]]
        if abs(tau - (step + 1) * dt_) < 1e-12 * max(1.0, t):
            step += 1
    x0 = math.log(s0)
    i = min(max(next((j for j, xj in enumerate(x) if xj >= x0), m), 1), m - 1)
    x1, x2, x3 = x[i - 1], x[i], x[i + 1]
    return (v[i - 1] * (x0 - x2) * (x0 - x3) / ((x1 - x2) * (x1 - x3))
            + v[i] * (x0 - x1) * (x0 - x3) / ((x2 - x1) * (x2 - x3))
            + v[i + 1] * (x0 - x1) * (x0 - x2) / ((x3 - x1) * (x3 - x2)))


@dataclass(frozen=True)
class PDEEngine:
    """European and American options under Black-Scholes by fd_vanilla, the funding rate and the forward's carry
    yield (cash dividends as a yield), discounted on the instrument's curve."""
    m: int = 200
    n_t: int = 200
    name: str = "PDE"

    def supports(self, inst: Instrument, model: Model) -> bool:
        return (isinstance(inst, EuropeanOption) and inst.exercise in ("european", "american")
                and isinstance(model, BlackScholes))

    def price(self, inst: EuropeanOption, model: BlackScholes, md: MarketData) -> float:
        t = md.t(inst.expiry)
        s = md.spots[inst.underlying]
        if t <= 0:
            return inst.notional * max((s - inst.strike) if inst.right == "C" else (inst.strike - s), 0.0) * (t == 0)
        r, q = _carry(md, inst.underlying, inst.expiry)
        vol = model.sigma(md, inst.underlying, inst.strike, inst.expiry)
        v = fd_vanilla(s, inst.strike, t, r, q, vol, inst.right, inst.exercise == "american", self.m, self.n_t)
        return inst.notional * v * md.df(inst.curve(md), inst.expiry) / md.df(md.funding_curve(inst.underlying),
                                                                               inst.expiry)


# ------------------------------------------------------------------------------------ Fourier and convertible engines
@dataclass(frozen=True)
class FourierEngine:
    """European options and digitals under Heston by the COS method (chapter 24) on the snapshot's forward."""
    n: int = 256
    name: str = "Fourier"

    def supports(self, inst: Instrument, model: Model) -> bool:
        return isinstance(model, HestonModel) and (isinstance(inst, DigitalOption) or (
            isinstance(inst, EuropeanOption) and inst.exercise == "european"))

    def price(self, inst: Instrument, model: HestonModel, md: MarketData) -> float:
        t = md.t(inst.expiry)
        fwd, df = md.forward(inst.underlying, inst.expiry), md.df(inst.curve(md), inst.expiry)
        cf = model.cf_model()
        if isinstance(inst, EuropeanOption):
            c = float(_cos_calls(cf, fwd, [inst.strike], t, n=self.n, df=df)[0])
            return inst.notional * (c if inst.right == "C" else c - df * (fwd - inst.strike))
        h = 1e-4 * inst.strike
        up, dn = _cos_calls(cf, fwd, [inst.strike + h, inst.strike - h], t, n=self.n, df=df)
        dig_call = -(up - dn) / (2 * h)
        return inst.notional * inst.payout * (dig_call if inst.right == "C" else df - dig_call)


@dataclass(frozen=True)
class ConvertibleEngine:
    """Chapter 21's Crank-Nicolson grid with the hazard lambda(S) of a CreditBlackScholes model; the volatility is the
    surface's at the conversion price; value per bond x notional (number of bonds)."""
    nx: int = 500
    steps_per_year: int = 200
    name: str = "ConvertiblePDE"

    def supports(self, inst: Instrument, model: Model) -> bool:
        return isinstance(inst, ConvertibleBond) and isinstance(model, CreditBlackScholes)

    def price(self, inst: ConvertibleBond, model: CreditBlackScholes, md: MarketData) -> float:
        t = md.t(inst.maturity)
        s = md.spots[inst.underlying]
        r, q = _carry(md, inst.underlying, inst.maturity)
        vol = model.sigma(md, inst.underlying, inst.face / inst.ratio, inst.maturity)
        start = md.t(inst.call_start) if inst.call_start is not None else t + 1.0
        cb = _Convertible(face=inst.face, maturity=t, coupon=inst.coupon, freq=inst.freq, ratio=inst.ratio,
                          recovery=inst.recovery, call_start=start, call_price=inst.call_price,
                          call_trigger=inst.call_trigger)
        grid = _cb_grid(cb, r, q, vol, _power_hazard(model.hazard, s, model.power), nx=self.nx,
                        steps_per_year=self.steps_per_year)
        return inst.notional * _cb_value_at(s, grid) * md.df(inst.curve(md), inst.maturity) / md.df(
            md.funding_curve(inst.underlying), inst.maturity)


register(EuropeanOption, BlackScholes, PDEEngine())
register(EuropeanOption, BlackScholes, MonteCarloEngine())
register(EuropeanOption, HestonModel, FourierEngine())
register(DigitalOption, BlackScholes, ClosedFormEngine())
register(DigitalOption, BlackScholes, MonteCarloEngine())
register(DigitalOption, HestonModel, FourierEngine())
register(BarrierOption, BlackScholes, ClosedFormEngine())
register(BarrierOption, BlackScholes, MonteCarloEngine())
register(ForwardStart, BlackScholes, ClosedFormEngine())
register(VarianceSwap, BlackScholes, ClosedFormEngine())
for _t in (AsianOption, Cliquet, BasketOption, WorstOf, Autocallable, TARF):
    register(_t, BlackScholes, MonteCarloEngine())
register(ConvertibleBond, CreditBlackScholes, ConvertibleEngine())


def engines_for(inst: Instrument, model: Model) -> list:
    """Every registered engine that supports the pair, default first (for cross-engine checks)."""
    out = []
    for it in type(inst).__mro__:
        for mt in type(model).__mro__:
            out += [e for e in _REGISTRY.get((it, mt), []) if e.supports(inst, model) and e not in out]
    return out
