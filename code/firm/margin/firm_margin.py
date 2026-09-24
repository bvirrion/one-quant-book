"""Scenario margin engine (build of Book 1, Chapter 20), in the style of SPAN.

Sixteen scenarios per product: volatility up/down at price moves of 0, +-1/3, +-2/3, +-3/3 of the
price scan range, and two extreme moves of which only a fraction of the loss is counted. Then an
inter-month spread charge, a short option minimum, and an inter-commodity credit. All parameters
belong to the clearing house; the ones in the tests are made up.
"""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Params:
    price_scan: float               # price scan range, in price points
    vol_scan: float                 # volatility scan range, absolute (0.04 = four vol points)
    extreme_mult: float = 3.0
    extreme_cover: float = 0.30
    intermonth_charge: float = 0.0  # currency per spread (one long, one short, different expiries)
    short_option_min: float = 0.0   # currency per short option
    multiplier: float = 1.0


@dataclass(frozen=True)
class Position:
    root: str
    expiry: str
    qty: int
    strike: float | None = None     # None for a future
    right: str = ""                 # 'C' or 'P' for options


@dataclass(frozen=True)
class Market:
    future: dict[tuple[str, str], float]          # (root, expiry) -> futures price
    vol: dict[tuple[str, str], float]             # implied volatility used for that expiry's options
    years: dict[tuple[str, str], float]           # time to expiry


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black76(f: float, k: float, vol: float, t: float, right: str) -> float:
    """Undiscounted Black (1976) value of a European option on a future."""
    if t <= 0 or vol <= 0:
        return max(f - k, 0.0) if right == "C" else max(k - f, 0.0)
    d1 = (math.log(f / k) + 0.5 * vol * vol * t) / (vol * math.sqrt(t))
    d2 = d1 - vol * math.sqrt(t)
    call = f * _phi(d1) - k * _phi(d2)
    return call if right == "C" else call - f + k


STANDARD = tuple((m / 3.0, v) for m in (0, 1, -1, 2, -2, 3, -3) for v in (1, -1))     # scenarios 1 to 14


def scenarios(p: Params) -> list[tuple[float, float, float]]:
    """(price move, vol move, fraction of the loss counted) for the 16 scenarios."""
    std = [(m * p.price_scan, v * p.vol_scan, 1.0) for m, v in STANDARD]
    ext = p.extreme_mult * p.price_scan
    return std + [(ext, 0.0, p.extreme_cover), (-ext, 0.0, p.extreme_cover)]


def value(pos: Position, mkt: Market, d_price: float = 0.0, d_vol: float = 0.0) -> float:
    key = (pos.root, pos.expiry)
    f = mkt.future[key] + d_price
    if pos.strike is None:
        return f
    return black76(f, pos.strike, max(mkt.vol[key] + d_vol, 1e-4), mkt.years[key], pos.right)


def risk_array(pos: Position, mkt: Market, p: Params) -> list[float]:
    """Loss (positive = loss) of ONE LONG unit under each scenario, in currency."""
    base = value(pos, mkt)
    return [-(value(pos, mkt, dp, dv) - base) * cover * p.multiplier for dp, dv, cover in scenarios(p)]


@dataclass(frozen=True)
class MarginResult:
    scan_risk: float
    worst_scenario: int             # 1-based
    intermonth: float
    short_option_min: float
    total: float


def product_margin(positions: list[Position], mkt: Market, p: Params) -> MarginResult:
    losses = [0.0] * 16
    for pos in positions:
        arr = risk_array(pos, mkt, p)
        for i in range(16):
            losses[i] += pos.qty * arr[i]
    worst = max(range(16), key=lambda i: losses[i])
    scan = max(losses[worst], 0.0)
    net_by_expiry: dict[str, float] = {}
    for pos in positions:                                        # spreads are counted on futures only, for simplicity
        if pos.strike is None:
            net_by_expiry[pos.expiry] = net_by_expiry.get(pos.expiry, 0) + pos.qty
    longs = sum(q for q in net_by_expiry.values() if q > 0)
    shorts = -sum(q for q in net_by_expiry.values() if q < 0)
    inter = min(longs, shorts) * p.intermonth_charge
    som = sum(-pos.qty for pos in positions if pos.strike is not None and pos.qty < 0) * p.short_option_min
    return MarginResult(scan, worst + 1, inter, som, max(scan + inter, som))


def portfolio_margin(by_root: dict[str, list[Position]], mkt: Market, params: dict[str, Params],
                     credits: dict[tuple[str, str], float] | None = None) -> tuple[float, dict[str, MarginResult]]:
    """Sum of product margins less inter-commodity credits: for a pair (a, b) with credit c, when the
    two products' worst scenarios are price moves in opposite directions for the portfolio (one loses
    when prices rise, the other when they fall), c times the smaller scan risk is given back on both."""
    res = {r: product_margin(ps, mkt, params[r]) for r, ps in by_root.items()}
    total = sum(m.total for m in res.values())
    for (a, b), c in (credits or {}).items():
        if a in res and b in res:
            up_a = scenarios(params[a])[res[a].worst_scenario - 1][0] > 0
            up_b = scenarios(params[b])[res[b].worst_scenario - 1][0] > 0
            if up_a != up_b:
                total -= 2 * c * min(res[a].scan_risk, res[b].scan_risk)
    return total, res
